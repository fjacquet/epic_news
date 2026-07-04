"""Contract: every agent's LLM must come from LLMConfig (OpenRouter base_url).

Agents without llm= resolve via env fallback and silently lose temperature,
base_url, and reasoning settings. Construction only — zero LLM calls.
"""

import pytest

from tests.crews._registry import ALL_CREW_CLASSES, build_crew


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_every_agent_uses_llmconfig(crew_cls):
    crew = build_crew(crew_cls)
    offenders = []
    for agent in crew.agents:
        # configured_via_llmconfig is set explicitly by
        # LLMConfig.get_openrouter_llm() (src/epic_news/config/llm_config.py)
        # after constructing the LLM instance. CrewAI's own env-fallback LLM
        # construction (crewai.utilities.llm_utils.
        # _llm_via_environment_or_fallback) never sets this attribute, even
        # though it can resolve the same OpenRouter base_url from provider
        # defaults for "openrouter/"-prefixed MODEL values when llm= was
        # never passed to Agent(). The sentinel is therefore what actually
        # discriminates "configured via LLMConfig" from "env fallback" here.
        if not getattr(agent.llm, "configured_via_llmconfig", False):
            offenders.append(f"{agent.role!r} (llm={agent.llm!r})")
    assert not offenders, (
        f"{crew_cls.__name__}: agents not configured via LLMConfig.get_openrouter_llm(): {offenders}"
    )
