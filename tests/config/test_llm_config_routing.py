"""LLMConfig transport routing.

Only ``openrouter/``-prefixed models go through OpenRouter's OpenAI-compatible
endpoint. Native provider prefixes (``gemini/``, ``anthropic/``, ...) must be left
for LiteLLM to route with their own env credentials — forcing OpenRouter's
base_url/api_key on them breaks the call. Construction only — zero LLM calls.
"""

from epic_news.config.llm_config import LLMConfig


def test_openrouter_model_uses_openrouter_transport():
    llm = LLMConfig.get_openrouter_llm(model="openrouter/mistralai/mistral-small-2603")
    assert llm.base_url == "https://openrouter.ai/api/v1"
    assert llm.is_litellm is True


def test_native_provider_model_leaves_transport_to_litellm():
    llm = LLMConfig.get_openrouter_llm(model="gemini/gemini-3.5-flash")
    assert llm.base_url is None
    assert llm.is_litellm is True
