"""Tests for transient-failure retry in kickoff_flow.

A deep_research run once died at its final task because OpenRouter's upstream Mistral
provider returned an error-shaped completion (content=None, tool_calls=None, 0 tokens).
The instructor TOOLS-mode parser raised ``'NoneType' object is not iterable``, which it
classifies as non-retryable, so ~19 minutes of prior agent work was discarded.

kickoff_flow now retries that class of failure -- and only that class.
"""

import asyncio

import pytest
from loguru import logger

from epic_news.utils.flow_enforcement import _is_transient_error, akickoff_flow, kickoff_flow
from epic_news.utils.interrupt import RunCancelledError, request_cancellation, reset_cancellation


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


@pytest.mark.parametrize(
    "message",
    [
        "litellm.Timeout: Connection timed out after 600.0 seconds",
        "Request timed out",
        "APITimeoutError: request timeout",
    ],
)
def test_timeouts_are_not_retried(message):
    # A raw request timeout means the full per-call budget was already burned; replaying
    # the whole multi-agent crew is wasteful and the cause is structural, not a blip.
    assert not _is_transient_error(RuntimeError(message))


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
    assert not any(msg.startswith("📊 Crew") for _, msg in records), "failure logged as success"


def test_success_still_logs_completion():
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda m: records.append((m.record["level"].name, m.record["message"])))
    try:
        kickoff_flow(FakeCrew([]), {"topic": "x"})
    finally:
        logger.remove(sink_id)

    assert any(msg.startswith("📊 Crew") for _, msg in records)


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
    assert not any(msg.startswith("📊 Crew") for _, msg in records), "failure logged as success"


def test_default_is_a_single_attempt(monkeypatch):
    monkeypatch.delenv("CREW_KICKOFF_ATTEMPTS", raising=False)
    from epic_news.utils.flow_enforcement import _retry_settings

    attempts, _ = _retry_settings()
    assert attempts == 1


@pytest.fixture
def request_cancel():
    """Set the cancel flag, and clear it after the test so other tests are not affected."""
    reset_cancellation()
    yield request_cancellation
    reset_cancellation()


@pytest.fixture
def caplog_loguru():
    """Loguru messages emitted during the test, as a list of strings."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]))
    yield messages
    logger.remove(sink_id)


def _crew_raising(fn, use_async):
    """A crew whose kickoff (sync) or akickoff (async) calls ``fn``."""
    if use_async:

        class _AsyncCrew:
            async def akickoff(self, inputs):
                return fn()

        return _AsyncCrew()

    class _SyncCrew:
        def kickoff(self, inputs):
            return fn()

    return _SyncCrew()


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_cancel_between_attempts_stops_the_next_one(monkeypatch, use_async, request_cancel):
    """Ctrl+C after a transient failure stops the retry, sync and async alike."""
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "3")
    monkeypatch.setenv("CREW_KICKOFF_BACKOFF_SECONDS", "0")
    calls: list[int] = []

    def _fail_then_cancel(*_a, **_k):
        calls.append(1)
        request_cancel()  # the user presses Ctrl+C while the first attempt fails
        raise RuntimeError("503 service unavailable")

    crew = _crew_raising(_fail_then_cancel, use_async)
    with pytest.raises(RunCancelledError):
        if use_async:
            asyncio.run(akickoff_flow(crew, {"topic": "x"}))
        else:
            kickoff_flow(crew, {"topic": "x"})
    assert calls == [1]


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_non_transient_error_fails_on_the_first_attempt(monkeypatch, use_async, caplog_loguru):
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "3")
    calls: list[int] = []

    def _bad_config(*_a, **_k):
        calls.append(1)
        raise ValueError("missing template variable")

    crew = _crew_raising(_bad_config, use_async)
    with pytest.raises(ValueError, match="missing template variable"):
        if use_async:
            asyncio.run(akickoff_flow(crew, {"topic": "x"}))
        else:
            kickoff_flow(crew, {"topic": "x"})
    assert calls == [1]
    assert any("failed after" in m and "attempt 1/3" in m for m in caplog_loguru)
