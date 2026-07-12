"""OpenRouter-routed Anthropic models must not get CrewAI's native-Anthropic
message workaround.

CrewAI prepends a dummy ``{"role": "user", "content": "."}`` before a leading
system message for models it classifies as Anthropic. Over OpenRouter's
OpenAI-compatible endpoint LiteLLM forwards messages verbatim, so that prepend
leaves the system message at index 1 and Anthropic rejects the request
("messages.1: role 'system' must precede an 'assistant' message or end the
array"). Construction only — zero LLM calls.
"""

import copy

from crewai import LLM

from epic_news.config.llm_config import LLMConfig

ANTHROPIC_VIA_OPENROUTER = "openrouter/anthropic/claude-opus-4.8-fast"
SYSTEM_THEN_USER = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hi"},
]


def test_openrouter_anthropic_is_not_flagged_native_anthropic():
    llm = LLMConfig.get_openrouter_llm(model=ANTHROPIC_VIA_OPENROUTER)
    assert llm.is_anthropic is False


def test_no_dummy_user_prepended_before_system_message():
    llm = LLMConfig.get_openrouter_llm(model=ANTHROPIC_VIA_OPENROUTER)
    formatted = llm._format_messages_for_provider(SYSTEM_THEN_USER)
    assert formatted[0] == {"role": "system", "content": "You are helpful."}


def test_fix_survives_deepcopy():
    """CrewAI deep-copies agent LLMs while assembling crews; the fix must persist.

    LLM.__deepcopy__ reconstructs the LLM from the model string, re-running the
    validator that derives is_anthropic — so the classifier patch, not an instance
    override, is what keeps this correct after a copy.
    """
    llm = copy.deepcopy(LLMConfig.get_openrouter_llm(model=ANTHROPIC_VIA_OPENROUTER))
    assert llm.is_anthropic is False
    formatted = llm._format_messages_for_provider(SYSTEM_THEN_USER)
    assert formatted[0]["role"] == "system"


def test_classifier_only_exempts_openrouter_prefix():
    """The patch narrows detection by route, not by vendor: only ``openrouter/``
    models are exempted; native ``anthropic/``/``claude-`` routing stays flagged so
    LiteLLM's system-hoisting and CrewAI's prepend remain correct there."""
    assert LLM._is_anthropic_model(ANTHROPIC_VIA_OPENROUTER) is False
    assert LLM._is_anthropic_model("anthropic/claude-3-5-sonnet") is True
    assert LLM._is_anthropic_model("claude-3-5-haiku") is True
