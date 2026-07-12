"""LLMConfig forces ReAct (text) tool-calling for every provider.

CrewAI's experimental agent executor uses LLM.supports_function_calling() to pick
native function-calling vs ReAct. Native function-calling trips executor bugs on
non-OpenAI providers (Gemini returns a tool_calls list that lands in the str field
TaskOutput.raw -> ValidationError; Anthropic rejects the forced-final-answer
prefill). This project's crews are tuned for ReAct, so native fc must stay off
regardless of the model. Construction only — zero LLM calls.
"""

import pytest

from epic_news.config.llm_config import LLMConfig

MODELS = [
    "gemini/gemini-3.5-flash",
    "openrouter/mistralai/mistral-small-2603",
    "openrouter/anthropic/claude-opus-4.8-fast",
]


@pytest.mark.parametrize("model", MODELS)
def test_native_function_calling_disabled(model):
    llm = LLMConfig.get_openrouter_llm(model=model)
    assert llm.supports_function_calling() is False
