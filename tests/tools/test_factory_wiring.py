"""Wiring tests for the repointed OSINT/web-search/fact-check factories.

After the tools migration these factories import their concrete tool classes
from `crewai_custom_tools`; these tests assert each factory returns the correct
package-sourced tool type (construction only — no network / no live keys).
"""

import pytest
from crewai_custom_tools import (
    DelegatingEmailSearchTool,
    GoogleFactCheckTool,
    PerplexitySearchTool,
    SerpApiTool,
    TavilyTool,
)

from epic_news.tools.email_search import get_email_search_tools
from epic_news.tools.fact_checking_factory import FactCheckingToolsFactory
from epic_news.tools.web_search_factory import WebSearchFactory


def test_web_search_factory_perplexity_with_key(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")
    assert isinstance(WebSearchFactory.create("perplexity"), PerplexitySearchTool)


def test_web_search_factory_perplexity_without_key_falls_back_to_tavily(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    assert isinstance(WebSearchFactory.create("perplexity"), TavilyTool)


def test_web_search_factory_serpapi():
    assert isinstance(WebSearchFactory.create("serpapi"), SerpApiTool)


def test_web_search_factory_tavily():
    assert isinstance(WebSearchFactory.create("tavily"), TavilyTool)


def test_web_search_factory_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown web search provider"):
        WebSearchFactory.create("bogus")


def test_fact_checking_factory_google():
    assert isinstance(FactCheckingToolsFactory.create("google"), GoogleFactCheckTool)


def test_fact_checking_factory_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown fact-checking provider"):
        FactCheckingToolsFactory.create("bogus")


def test_get_email_search_tools_returns_delegating_tool():
    tools = get_email_search_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], DelegatingEmailSearchTool)
