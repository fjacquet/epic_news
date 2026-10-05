"""Trace events for the Epic News flow.

``TraceEvent`` and ``Tracer`` record events to ``traces/<trace_id>.json``;
``trace_task`` records ``task_start`` / ``task_error`` / ``task_end`` around a
flow step (plain or ``async def``).
"""

import hashlib
import inspect
import json
import os
import time
from datetime import datetime
from functools import wraps
from typing import Any

from epic_news.utils.directory_utils import ensure_output_directory

# Constants
TRACE_DIR = "traces"

# Ensure directories exist
ensure_output_directory(TRACE_DIR)


class TraceEvent:
    """
    Represents a trace event in the system.
    """

    def __init__(self, event_type: str, source: str, details: dict[str, Any], timestamp: float | None = None):
        """
        Initialize a trace event.

        Args:
            event_type: Type of event (e.g., "task_start", "task_end", "tool_call")
            source: Source of the event (e.g., crew name, agent name)
            details: Additional details about the event
            timestamp: Event timestamp (defaults to current time)
        """
        self.event_type = event_type
        self.source = source
        self.details = details
        self.timestamp = timestamp or time.time()
        self.event_id = hashlib.sha256(
            f"{self.source}:{self.event_type}:{self.timestamp}".encode()
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the trace event to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the trace event
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "details": self.details,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TraceEvent":
        """
        Create a trace event from a dictionary.

        Args:
            data: Dictionary representation of a trace event

        Returns:
            TraceEvent: The created trace event
        """
        event = cls(
            event_type=data["event_type"],
            source=data["source"],
            details=data["details"],
            timestamp=data["timestamp"],
        )
        event.event_id = data["event_id"]
        return event


class Tracer:
    """
    Traces events in the system for observability.
    """

    def __init__(self, trace_id: str | None = None):
        """
        Initialize a tracer.

        Args:
            trace_id: ID for the trace (defaults to a timestamp-based ID)
        """
        self.trace_id = trace_id or f"trace_{int(time.time())}"
        self.events: list[TraceEvent] = []
        self.trace_file = os.path.join(TRACE_DIR, f"{self.trace_id}.json")

    def add_event(self, event: TraceEvent) -> None:
        """
        Add an event to the trace.

        Args:
            event: The trace event to add
        """
        self.events.append(event)
        self._save_event(event)

    def _save_event(self, event: TraceEvent) -> None:
        """
        Save an event to the trace file.

        Args:
            event: The trace event to save
        """
        event_dict = event.to_dict()

        # Append to the trace file
        with open(self.trace_file, "a") as f:
            f.write(json.dumps(event_dict) + "\n")

    def get_events(self, event_type: str | None = None, source: str | None = None) -> list[TraceEvent]:
        """
        Get events matching the specified criteria.

        Args:
            event_type: Filter by event type
            source: Filter by source

        Returns:
            List[TraceEvent]: List of matching events
        """
        filtered_events = self.events

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if source:
            filtered_events = [e for e in filtered_events if e.source == source]

        return filtered_events

    @classmethod
    def load_trace(cls, trace_id: str) -> "Tracer":
        """
        Load a trace from a file.

        Args:
            trace_id: ID of the trace to load

        Returns:
            Tracer: The loaded tracer
        """
        tracer = cls(trace_id)
        trace_file = os.path.join(TRACE_DIR, f"{trace_id}.json")

        if os.path.exists(trace_file):
            with open(trace_file) as f:
                for line in f:
                    event_dict = json.loads(line)
                    event = TraceEvent.from_dict(event_dict)
                    tracer.events.append(event)

        return tracer


def trace_task(tracer: Tracer):
    """Record ``task_start`` / ``task_error`` / ``task_end`` events around a flow step.

    Works for plain and ``async def`` steps; an async step is recorded when it
    finishes, not when its coroutine is created.
    """

    def decorator(func):
        task_name = func.__name__

        def _start(args, kwargs) -> float:
            details = {"task_name": task_name, "args": str(args), "kwargs": str(kwargs)}
            tracer.add_event(TraceEvent("task_start", f"task:{task_name}", details))
            return time.time()

        def _end(start: float, result: Any, error: BaseException | None) -> None:
            if error is not None:
                details = {"task_name": task_name, "error": str(error)}
                tracer.add_event(TraceEvent("task_error", f"task:{task_name}", details))
            end_details = {
                "task_name": task_name,
                "duration": time.time() - start,
                "success": error is None,
                "result_type": type(result).__name__ if error is None else None,
            }
            tracer.add_event(TraceEvent("task_end", f"task:{task_name}", end_details))

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = _start(args, kwargs)
                try:
                    result = await func(*args, **kwargs)
                except BaseException as e:  # Ctrl+C too: the step still gets its task_end
                    _end(start, None, e)
                    raise
                _end(start, result, None)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = _start(args, kwargs)
            try:
                result = func(*args, **kwargs)
            except BaseException as e:  # Ctrl+C too: the step still gets its task_end
                _end(start, None, e)
                raise
            _end(start, result, None)
            return result

        return wrapper

    return decorator
