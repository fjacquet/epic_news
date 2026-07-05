import pytest
from faker import Faker

from epic_news.utils.observability import (
    Dashboard,
    HallucinationGuard,
    TraceEvent,
    Tracer,
    get_observability_tools,
    guard_output,
    monitor_agent,
    trace_task,
)

fake = Faker()


def test_trace_event():
    # Test that a TraceEvent is created correctly
    event = TraceEvent("test_event", "test_source", {"test_key": "test_value"})
    assert event.event_type == "test_event"
    assert event.source == "test_source"
    assert event.details == {"test_key": "test_value"}


def test_tracer(tmp_path):
    # Test that the Tracer traces events correctly
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    tracer = Tracer(trace_id="test_trace")
    tracer.trace_file = trace_dir / "test_trace.json"
    event = TraceEvent("test_event", "test_source", {"test_key": "test_value"})
    tracer.add_event(event)
    assert len(tracer.events) == 1
    assert tracer.events[0].event_type == "test_event"


def test_hallucination_guard():
    # Test that the HallucinationGuard detects hallucinations
    guard = HallucinationGuard(confidence_threshold=0.9)
    result = guard.check_statement("This is definitely true.", {})
    assert result["is_likely_hallucination"]
    result = guard.check_statement("This might be true.", {})
    assert not result["is_likely_hallucination"]


def test_dashboard(tmp_path):
    # Test that the Dashboard updates metrics correctly
    dashboard_dir = tmp_path / "dashboards"
    dashboard_dir.mkdir()
    dashboard = Dashboard(dashboard_id="test_dashboard")
    dashboard.data_file = dashboard_dir / "test_dashboard.json"
    dashboard.update_metric("test_category", "test_name", "test_metric", "test_value")
    assert dashboard.get_metrics("test_category", "test_name")["test_metric"] == "test_value"


def test_get_observability_tools():
    # Test that get_observability_tools returns a dictionary of observability tools
    tools = get_observability_tools("test_crew")
    assert "tracer" in tools
    assert "dashboard" in tools
    assert "hallucination_guard" in tools


def test_tracer_get_events_filter(tmp_path):
    # get_events should filter by event_type and return all events when no filter given
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    tracer = Tracer(trace_id="filter_test")
    tracer.trace_file = trace_dir / "filter_test.json"

    start_event = TraceEvent("task_start", "task:foo", {"n": 1})
    end_event = TraceEvent("task_end", "task:foo", {"n": 2})
    other_source_event = TraceEvent("task_start", "task:bar", {"n": 3})
    tracer.add_event(start_event)
    tracer.add_event(end_event)
    tracer.add_event(other_source_event)

    all_events = tracer.get_events()
    assert len(all_events) == 3

    start_events = tracer.get_events(event_type="task_start")
    assert len(start_events) == 2
    assert all(e.event_type == "task_start" for e in start_events)

    foo_events = tracer.get_events(source="task:foo")
    assert len(foo_events) == 2
    assert all(e.source == "task:foo" for e in foo_events)

    filtered_both = tracer.get_events(event_type="task_start", source="task:bar")
    assert filtered_both == [other_source_event]

    no_match = tracer.get_events(event_type="does_not_exist")
    assert no_match == []


def test_tracer_save_load_round_trip(tmp_path, monkeypatch):
    # Tracer writes events to TRACE_DIR (relative "traces") and load_trace reads them back
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()

    tracer = Tracer(trace_id="round_trip_test")
    tracer.add_event(TraceEvent("task_start", "task:rt", {"key": "value"}))
    tracer.add_event(TraceEvent("task_end", "task:rt", {"duration": 1.5}))

    loaded = Tracer.load_trace("round_trip_test")
    assert len(loaded.events) == 2
    assert loaded.events[0].event_type == "task_start"
    assert loaded.events[0].source == "task:rt"
    assert loaded.events[0].details == {"key": "value"}
    assert loaded.events[1].event_type == "task_end"
    assert loaded.events[1].details == {"duration": 1.5}

    # Loading a trace_id with no file yet returns an empty tracer, not an error
    empty = Tracer.load_trace("never_saved_trace")
    assert empty.events == []


def test_dashboard_unknown_category_and_name_return_empty():
    dashboard = Dashboard(dashboard_id="unknown_lookup_test")
    assert dashboard.get_metrics("nonexistent_category") == {}
    assert dashboard.get_metrics("nonexistent_category", "nonexistent_name") == {}
    # Known category, unknown name
    assert dashboard.get_metrics("agents", "nonexistent_agent") == {}


def test_dashboard_update_metric_then_get_metrics(tmp_path):
    dashboard_dir = tmp_path / "dashboards"
    dashboard_dir.mkdir()
    dashboard = Dashboard(dashboard_id="update_test")
    dashboard.data_file = dashboard_dir / "update_test.json"

    dashboard.update_metric("agents", "researcher", "calls", 1)
    assert dashboard.get_metrics("agents", "researcher") == {"calls": 1}
    assert dashboard.metrics["system"]["events_count"] == 1

    dashboard.update_metric("agents", "researcher", "calls", 2)
    assert dashboard.get_metrics("agents", "researcher")["calls"] == 2
    assert dashboard.metrics["system"]["events_count"] == 2

    # Category-only lookup returns the whole category dict
    assert dashboard.get_metrics("agents") == {"researcher": {"calls": 2}}


