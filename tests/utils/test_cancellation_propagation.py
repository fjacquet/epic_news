"""A cancelled run must not start new provider work, and must not write a report."""

import pytest

from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.flow_enforcement import kickoff_flow
from epic_news.utils.interrupt import RunCancelledError, request_cancellation, reset_cancellation


@pytest.fixture(autouse=True)
def _clean_cancellation_flag():
    reset_cancellation()
    yield
    reset_cancellation()


class _CountingCrew:
    def __init__(self):
        self.kickoffs = 0

    def kickoff(self, inputs):
        self.kickoffs += 1
        return "ok"


class _CountingLLM:
    def __init__(self):
        self.calls = 0

    def call(self, messages):
        self.calls += 1
        return "## prose"


def test_kickoff_flow_refuses_to_start_a_cancelled_crew():
    crew = _CountingCrew()
    request_cancellation()

    with pytest.raises(RunCancelledError):
        kickoff_flow(crew, {"topic": "x"})

    assert crew.kickoffs == 0


def test_kickoff_flow_runs_normally_when_not_cancelled():
    crew = _CountingCrew()

    assert kickoff_flow(crew, {"topic": "x"}) == "ok"
    assert crew.kickoffs == 1


def test_cancellation_aborts_narration_instead_of_writing_placeholders(tmp_path):
    llm = _CountingLLM()
    out = tmp_path / "r.docx"
    request_cancellation()

    with pytest.raises(RunCancelledError):
        assemble_fragments(
            [
                Section("Intro", instruction="i", context="c"),
                Section("Budget", instruction="i", context="c"),
            ],
            {"title": "T", "author": "Epic News", "date": ""},
            str(out),
            llm,
            system="sys",
        )

    assert llm.calls == 0
    assert not out.exists()
