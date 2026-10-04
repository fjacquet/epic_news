"""Contract: settings and tools on every built agent actually apply.

Construction only — zero LLM calls.
"""

from __future__ import annotations

from collections import Counter

import pytest
from crewai_tools import FileReadTool

from epic_news.config.llm_config import LLMConfig
from tests.crews._registry import ALL_CREW_CLASSES, build_crew

# Tool-name fragments that identify web search / scraping tools.
_WEB_TOOL_MARKERS = ("search", "scrape", "website", "fetch")


def _agents(crew_cls):
    return build_crew(crew_cls).agents


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_every_agent_llm_has_a_timeout(crew_cls):
    """The timeout must live on the LLM; Agent(llm_timeout=...) is silently dropped."""
    offenders = [a.role for a in _agents(crew_cls) if getattr(a.llm, "timeout", None) is None]
    assert not offenders, f"{crew_cls.__name__}: agents whose LLM has no timeout: {offenders}"


# Agents that deliberately override LLMConfig.get_max_iter(): (crew class, role) -> max_iter.
MAX_ITER_OVERRIDES = {
    # Analyses every ticker of the 60+ line portfolio CSV, roughly one tool call each.
    ("FinDailyCrew", "Senior Stock Analyst"): 30,
}


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_every_agent_uses_configured_max_iter(crew_cls):
    """Crew(max_iter=...) is not a field; the cap must be set on each Agent."""
    default = LLMConfig.get_max_iter()
    offenders = []
    for a in _agents(crew_cls):
        expected = MAX_ITER_OVERRIDES.get((crew_cls.__name__, a.role.strip()), default)
        if a.max_iter != expected:
            offenders.append(f"{a.role!r} (max_iter={a.max_iter}, expected {expected})")
    assert not offenders, f"{crew_cls.__name__}: agents with the wrong max_iter: {offenders}"


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_no_agent_holds_duplicate_tools(crew_cls):
    offenders = {}
    for a in _agents(crew_cls):
        dups = [n for n, k in Counter(t.name for t in a.tools or []).items() if k > 1]
        if dups:
            offenders[a.role] = dups
    assert not offenders, f"{crew_cls.__name__}: duplicate tools per agent: {offenders}"


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_no_unscoped_file_reader_next_to_web_tools(crew_cls):
    """Web content must not be able to steer an unscoped file reader (prompt injection)."""
    offenders = []
    for a in _agents(crew_cls):
        tools = a.tools or []
        has_file_reader = any(isinstance(t, FileReadTool) for t in tools)
        has_web_tool = any(m in t.name.lower() for t in tools for m in _WEB_TOOL_MARKERS)
        if has_file_reader and has_web_tool:
            offenders.append(a.role)
    assert not offenders, f"{crew_cls.__name__}: unscoped FileReadTool next to web tools on: {offenders}"
