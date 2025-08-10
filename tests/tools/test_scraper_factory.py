import importlib
import sys
import types

import pytest

from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
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
    """
    Provide a stub FirecrawlTool in sys.modules so scraper_factory can import it
    without requiring external SDK or API key. Ensures the firecrawl branch works.
    """
    # Create stub module and class
    module_name = "epic_news.tools.firecrawl_tool"
    stub_module = types.ModuleType(module_name)

    class StubFirecrawlTool:  # no init requirements
        def __init__(self, **kwargs):
            pass

    stub_module.FirecrawlTool = StubFirecrawlTool

    # Inject into sys.modules
    sys.modules[module_name] = stub_module

    # Ensure future imports see the stub
    importlib.invalidate_caches()

    try:
        monkeypatch.setenv("WEB_SCRAPER_PROVIDER", "firecrawl")
        scraper = get_scraper()
        assert isinstance(scraper, StubFirecrawlTool)
    finally:
        # Cleanup stub
        sys.modules.pop(module_name, None)
        importlib.invalidate_caches()
