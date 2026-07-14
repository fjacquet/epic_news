"""LLMConfig retries LLM.call when a provider returns empty content.

gemini/gemini-3.5-flash intermittently returns a thought-only response on CrewAI
ReAct steps (message.content is None with finish_reason=stop). CrewAI then raises
"Invalid response from LLM call - None or empty" and the task dies after its three
retries. The empties are stochastic, so re-issuing the identical call a few times
yields text. These tests exercise the retry loop deterministically (no live calls)
plus the emptiness predicate and confirm the class patch is applied.
"""

from crewai import LLM

from epic_news.config.llm_config import (
    _call_with_empty_retry,
    _is_empty_llm_response,
)


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
