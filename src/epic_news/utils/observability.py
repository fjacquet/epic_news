"""
Observability and Automatic Guardrails for Epic News Crews

This module provides utilities for monitoring, tracing, and implementing
guardrails against hallucinations in AI agent outputs.
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime
from functools import wraps
from typing import Any

from loguru import logger

from epic_news.utils.directory_utils import ensure_output_directory

# Configure logging
# logger = logging.getLogger("observability")

# Constants
TRACE_DIR = "traces"
DASHBOARD_DATA_DIR = os.path.join("output", "dashboard_data")

# Ensure directories exist
ensure_output_directory(TRACE_DIR)
ensure_output_directory(DASHBOARD_DATA_DIR)


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


class HallucinationGuard:
    """
    Guards against hallucinations in AI agent outputs.
    """

    def __init__(self, confidence_threshold: float = 0.7, fact_checking_enabled: bool = True):
        """
        Initialize a hallucination guard.

        Args:
            confidence_threshold: Threshold for confidence scores
            fact_checking_enabled: Whether to enable fact checking
        """
        self.confidence_threshold = confidence_threshold
        self.fact_checking_enabled = fact_checking_enabled
        self.known_facts: dict[str, Any] = {}

    def check_statement(self, statement: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Check a statement for potential hallucinations.

        Args:
            statement: The statement to check
            context: Context information for the check

        Returns:
            Dict[str, Any]: Results of the hallucination check
        """
        # Simple pattern-based checks
        results = {
            "statement": statement,
            "is_likely_hallucination": False,
            "confidence": 1.0,
            "warnings": [],
            "context_used": context,
        }

        # Check for specific hallucination patterns
        patterns = [
            (r"\b(definitely|certainly|absolutely|undoubtedly)\b", "Overly confident language detected", 0.8),
            (r"\b(all|every|always|never)\b", "Absolute statements detected", 0.7),
            (r"\b(famous|well-known|renowned|celebrated)\b", "Potentially exaggerated importance", 0.6),
            (
                r"\b(recent studies show|research indicates|experts agree)\b",
                "Vague appeal to authority without citation",
                0.5,
            ),
        ]

        for pattern, warning, confidence_penalty in patterns:
            if re.search(pattern, statement, re.IGNORECASE):
                results["warnings"].append(warning)  # type: ignore[attr-defined]
                results["confidence"] *= confidence_penalty  # type: ignore[operator]

        # Check if statement contradicts known facts
        for fact_key, fact_value in self.known_facts.items():
            if fact_key in statement and str(fact_value) not in statement:
                results["warnings"].append(f"Contradicts known fact: {fact_key} = {fact_value}")  # type: ignore[attr-defined]
                results["confidence"] *= 0.5  # type: ignore[operator]

        # Final determination
        if results["confidence"] < self.confidence_threshold:  # type: ignore[operator]
            results["is_likely_hallucination"] = True

        return results

    def add_known_fact(self, key: str, value: Any) -> None:
        """
        Add a known fact to the guard.

        Args:
            key: Fact key
            value: Fact value
        """
        self.known_facts[key] = value

    def validate_output(
        self, output: str, context: dict[str, Any], fix_hallucinations: bool = False
    ) -> dict[str, Any]:
        """
        Validate an output for hallucinations.

        Args:
            output: The output to validate
            context: Context information for validation
            fix_hallucinations: Whether to attempt to fix hallucinations

        Returns:
            Dict[str, Any]: Validation results
        """
        # Split output into sentences for checking
        sentences = re.split(r"(?<=[.!?])\s+", output)

        results = {
            "original_output": output,
            "hallucination_score": 0.0,
            "warnings": [],
            "fixed_output": output if fix_hallucinations else None,
        }

        hallucination_count = 0

        for sentence in sentences:
            check_result = self.check_statement(sentence, context)
            if check_result["is_likely_hallucination"]:
                hallucination_count += 1
                results["warnings"].extend(check_result["warnings"])  # type: ignore[attr-defined]

        if sentences:
            results["hallucination_score"] = hallucination_count / len(sentences)

        # Attempt to fix hallucinations if requested
        if fix_hallucinations and results["hallucination_score"] > 0:  # type: ignore[operator]
            # Simple fix: add disclaimers to the output
            disclaimer = "\n\nNote: Some statements in this output may require further verification."
            results["fixed_output"] = output + disclaimer

        return results


