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
        # LLMConfig.get_openrouter_llm() marks its LLMs two ways:
        #
        # 1. configured_via_llmconfig — a plain instance attribute set after
        #    construction. Fast, explicit, but a NON-field attribute that
        #    Pydantic's model_copy()/deepcopy drops. CrewAI copies agents (and
        #    their LLMs) while assembling some crews, which strips it.
        # 2. is_litellm=True — a real Pydantic field (survives copy) that
        #    LLMConfig sets to force LiteLLM routing (see llm_config.py for why:
        #    CrewAI 1.15's native provider sends strict tool schemas OpenRouter
        #    rejects). CrewAI's env-fallback construction
        #    (crewai.utilities.llm_utils._llm_via_environment_or_fallback)
        #    yields the NATIVE provider with is_litellm=False for our
        #    "openrouter/"-prefixed MODEL, so is_litellm=True reliably means
        #    "built by LLMConfig" here and, unlike the sentinel, survives copy.
        via_llmconfig = getattr(agent.llm, "configured_via_llmconfig", False) or (
            getattr(agent.llm, "is_litellm", False) is True
        )
        if not via_llmconfig:
            offenders.append(f"{agent.role!r} (llm={agent.llm!r})")
    assert not offenders, (
        f"{crew_cls.__name__}: agents not configured via LLMConfig.get_openrouter_llm(): {offenders}"
    )
