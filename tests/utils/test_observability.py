import asyncio

import pytest
from faker import Faker

from epic_news.utils.observability import TraceEvent, Tracer, trace_task

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


def test_trace_task_records_an_async_step_after_it_finishes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    tracer = Tracer(trace_id="async_success_test")
    finished: list[bool] = []

    @trace_task(tracer)
    async def step():
        await asyncio.sleep(0)
        finished.append(True)
        return {"ok": True}

    assert asyncio.run(step()) == {"ok": True}
    end = tracer.get_events(event_type="task_end")[-1]
    assert finished == [True]
    assert end.details["success"] is True
    assert end.details["result_type"] == "dict"


def test_trace_task_records_an_async_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    tracer = Tracer(trace_id="async_error_test")

    @trace_task(tracer)
    async def step():
        raise RuntimeError("osint failed")

    with pytest.raises(RuntimeError, match="osint failed"):
        asyncio.run(step())
    assert tracer.get_events(event_type="task_error")[-1].details["error"] == "osint failed"
    assert tracer.get_events(event_type="task_end")[-1].details["success"] is False


def test_unused_tools_are_gone():
    import epic_news.utils.observability as observability

    for name in (
        "Dashboard",
        "HallucinationGuard",
        "monitor_agent",
        "guard_output",
        "get_observability_tools",
    ):
        assert not hasattr(observability, name), name


def test_trace_task_records_task_end_on_keyboard_interrupt(tmp_path, monkeypatch):
    """Ctrl+C inside a step still closes its trace with task_end only, as before S8."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "traces").mkdir()
    tracer = Tracer(trace_id="interrupt_test")

    @trace_task(tracer)
    def step():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        step()
    assert tracer.get_events(event_type="task_end")[-1].details["success"] is False
    assert tracer.get_events(event_type="task_error") == []
