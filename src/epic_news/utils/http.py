"""Shared HTTP utilities for tools.

- Exposes a preconfigured httpx client (HTTP/2, sane timeouts, UA headers).
- Provides retrying helpers via tenacity for transient errors (timeouts, 5xx).
- Offers a convenience function to enable requests-cache for legacy requests callers.
"""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

try:
    import requests_cache
except Exception:  # pragma: no cover
    requests_cache = None  # type: ignore[assignment]

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (compatible; EpicNews/1.0; +https://example.com)"
}

_client: httpx.Client | None = None
_async_client: httpx.AsyncClient | None = None


def get_httpx_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0),
            headers=_DEFAULT_HEADERS.copy(),
            follow_redirects=True,
        )
    return _client


def get_async_httpx_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            http2=True,
            timeout=httpx.Timeout(10.0, connect=5.0, read=10.0, write=10.0),
            headers=_DEFAULT_HEADERS.copy(),
            follow_redirects=True,
        )
    return _async_client


def _retry_predicate(exc: Exception) -> bool:
    # Retry on transient network issues and 5xx HTTP responses only
    if isinstance(
        exc, httpx.ConnectTimeout | httpx.ReadTimeout | httpx.WriteError | httpx.RemoteProtocolError
    ):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            status = exc.response.status_code
            return 500 <= status < 600
        except Exception:
            return False
    return False


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception(_retry_predicate),  # type: ignore[arg-type]
    reraise=True,
)
def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float | httpx.Timeout | None = None,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    client = get_httpx_client()
    resp = client.get(url, headers=headers, timeout=timeout, params=params)
    # Always raise for >=400; retry predicate will only retry on 5xx
    resp.raise_for_status()
    return resp


def configure_requests_cache(
    cache_name: str = "http_cache", expire_after: int = 900, allowable_methods: list[str] | None = None
) -> None:
    """Enable requests-cache for legacy `requests` users.

    This is a no-op if requests-cache is unavailable.
    """
    if requests_cache is None:  # pragma: no cover
        return
    if allowable_methods is None:
        allowable_methods = ["GET", "HEAD"]
    requests_cache.install_cache(
        cache_name=cache_name, expire_after=expire_after, allowable_methods=allowable_methods
    )
