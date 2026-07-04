"""Tests for the kickoff_flow wrapper: behavior and log formatting."""

import pytest
from loguru import logger

from epic_news.utils.flow_enforcement import kickoff_flow


class StubCrew:
    """Mimics a @CrewBase factory: has .crew() returning an object with .kickoff()."""

    def __init__(self):
        self.received_inputs = None

    def crew(self):
        return self

    def kickoff(self, inputs):
        self.received_inputs = inputs
        return "SENTINEL_RESULT"


def test_kickoff_flow_calls_kickoff_and_returns_result():
    stub = StubCrew()
    result = kickoff_flow(stub, {"topic": "x"})
    assert result == "SENTINEL_RESULT"
    assert stub.received_inputs == {"topic": "x"}


def test_kickoff_flow_rejects_non_dict_context():
    with pytest.raises(ValueError):
        kickoff_flow(StubCrew(), "not a dict")


def test_kickoff_flow_logs_are_formatted():
    """Placeholders must be interpolated: no literal '{}' or '%.2fs' in output."""
    records: list[str] = []
    sink_id = logger.add(lambda msg: records.append(str(msg)), level="INFO")
    try:
        kickoff_flow(StubCrew(), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    text = "".join(records)
    assert "StubCrew" in text
    assert "{}" not in text
    assert "%.2fs" not in text
