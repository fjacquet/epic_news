import json

from crewai_tools import ScrapeWebsiteTool

from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool


def _fake_page(text):
    def _run(self, **kwargs):
        return text

    return _run


def test_long_page_is_truncated(monkeypatch):
    monkeypatch.setenv("SCRAPE_MAX_CHARS", "100")
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("é" * 500))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert out["url"] == "https://example.com"
    assert out["truncated"] is True
    assert out["content"] == "é" * 100


def test_short_page_is_untouched(monkeypatch):
    monkeypatch.setenv("SCRAPE_MAX_CHARS", "100")
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("short page"))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert out == {"url": "https://example.com", "content": "short page", "truncated": False}


def test_default_cap(monkeypatch):
    monkeypatch.delenv("SCRAPE_MAX_CHARS", raising=False)
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("x" * 20000))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert len(out["content"]) == 12000 and out["truncated"] is True


def test_scrape_error_becomes_json(monkeypatch):
    def _boom(self, **kwargs):
        raise ValueError("Website URL must be provided.")

    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _boom)
    out = json.loads(CappedScrapeWebsiteTool()._run())
    assert "error" in out


def test_same_tool_name_as_crewai_scraper():
    assert CappedScrapeWebsiteTool().name == ScrapeWebsiteTool().name