class Dashboard:
    """
    Provides dashboard capabilities for monitoring system activity.
    """

    def __init__(self, dashboard_id: str | None = None):
        """
        Initialize a dashboard.

        Args:
            dashboard_id: ID for the dashboard (defaults to a timestamp-based ID)
        """
        self.dashboard_id = dashboard_id or f"dashboard_{int(time.time())}"
        self.data_file = os.path.join(DASHBOARD_DATA_DIR, f"{self.dashboard_id}.json")
        self.metrics: dict[str, Any] = {
            "crews": {},
            "agents": {},
            "tasks": {},
            "tools": {},
            "system": {"start_time": time.time(), "events_count": 0},
        }

    def update_metric(self, category: str, name: str, metric: str, value: Any) -> None:
        """
        Update a metric in the dashboard.

        Args:
            category: Metric category (e.g., "crews", "agents")
            name: Name within the category
            metric: Metric name
            value: Metric value
        """
        if category not in self.metrics:
            self.metrics[category] = {}

        if name not in self.metrics[category]:
            self.metrics[category][name] = {}

        self.metrics[category][name][metric] = value
        self.metrics["system"]["events_count"] += 1

        # Save the updated metrics
        self._save_metrics()

    def _save_metrics(self) -> None:
        """Save the metrics to the data file."""
        with open(self.data_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

    def get_metrics(self, category: str | None = None, name: str | None = None) -> dict[str, Any]:
        """
        Get metrics from the dashboard.

        Args:
            category: Filter by category
            name: Filter by name within category

        Returns:
            Dict[str, Any]: Filtered metrics
        """
        if category and name:
            return self.metrics.get(category, {}).get(name, {})  # type: ignore[no-any-return]
        if category:
            return self.metrics.get(category, {})  # type: ignore[no-any-return]
        return self.metrics

    @classmethod
    def load_dashboard(cls, dashboard_id: str) -> "Dashboard":
        """
        Load a dashboard from a file.

        Args:
            dashboard_id: ID of the dashboard to load

        Returns:
            Dashboard: The loaded dashboard
        """
        dashboard = cls(dashboard_id)
        data_file = os.path.join(DASHBOARD_DATA_DIR, f"{dashboard_id}.json")

        if os.path.exists(data_file):
            with open(data_file) as f:
                dashboard.metrics = json.load(f)

        return dashboard


# Decorators for observability
def trace_task(tracer: Tracer):
    """
    Decorator to trace task execution.

    Args:
        tracer: The tracer to use

    Returns:
        Callable: The decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract task information
            task_name = func.__name__

            # Record task start
            start_details = {"task_name": task_name, "args": str(args), "kwargs": str(kwargs)}
            tracer.add_event(TraceEvent("task_start", f"task:{task_name}", start_details))

            # Execute the task
            start_time = time.time()
            try:
                success = False  # Initialize success to False
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = str(e)
                success = False
                error_details = {"task_name": task_name, "error": str(e)}
                tracer.add_event(TraceEvent("task_error", f"task:{task_name}", error_details))
                raise
            finally:
                # Record task end
                end_time = time.time()
                end_details = {
                    "task_name": task_name,
                    "duration": end_time - start_time,
                    "success": success,
                    "result_type": type(result).__name__ if success else None,
                }
                tracer.add_event(TraceEvent("task_end", f"task:{task_name}", end_details))

            return result

        return wrapper

    return decorator


def monitor_agent(dashboard: Dashboard):
    """
    Decorator to monitor agent activity.

    Args:
        dashboard: The dashboard to use

    Returns:
        Callable: The decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent information
            agent_name = func.__name__

            # Update agent metrics
            dashboard.update_metric(
                category="agents",
                name=agent_name,
                metric="calls",
                value=dashboard.get_metrics("agents", agent_name).get("calls", 0) + 1,
            )

            # Execute the agent function
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            # Update more metrics
            dashboard.update_metric(
                category="agents", name=agent_name, metric="last_execution_time", value=end_time - start_time
            )

            dashboard.update_metric(
                category="agents",
                name=agent_name,
                metric="last_execution_timestamp",
                value=datetime.now().isoformat(),
            )

            return result

        return wrapper

    return decorator


def guard_output(hallucination_guard: HallucinationGuard, context: dict[str, Any] | None = None):
    """
    Decorator to guard against hallucinations in function outputs.

    Args:
        hallucination_guard: The hallucination guard to use
        context: Context information for validation

    Returns:
        Callable: The decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function
            result = func(*args, **kwargs)

            # Only validate string outputs
            if isinstance(result, str):
                # Use function name and args as context if not provided
                ctx = context or {"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}

                # Validate the output
                validation = hallucination_guard.validate_output(
                    output=result, context=ctx, fix_hallucinations=True
                )

                # Log warnings if any
                if validation["warnings"]:
                    logger.warning(
                        f"Potential hallucinations in {func.__name__} output: {validation['warnings']}"
                    )

                # Return the fixed output if available
                if validation["fixed_output"]:
                    return validation["fixed_output"]

            return result

        return wrapper

    return decorator


# Factory function to get observability tools
def get_observability_tools(crew_name: str) -> dict[str, Any]:
    """
    Get observability tools for a crew.

    Args:
        crew_name: Name of the crew

    Returns:
        Dict[str, Any]: Dictionary of observability tools
    """
    # Create a trace ID based on crew name and timestamp
    trace_id = f"{crew_name}_{int(time.time())}"
    dashboard_id = f"{crew_name}_dashboard"

    # Create tools
    tracer = Tracer(trace_id)
    dashboard = Dashboard(dashboard_id)
    hallucination_guard = HallucinationGuard()

    return {
        "tracer": tracer,
        "dashboard": dashboard,
        "hallucination_guard": hallucination_guard,
        "trace_task": lambda: trace_task(tracer),
        "monitor_agent": lambda: monitor_agent(dashboard),
        "guard_output": lambda ctx=None: guard_output(hallucination_guard, ctx),
    }
