"""CrewAI patches live in crewai_patches, are applied by the flow entry point, and apply once."""

import subprocess
import sys

from crewai import LLM

from epic_news.config import crewai_patches


def test_importing_the_flow_applies_the_patches():
    """In a fresh interpreter (conftest applies the patches for this process), main must apply them."""
    probe = (
        "import epic_news.main\n"
        "from crewai import LLM\n"
        "from crewai.llms.base_llm import BaseLLM\n"
        "assert getattr(LLM, '_openrouter_anthropic_patched', False)\n"
        "assert getattr(BaseLLM, '_react_tool_calling_forced', False)\n"
        "assert getattr(BaseLLM, '_retry_on_empty_patched', False)\n"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-2000:]


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
