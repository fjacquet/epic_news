"""
Tracing utilities for Epic News flows and tools.

- Initializes an optional Langfuse client from environment variables if available.
- Provides a `trace_span` context manager and `@traced` decorator to annotate
  kickoff calls, agent runs, and tool invocations.

Environment variables (optional):
- LANGFUSE_PUBLIC_KEY
- LANGFUSE_SECRET_KEY
- LANGFUSE_HOST (default: https://cloud.langfuse.com)
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager, suppress
from typing import Any, Callable, Optional, TypeVar, cast

T = TypeVar("T")

# Soft dependency on langfuse
_langfuse = None
_langfuse_span_cls = None

try:  # Attempt to initialize Langfuse if configured
    from langfuse import Langfuse  # type: ignore

    LF_PUBLIC = os.getenv("LANGFUSE_PUBLIC_KEY")
    LF_SECRET = os.getenv("LANGFUSE_SECRET_KEY")
    LF_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if LF_PUBLIC and LF_SECRET:
        _langfuse = Langfuse(public_key=LF_PUBLIC, secret_key=LF_SECRET, host=LF_HOST)
except Exception:
    _langfuse = None  # Not available or not configured


@contextmanager
def trace_span(name: str, attrs: Optional[dict[str, Any]] = None):
    """
    Context manager to trace spans via Langfuse when available; otherwise no-op.
    """
    start = time.perf_counter()
    span = None
    try:
        if _langfuse:
            span = _langfuse.span(name=name, input=attrs or {})  # type: ignore[attr-defined]
        yield
        if span is not None:
            span.end(output={"status": "ok"})
    except Exception as e:  # Ensure tracing never breaks app logic
        if span is not None:
            with suppress(Exception):
                span.end(output={"status": "error", "error": str(e)})
        raise
    finally:
        if not _langfuse:
            # Fallback could log timing if needed; kept minimal by design
            _ = time.perf_counter() - start


def traced(name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to wrap a function within a trace_span named `name`."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with trace_span(name, {"func": func.__name__}):
                return cast(T, func(*args, **kwargs))

        return wrapper

    return decorator
