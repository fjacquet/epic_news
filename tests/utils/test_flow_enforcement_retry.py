"""Tests for transient-failure retry in kickoff_flow.

A deep_research run once died at its final task because OpenRouter's upstream Mistral
provider returned an error-shaped completion (content=None, tool_calls=None, 0 tokens).
The instructor TOOLS-mode parser raised ``'NoneType' object is not iterable``, which it
classifies as non-retryable, so ~19 minutes of prior agent work was discarded.

kickoff_flow now retries that class of failure -- and only that class.
"""

import pytest
from loguru import logger

from epic_news.utils.flow_enforcement import _is_transient_error, akickoff_flow, kickoff_flow


class FakeCrew:
    """Minimal stand-in for a CrewAI Crew factory."""

    def __init__(self, failures: list[Exception | None]):
        self._failures = list(failures)
        self.kickoff_calls = 0

    def crew(self):
        return self

    def kickoff(self, inputs):
        self.kickoff_calls += 1
        outcome = self._failures.pop(0) if self._failures else None
        if isinstance(outcome, Exception):
            raise outcome
        return f"ok:{inputs.get('topic')}"


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch):
    """Keep the backoff from actually sleeping during tests."""
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "3")
    monkeypatch.setenv("CREW_KICKOFF_BACKOFF_SECONDS", "0")


@pytest.mark.parametrize(
    "message",
    [
        "No tool calls or function call found in response (mode: TOOLS)",
        "'NoneType' object is not iterable",
        "Max retries exceeded. Total attempts: 1",
        "Rate limit exceeded",
        "503 Service Unavailable",
        "Request timed out",
    ],
)
def test_transient_markers_recognised(message):
    assert _is_transient_error(RuntimeError(message))


@pytest.mark.parametrize(
    "message",
    [
        "1 validation error for DeepResearchReport",
        "KeyError: 'tools'",
        "FileNotFoundError: output/deep_research/python_scripts",
    ],
)
def test_real_bugs_are_not_treated_as_transient(message):
    assert not _is_transient_error(ValueError(message))


def test_retries_transient_failure_then_succeeds():
    crew = FakeCrew([TypeError("'NoneType' object is not iterable"), None])

    result = kickoff_flow(crew, {"topic": "crewai"})

    assert result == "ok:crewai"
    assert crew.kickoff_calls == 2, "should have retried exactly once"


def test_gives_up_after_configured_attempts():
    crew = FakeCrew([TypeError("'NoneType' object is not iterable")] * 5)

    with pytest.raises(TypeError):
        kickoff_flow(crew, {"topic": "crewai"})

    assert crew.kickoff_calls == 3, "should stop at CREW_KICKOFF_ATTEMPTS"


def test_non_transient_error_fails_fast_without_retry():
    crew = FakeCrew([ValueError("1 validation error for DeepResearchReport")])

    with pytest.raises(ValueError):
        kickoff_flow(crew, {"topic": "crewai"})

    assert crew.kickoff_calls == 1, "a real bug must not be retried"


def test_failure_is_logged_as_error_not_success():
    """The old `finally` block logged the success checkmark even when kickoff raised."""
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda m: records.append((m.record["level"].name, m.record["message"])))
    try:
        with pytest.raises(ValueError):
            kickoff_flow(FakeCrew([ValueError("boom")]), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    levels = {level for level, _ in records}
    assert "ERROR" in levels
    assert not any("finished in" in msg for _, msg in records), "failure logged as success"


def test_success_still_logs_completion():
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda m: records.append((m.record["level"].name, m.record["message"])))
    try:
        kickoff_flow(FakeCrew([]), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    assert any("finished in" in msg for _, msg in records)


class FakeAsyncCrew:
    """Async stand-in; akickoff_flow drives the parallel OSINT crews."""

    def __init__(self, failures: list[Exception | None]):
        self._failures = list(failures)
        self.kickoff_calls = 0

    def crew(self):
        return self

    async def akickoff(self, inputs):
        self.kickoff_calls += 1
        outcome = self._failures.pop(0) if self._failures else None
        if isinstance(outcome, Exception):
            raise outcome
        return f"ok:{inputs.get('topic')}"


@pytest.mark.asyncio
async def test_async_retries_transient_failure_then_succeeds():
    crew = FakeAsyncCrew([TypeError("'NoneType' object is not iterable"), None])

    result = await akickoff_flow(crew, {"topic": "crewai"})

    assert result == "ok:crewai"
    assert crew.kickoff_calls == 2


@pytest.mark.asyncio
async def test_async_non_transient_error_fails_fast():
    crew = FakeAsyncCrew([ValueError("1 validation error for WebPresenceReport")])

    with pytest.raises(ValueError):
        await akickoff_flow(crew, {"topic": "crewai"})

    assert crew.kickoff_calls == 1


@pytest.mark.asyncio
async def test_async_gives_up_after_configured_attempts():
    crew = FakeAsyncCrew([TypeError("'NoneType' object is not iterable")] * 5)

    with pytest.raises(TypeError):
        await akickoff_flow(crew, {"topic": "crewai"})

    assert crew.kickoff_calls == 3


@pytest.mark.asyncio
async def test_async_failure_is_not_logged_as_success():
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda m: records.append((m.record["level"].name, m.record["message"])))
    try:
        with pytest.raises(ValueError):
            await akickoff_flow(FakeAsyncCrew([ValueError("boom")]), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    assert "ERROR" in {level for level, _ in records}
    assert not any("finished in" in msg for _, msg in records), "failure logged as success"
