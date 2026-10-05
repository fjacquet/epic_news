"""CrewAI patches live in crewai_patches, are applied by the flow entry point, and apply once."""

import importlib

from crewai import LLM
from crewai.llms.base_llm import BaseLLM

from epic_news.config import crewai_patches


def test_importing_the_flow_applies_the_patches():
    importlib.import_module("epic_news.main")
    assert getattr(LLM, "_openrouter_anthropic_patched", False)
    assert getattr(BaseLLM, "_react_tool_calling_forced", False)
    assert getattr(BaseLLM, "_retry_on_empty_patched", False)


def test_apply_is_idempotent():
    crewai_patches.apply_crewai_patches()
    call_once = LLM.call
    acall_once = getattr(LLM, "acall", None)
    crewai_patches.apply_crewai_patches()
    assert LLM.call is call_once
    assert getattr(LLM, "acall", None) is acall_once


def test_llm_config_no_longer_holds_patches():
    from epic_news.config import llm_config

    for name in (
        "_with_llm_slot",
        "_call_with_empty_retry",
        "_wrap_call_for_react_safety",
        "_force_react_tool_calling",
    ):
        assert not hasattr(llm_config, name), name
