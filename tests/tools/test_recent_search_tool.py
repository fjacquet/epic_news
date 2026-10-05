import json

import pytest

from epic_news.tools import recent_search_tool
from epic_news.tools.recent_search_tool import RecentSearchTool


class _FakePerplexity:
    calls: list = []
    reply = '{"success": true, "data": {"answer": "x", "citations": []}, "error": null}'

    def _run(self, query, **kwargs):
        type(self).calls.append((query, kwargs))
        return type(self).reply


@pytest.fixture
def fake(monkeypatch):
    _FakePerplexity.calls = []
    _FakePerplexity.reply = '{"success": true, "data": {"answer": "x", "citations": []}, "error": null}'
    monkeypatch.setattr(recent_search_tool, "PerplexitySearchTool", _FakePerplexity)
    return _FakePerplexity


def test_searches_the_last_year_and_returns_json(fake):
    out = json.loads(RecentSearchTool()._run("EU AI act 2026"))
    assert fake.calls == [("EU AI act 2026", {"search_recency": "year"})]
    assert out["data"]["answer"] == "x"


def test_missing_api_key_points_to_hybrid_search(monkeypatch):
    def _boom():
        raise ValueError("PERPLEXITY_API_KEY missing")

    monkeypatch.setattr(recent_search_tool, "PerplexitySearchTool", _boom)
    out = json.loads(RecentSearchTool()._run("q"))
    assert "hybrid_search" in out["error"]


def test_error_payload_points_to_hybrid_search(fake):
    fake.reply = '{"success": false, "data": null, "error": "HTTP 429"}'
    out = json.loads(RecentSearchTool()._run("q"))
    assert "HTTP 429" in out["error"]
    assert "hybrid_search" in out["error"]
