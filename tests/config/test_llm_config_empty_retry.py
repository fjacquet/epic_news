"""LLMConfig retries LLM.call when a provider returns empty content.

gemini/gemini-3.7-flash intermittently returns a thought-only response on CrewAI
ReAct steps (message.content is None with finish_reason=stop). CrewAI then raises
"Invalid response from LLM call - None or empty" and the task dies after its three
retries. The empties are stochastic, so re-issuing the identical call a few times
yields text. These tests exercise the retry loop deterministically (no live calls)
plus the emptiness predicate and confirm the class patch is applied.
"""

import asyncio

import pytest
from crewai import LLM
from crewai.llms.base_llm import BaseLLM

from epic_news.config import llm_config
from epic_news.config.llm_config import (
    _acall_with_empty_retry,
    _call_with_empty_retry,
    _is_empty_llm_response,
)


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    """Record backoff delays instead of sleeping for real (sync and async)."""
    delays: list[float] = []

    async def fake_async_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(llm_config, "_sleep", delays.append)
    monkeypatch.setattr(llm_config, "_async_sleep", fake_async_sleep)
    return delays


def test_is_empty_llm_response_predicate():
    assert _is_empty_llm_response(None) is True
    assert _is_empty_llm_response("") is True
    assert _is_empty_llm_response("   \n\t ") is True
    assert _is_empty_llm_response("Final Answer: ok") is False
    assert _is_empty_llm_response(0) is False  # a non-str truthy-ish value is not "empty text"


def test_retry_returns_first_non_empty():
    seq = iter(["", "  ", "Action: search"])
    calls = {"n": 0}

    def call_fn():
        calls["n"] += 1
        return next(seq)

    result = _call_with_empty_retry(call_fn, max_retries=6, model="gemini/test")
    assert result == "Action: search"
    assert calls["n"] == 3  # two empties, then success


def test_non_empty_first_call_does_not_retry():
    calls = {"n": 0}

    def call_fn():
        calls["n"] += 1
        return "immediate answer"

    result = _call_with_empty_retry(call_fn, max_retries=6, model="m")
    assert result == "immediate answer"
    assert calls["n"] == 1  # returned on the first call, no retries


def test_gives_up_after_max_retries_returns_last():
    calls = {"n": 0}

    def call_fn():
        calls["n"] += 1
        return ""  # always empty

    result = _call_with_empty_retry(call_fn, max_retries=3, model="m")
    assert result == ""  # returns the last (still empty) result for normal handling
    assert calls["n"] == 4  # 1 initial + 3 retries


def test_max_retries_zero_disables_retry():
    calls = {"n": 0}

    def call_fn():
        calls["n"] += 1
        return

    result = _call_with_empty_retry(call_fn, max_retries=0, model="m")
    assert result is None
    assert calls["n"] == 1


def test_llm_call_is_patched():
    assert getattr(LLM, "_retry_on_empty_patched", False) is True


def test_backoff_sleeps_once_per_retry_and_grows(sleeps):
    _call_with_empty_retry(lambda: "", max_retries=4, model="m")
    assert len(sleeps) == 4
    # Exponential base 0.5s with jitter in [50%, 100%] of the nominal delay.
    for attempt, delay in enumerate(sleeps, start=1):
        nominal = min(8.0, 0.5 * 2 ** (attempt - 1))
        assert nominal / 2 <= delay <= nominal


def test_backoff_is_capped(sleeps):
    _call_with_empty_retry(lambda: "", max_retries=10, model="m")
    assert max(sleeps) <= 8.0
    assert sleeps[-1] >= 4.0  # nominal capped at 8s, jitter keeps it >= half


def test_no_sleep_when_first_call_succeeds(sleeps):
    _call_with_empty_retry(lambda: "text", max_retries=4, model="m")
    assert sleeps == []


def test_async_backoff_uses_async_sleep(sleeps):
    async def call_fn():
        return ""

    asyncio.run(_acall_with_empty_retry(call_fn, max_retries=3, model="m"))
    assert len(sleeps) == 3


def test_default_empty_retries_is_two(monkeypatch, sleeps):
    monkeypatch.delenv("LLM_EMPTY_RETRIES", raising=False)
    seen = {"n": 0}

    class _AlwaysEmpty(BaseLLM):
        def call(self, messages, **kwargs):
            seen["n"] += 1
            return ""

    _AlwaysEmpty(model="fake/model").call([])
    assert seen["n"] == 3  # 1 initial + 2 retries
    assert len(sleeps) == 2
