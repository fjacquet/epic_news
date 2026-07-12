"""extract_info stores the enriched brief on state, falling back to the raw request."""

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow


class _TaskOutput:
    def __init__(self, raw):
        self.raw = raw


class _Result:
    def __init__(self, tasks_output, pydantic=None):
        self.tasks_output = tasks_output
        self.pydantic = pydantic


def _flow(monkeypatch, result):
    flow = ReceptionFlow(user_request="raw messy request")
    flow.state.user_request = "raw messy request"
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda *a, **k: result)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    return flow


def test_captures_enriched_brief(monkeypatch):
    result = _Result([_TaskOutput("Clean brief"), _TaskOutput("{}")], pydantic=None)
    flow = _flow(monkeypatch, result)

    flow.extract_info()

    assert flow.state.enriched_brief == "Clean brief"


def test_falls_back_to_raw_request_when_no_brief(monkeypatch):
    result = _Result([], pydantic=None)  # crew produced no task outputs
    flow = _flow(monkeypatch, result)

    flow.extract_info()

    assert flow.state.enriched_brief == "raw messy request"
