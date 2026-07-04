"""Deterministic end-to-end tests for ReceptionFlow with stubbed crew kickoffs.

No LLM calls: kickoff_flow/akickoff_flow are patched in epic_news.main.
All file output is redirected to tmp_path via monkeypatch.chdir (the flow's
paths are cwd-relative).
"""

import json

from epic_news.main import ReceptionFlow
from epic_news.models.extracted_info import ExtractedInfo


class FakeCrewOutput:
    """Mimics crewai CrewOutput for the attributes ReceptionFlow reads."""

    def __init__(self, raw: str = "", pydantic=None):
        self.raw = raw
        self.pydantic = pydantic
        self.tasks_output = []
        self.json_dict = None

    def __str__(self) -> str:
        return self.raw


def test_flow_constructs():
    flow = ReceptionFlow(user_request="test request")
    assert flow._user_request == "test request"


def _fake_kickoff_factory(classification: str, poem_json: str):
    """Returns a kickoff_flow replacement dispatching on crew class name."""

    def fake_kickoff(crew_or_factory, context):
        crew_name = type(crew_or_factory).__name__
        if crew_name == "InformationExtractionCrew":
            return FakeCrewOutput(
                raw="{}",
                pydantic=ExtractedInfo(
                    main_subject_or_activity="a test poem",
                    topic="a test poem",
                ),
            )
        if crew_name == "ClassifyCrew":
            return FakeCrewOutput(raw=classification)
        if crew_name == "PoemCrew":
            return FakeCrewOutput(raw=poem_json)
        raise AssertionError(f"Unexpected crew kicked off: {crew_name}")

    return fake_kickoff


def test_poem_route_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")
    # epic_news.utils.observability creates "traces/" once at import time,
    # relative to the cwd active then (the repo root, not tmp_path). The
    # @trace_task decorator on every flow method writes into that directory
    # by relative path, so after chdir it must be recreated here.
    (tmp_path / "traces").mkdir()

    poem_json = json.dumps({"title": "Ode to Tests", "poem": "Lines of green.\nNo flakes seen."})
    monkeypatch.setattr("epic_news.main.kickoff_flow", _fake_kickoff_factory("POEM", poem_json))

    flow = ReceptionFlow(user_request="Write me a poem about tests")
    flow.kickoff()

    assert flow.state.selected_crew == "POEM"
    html = tmp_path / "output" / "poem" / "poem.html"
    assert html.exists(), "poem HTML was not written"
    content = html.read_text(encoding="utf-8")
    assert "Ode to Tests" in content
    assert flow.state.email_sent is True  # email step ran and was gated off


def test_unknown_category_routes_to_error_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")
    # See comment in test_poem_route_end_to_end: traces/ must be recreated
    # under tmp_path since observability.py only creates it once at import
    # time, relative to the original cwd.
    (tmp_path / "traces").mkdir()

    monkeypatch.setattr(
        "epic_news.main.kickoff_flow",
        _fake_kickoff_factory("GIBBERISH_NO_CATEGORY", "{}"),
    )

    flow = ReceptionFlow(user_request="unclassifiable nonsense")
    flow.kickoff()

    assert flow.state.selected_crew == "UNKNOWN"
    assert flow.state.final_report is not None
    assert flow.state.final_report.startswith("Error:")
