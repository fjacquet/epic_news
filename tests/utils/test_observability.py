from faker import Faker

from epic_news.utils.observability import (
    Dashboard,
    HallucinationGuard,
    TraceEvent,
    Tracer,
    get_observability_tools,
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
