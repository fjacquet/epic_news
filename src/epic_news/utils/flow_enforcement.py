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

import logging
import time
from typing import Any

try:
    # Local, optional tracing (no hard dependency)
    from .tracing import trace_span
except Exception:  # pragma: no cover - fallback if tracing is unavailable
    from contextlib import contextmanager

    @contextmanager
    def trace_span(name: str, attrs: dict[str, Any] | None = None):
        yield


logger = logging.getLogger(__name__)


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
    """
    if not isinstance(context, dict):
        raise ValueError("kickoff_flow context must be a dict")

    crew_name = type(crew_or_factory).__name__
    start = time.perf_counter()

    with trace_span("kickoff_flow", {"crew": crew_name, "keys": sorted(context.keys())}):
        crew = _get_crew_instance(crew_or_factory)
        if not hasattr(crew, "kickoff"):
            raise AttributeError(f"Object {crew!r} does not support kickoff()")

        logger.info(
            "🚀 Kicking off crew {} with context keys: {}", crew_name, ", ".join(sorted(context.keys()))
        )
        try:
            result = crew.kickoff(inputs=context)
            return result
        finally:
            elapsed = time.perf_counter() - start
            logger.info("✅ Crew {} finished in %.2fs", crew_name, elapsed)
