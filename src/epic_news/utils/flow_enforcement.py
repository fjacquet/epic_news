"""
Flow enforcement utilities for Epic News crews.

This module provides a small wrapper around CrewAI kickoff calls to:
- Centralize orchestration entrypoints.
- Add lightweight tracing/logging around runs.
- Avoid ad-hoc direct calls to internal crew or renderer methods from outside flows.

Usage:
    from epic_news.utils.flow_enforcement import kickoff_flow
    result = kickoff_flow(SomeCrew(), context={"topic": "AI"})
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from loguru import logger

try:
    # Local, optional tracing (no hard dependency)
    from .tracing import trace_span
except Exception:  # pragma: no cover - fallback if tracing is unavailable
    from contextlib import contextmanager

    @contextmanager
    def trace_span(name: str, attrs: dict[str, Any] | None = None):
        yield


# Substrings identifying provider-side hiccups that are worth retrying. A crew run is
# expensive (deep_research takes ~19 min), so we only retry failures that are known to
# be transient and leave real defects -- validation errors, bad config -- to fail fast.
#
# The first two entries cover an observed OpenRouter/Mistral failure: the provider
# returns an error-shaped completion (content=None, tool_calls=None, 0 tokens). The
# instructor TOOLS-mode parser then iterates the missing tool_calls and raises a
# TypeError, which instructor classifies as non-retryable, so it aborts after 1 attempt.
#
# NOTE: raw request timeouts (litellm.Timeout, "timed out") are deliberately absent.
# A timeout means the crew already burned the full per-call budget (e.g. 600s); replaying
# the whole multi-agent crew 2-3x turns one slow run into ~40 min of waste and rarely
# succeeds, because the cause is structural (oversized context / overloaded provider),
# not a transient blip. Timeouts fail fast so the caller sees the real error immediately.
_TRANSIENT_ERROR_MARKERS: tuple[str, ...] = (
    "no tool calls or function call found",
    "'nonetype' object is not iterable",
    "max retries exceeded",
    "rate limit",
    "service unavailable",
    "internal server error",
    "bad gateway",
    "overloaded",
    "502",
    "503",
    "529",
)


def _is_transient_error(exc: BaseException) -> bool:
    """Return True when the exception looks like a retryable provider-side failure."""
    message = str(exc).lower()
    return any(marker in message for marker in _TRANSIENT_ERROR_MARKERS)


def _retry_settings() -> tuple[int, float]:
    """Read retry attempts and base backoff seconds from the environment."""
    attempts = max(1, int(os.getenv("CREW_KICKOFF_ATTEMPTS", "3")))
    backoff = max(0.0, float(os.getenv("CREW_KICKOFF_BACKOFF_SECONDS", "5")))
    return attempts, backoff


def _get_crew_instance(crew_or_factory: Any) -> Any:
    """Return a CrewAI Crew instance from either a factory (with .crew()) or a Crew itself.

    This allows calling kickoff_flow(SomeCrew()) or kickoff_flow(SomeCrew().crew()).
    """
    # If this looks like a factory with a .crew() method, call it to get a Crew instance
    if hasattr(crew_or_factory, "crew") and callable(crew_or_factory.crew):
        return crew_or_factory.crew()
    return crew_or_factory


def kickoff_flow(crew_or_factory: Any, context: dict[str, Any]) -> Any:
    """Kick off a CrewAI run in a consistent, traceable way.

    - Accepts either a Crew factory (with .crew()) or a Crew instance.
    - Ensures context is a dict.
    - Adds basic timing + optional tracing via trace_span.
    - Retries transient provider failures (see ``_TRANSIENT_ERROR_MARKERS``) so a single
      empty completion cannot discard an entire multi-agent run.
    """
    if not isinstance(context, dict):
        raise ValueError("kickoff_flow context must be a dict")

    crew_name = type(crew_or_factory).__name__
    attempts, backoff = _retry_settings()
    start = time.perf_counter()

    with trace_span("kickoff_flow", {"crew": crew_name, "keys": sorted(context.keys())}):
        logger.info(
            "🚀 Kicking off crew {} with context keys: {}", crew_name, ", ".join(sorted(context.keys()))
        )
        for attempt in range(1, attempts + 1):
            # Rebuild the crew each attempt: a Crew carries per-run task state that is
            # not safe to replay after a mid-run failure.
            crew = _get_crew_instance(crew_or_factory)
            if not hasattr(crew, "kickoff"):
                raise AttributeError(f"Object {crew!r} does not support kickoff()")

            try:
                result = crew.kickoff(inputs=context)
            except Exception as exc:
                elapsed = time.perf_counter() - start
                if attempt < attempts and _is_transient_error(exc):
                    delay = backoff * (2 ** (attempt - 1))
                    logger.warning(
                        "⚠️ Crew {} hit a transient provider error on attempt {}/{} after {:.2f}s; "
                        "retrying in {:.1f}s. Error: {}",
                        crew_name,
                        attempt,
                        attempts,
                        elapsed,
                        delay,
                        exc,
                    )
                    time.sleep(delay)
                    continue
                logger.error(
                    "❌ Crew {} failed after {:.2f}s on attempt {}/{}: {}",
                    crew_name,
                    elapsed,
                    attempt,
                    attempts,
                    exc,
                )
                raise
            else:
                elapsed = time.perf_counter() - start
                logger.info("✅ Crew {} finished in {:.2f}s", crew_name, elapsed)
                return result

        # Unreachable: every iteration either returns or raises.
        raise RuntimeError(  # pragma: no cover
            f"Crew {crew_name} exhausted {attempts} attempts without result"
        )


async def akickoff_flow(crew_or_factory: Any, context: dict[str, Any]) -> Any:
    """Async version of kickoff_flow using CrewAI's native akickoff().

    Uses CrewAI's native async execution for high-concurrency workloads.
    Ideal for running multiple crews in parallel with asyncio.gather().

    - Accepts either a Crew factory (with .crew()) or a Crew instance.
    - Ensures context is a dict.
    - Adds basic timing + optional tracing via trace_span.
    - Retries transient provider failures, mirroring kickoff_flow. This path runs the
      parallel OSINT crews, so a single empty completion must not drop the whole fan-out.
    """
    if not isinstance(context, dict):
        raise ValueError("akickoff_flow context must be a dict")

    crew_name = type(crew_or_factory).__name__
    attempts, backoff = _retry_settings()
    start = time.perf_counter()

    with trace_span("akickoff_flow", {"crew": crew_name, "keys": sorted(context.keys())}):
        logger.info(
            "🚀 Async kicking off crew {} with context keys: {}",
            crew_name,
            ", ".join(sorted(context.keys())),
        )
        for attempt in range(1, attempts + 1):
            # Rebuild the crew each attempt: a Crew carries per-run task state that is
            # not safe to replay after a mid-run failure.
            crew = _get_crew_instance(crew_or_factory)
            if not hasattr(crew, "akickoff"):
                raise AttributeError(f"Object {crew!r} does not support akickoff()")

            try:
                result = await crew.akickoff(inputs=context)
            except Exception as exc:
                elapsed = time.perf_counter() - start
                if attempt < attempts and _is_transient_error(exc):
                    delay = backoff * (2 ** (attempt - 1))
                    logger.warning(
                        "⚠️ Crew {} hit a transient provider error on attempt {}/{} after {:.2f}s; "
                        "retrying in {:.1f}s. Error: {}",
                        crew_name,
                        attempt,
                        attempts,
                        elapsed,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(
                    "❌ Crew {} failed after {:.2f}s on attempt {}/{}: {}",
                    crew_name,
                    elapsed,
                    attempt,
                    attempts,
                    exc,
                )
                raise
            else:
                elapsed = time.perf_counter() - start
                logger.info("✅ Crew {} finished in {:.2f}s", crew_name, elapsed)
                return result

        # Unreachable: every iteration either returns or raises.
        raise RuntimeError(  # pragma: no cover
            f"Crew {crew_name} exhausted {attempts} attempts without result"
        )