def test_hallucination_guard_check_statement_confident_vs_hedged():
    guard = HallucinationGuard(confidence_threshold=0.9)

    confident = guard.check_statement("This is definitely and absolutely true.", {})
    assert confident["is_likely_hallucination"] is True
    assert "Overly confident language detected" in confident["warnings"]
    assert confident["confidence"] < 0.9

    hedged = guard.check_statement("This might possibly be true.", {})
    assert hedged["is_likely_hallucination"] is False
    assert hedged["warnings"] == []
    assert hedged["confidence"] == 1.0


def test_hallucination_guard_validate_output_fix_true_and_false():
    guard = HallucinationGuard(confidence_threshold=0.9)
    output = "This is definitely true. This might be true."

    fixed_result = guard.validate_output(output, {}, fix_hallucinations=True)
    assert fixed_result["hallucination_score"] == 0.5
    assert fixed_result["fixed_output"] == output + (
        "\n\nNote: Some statements in this output may require further verification."
    )
    assert fixed_result["warnings"] != []

    unfixed_result = guard.validate_output(output, {}, fix_hallucinations=False)
    assert unfixed_result["hallucination_score"] == 0.5
    assert unfixed_result["fixed_output"] is None


def test_trace_task_decorator_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    tracer = Tracer(trace_id="decorator_success_test")

    @trace_task(tracer)
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5

    events = tracer.get_events()
    event_types = [e.event_type for e in events]
    assert event_types == ["task_start", "task_end"]

    end_event = events[1]
    assert end_event.details["success"] is True
    assert end_event.details["result_type"] == "int"
    assert end_event.details["task_name"] == "add"


def test_trace_task_decorator_exception_propagates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    tracer = Tracer(trace_id="decorator_error_test")

    @trace_task(tracer)
    def boom():
        raise ValueError("kaboom")

    with pytest.raises(ValueError, match="kaboom"):
        boom()

    event_types = [e.event_type for e in tracer.get_events()]
    assert event_types == ["task_start", "task_error", "task_end"]

    end_event = tracer.get_events(event_type="task_end")[0]
    assert end_event.details["success"] is False
    assert end_event.details["result_type"] is None

    error_event = tracer.get_events(event_type="task_error")[0]
    assert error_event.details["error"] == "kaboom"


def test_monitor_agent_decorator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "dashboard_data").mkdir(parents=True)
    dashboard = Dashboard(dashboard_id="decorator_agent_test")

    @monitor_agent(dashboard)
    def agent_func(x):
        return x * 2

    result = agent_func(21)
    assert result == 42

    metrics = dashboard.get_metrics("agents", "agent_func")
    assert metrics["calls"] == 1
    assert "last_execution_time" in metrics
    assert "last_execution_timestamp" in metrics

    agent_func(1)
    assert dashboard.get_metrics("agents", "agent_func")["calls"] == 2


def test_guard_output_decorator_fixes_hallucination():
    guard = HallucinationGuard(confidence_threshold=0.9)

    @guard_output(guard)
    def produce_confident_output():
        return "This is definitely a famous and well-known fact."

    result = produce_confident_output()
    assert result != "This is definitely a famous and well-known fact."
    assert result.endswith("Note: Some statements in this output may require further verification.")


def test_guard_output_decorator_passes_through_clean_output():
    guard = HallucinationGuard(confidence_threshold=0.9)

    @guard_output(guard)
    def produce_clean_output():
        return "The sky appears blue during the day."

    result = produce_clean_output()
    assert result == "The sky appears blue during the day."


def test_guard_output_decorator_ignores_non_string_output():
    guard = HallucinationGuard(confidence_threshold=0.9)

    @guard_output(guard)
    def produce_non_string():
        return {"definitely": "not a string"}

    result = produce_non_string()
    assert result == {"definitely": "not a string"}


def test_get_observability_tools_full_contract():
    tools = get_observability_tools("contract_crew")

    assert set(tools.keys()) == {
        "tracer",
        "dashboard",
        "hallucination_guard",
        "trace_task",
        "monitor_agent",
        "guard_output",
    }
    assert isinstance(tools["tracer"], Tracer)
    assert isinstance(tools["dashboard"], Dashboard)
    assert isinstance(tools["hallucination_guard"], HallucinationGuard)
    assert tools["tracer"].trace_id.startswith("contract_crew_")
    assert tools["dashboard"].dashboard_id == "contract_crew_dashboard"

    # Decorator factories return callables usable as decorators
    assert callable(tools["trace_task"]())
    assert callable(tools["monitor_agent"]())
    assert callable(tools["guard_output"]())
