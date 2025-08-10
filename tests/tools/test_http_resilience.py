import httpx
import pytest

from epic_news.utils import http as http_utils


def test_http_get_retries_on_5xx(monkeypatch):
    # Arrange: stub client with flaky get
    attempts = {"count": 0}

    req = httpx.Request("GET", "https://example.com")

    def fake_get(url, headers=None, timeout=None, params=None):  # noqa: ARG001
        attempts["count"] += 1
        if attempts["count"] < 3:
            resp = httpx.Response(500, request=req)
            raise httpx.HTTPStatusError("server error", request=req, response=resp)
        return httpx.Response(200, request=req, content=b"ok")

    class StubClient:
        def get(self, *a, **k):  # noqa: ANN001, ANN002
            return fake_get(*a, **k)

    monkeypatch.setattr(http_utils, "get_httpx_client", lambda: StubClient())

    # Act
    resp = http_utils.http_get("https://example.com")

    # Assert: 3 attempts, final success
    assert attempts["count"] == 3
    assert resp.status_code == 200


def test_http_get_does_not_retry_on_4xx(monkeypatch):
    req = httpx.Request("GET", "https://example.com/404")

    def fake_get(url, headers=None, timeout=None, params=None):  # noqa: ARG001
        resp = httpx.Response(404, request=req)
        # raise_for_status happens in http_get, but we simulate raising here to test retry predicate too
        raise httpx.HTTPStatusError("not found", request=req, response=resp)

    class StubClient:
        def get(self, *a, **k):  # noqa: ANN001, ANN002
            return fake_get(*a, **k)

    attempts = {"count": 0}

    def counted_client():
        attempts["count"] += 1
        return StubClient()

    monkeypatch.setattr(http_utils, "get_httpx_client", counted_client)

    with pytest.raises(httpx.HTTPStatusError):
        http_utils.http_get("https://example.com/404")

    # Should only try once for 4xx
    assert attempts["count"] == 1
