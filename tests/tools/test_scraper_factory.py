import pytest
from crewai_custom_tools import ScrapeNinjaTool

from epic_news.tools.scraper_factory import get_scraper


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Ensure we start each test without provider env set
    monkeypatch.delenv("WEB_SCRAPER_PROVIDER", raising=False)
    yield
    monkeypatch.delenv("WEB_SCRAPER_PROVIDER", raising=False)


def test_get_scraper_default_returns_scrapeninja(monkeypatch):
    monkeypatch.delenv("WEB_SCRAPER_PROVIDER", raising=False)
    scraper = get_scraper()
    assert isinstance(scraper, ScrapeNinjaTool)


def test_get_scraper_explicit_scrapeninja(monkeypatch):
    monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "scrapeninja")
    scraper = get_scraper()
    assert isinstance(scraper, ScrapeNinjaTool)


def test_get_scraper_invalid_provider_raises_valueerror(monkeypatch):
    monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "invalid_provider")
    with pytest.raises(ValueError):
        _ = get_scraper()


def test_get_scraper_composio_not_implemented(monkeypatch):
    monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "composio")
    with pytest.raises(NotImplementedError):
        _ = get_scraper()


def test_get_scraper_tavily_valueerror(monkeypatch):
    monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "tavily")
    with pytest.raises(ValueError):
        _ = get_scraper()


def test_get_scraper_firecrawl_with_stub(monkeypatch):
    """Patch FirecrawlTool where scraper_factory imports it (package top-level)."""

    class StubFirecrawlTool:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr("crewai_custom_tools.FirecrawlTool", StubFirecrawlTool)
    monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "firecrawl")
    scraper = get_scraper()
    assert isinstance(scraper, StubFirecrawlTool)
