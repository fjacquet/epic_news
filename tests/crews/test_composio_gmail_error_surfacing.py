"""Composio Gmail failures must be surfaced, not swallowed.

A real run hit HTTP 401 (invalid COMPOSIO_API_KEY). The loader caught it with a bare
print(), returned [], and the resulting tool-less agent reported the email as sent.
These tests pin the loud-failure behaviour and the credential hint.
"""

from types import SimpleNamespace

import pytest
from loguru import logger

from epic_news.config.composio_config import ComposioConfig
from epic_news.crews.post.post_crew import PostCrew


@pytest.fixture
def config(monkeypatch) -> ComposioConfig:
    monkeypatch.setenv("COMPOSIO_API_KEY", "test-key-not-a-real-secret")
    cfg = ComposioConfig.__new__(ComposioConfig)
    cfg.api_key = "test-key-not-a-real-secret"
    cfg.user_id = "default"
    return cfg


def _capture(fn):
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda m: records.append((m.record["level"].name, m.record["message"])))
    try:
        result = fn()
    finally:
        logger.remove(sink_id)
    return result, records


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="COMPOSIO_API_KEY"):
        ComposioConfig(api_key=None, user_id="default")


def test_gmail_401_is_logged_as_error_with_credential_hint(config):
    def boom(**_kwargs):
        raise RuntimeError("Error code: 401 - Invalid API key")

    config.client = SimpleNamespace(tools=SimpleNamespace(get=boom))

    tools, records = _capture(config.get_gmail_email_tools)

    assert tools == []
    errors = [msg for level, msg in records if level == "ERROR"]
    assert errors, f"401 was swallowed; captured {records}"
    assert any("COMPOSIO_API_KEY" in msg for msg in errors), "no credential hint given"


def test_gmail_non_auth_error_logged_without_credential_hint(config):
    def boom(**_kwargs):
        raise RuntimeError("connection reset by peer")

    config.client = SimpleNamespace(tools=SimpleNamespace(get=boom))

    tools, records = _capture(config.get_gmail_email_tools)

    assert tools == []
    errors = [msg for level, msg in records if level == "ERROR"]
    assert errors
    assert not any("COMPOSIO_API_KEY" in msg for msg in errors)


def test_gmail_tools_returned_when_available(config):
    expected = [SimpleNamespace(name="GMAIL_SEND_EMAIL")]
    config.client = SimpleNamespace(tools=SimpleNamespace(get=lambda **_k: expected))

    assert config.get_gmail_email_tools() == expected


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("get_search_tools", {}),
        ("get_social_media_tools", {}),
        ("get_financial_tools", {}),
        ("get_communication_tools", {}),
        ("get_content_creation_tools", {}),
        ("get_custom_tools", {"toolkits": ["NOTION"]}),
    ],
)
def test_every_loader_logs_errors_instead_of_swallowing_them(config, method, kwargs):
    """Each loader used to swallow failures via a bare print(); all must log at ERROR."""

    def boom(**_kwargs):
        raise RuntimeError("composio exploded")

    config.client = SimpleNamespace(tools=SimpleNamespace(get=boom))

    tools, records = _capture(lambda: getattr(config, method)(**kwargs))

    assert tools == []
    assert any(level == "ERROR" for level, _ in records), f"{method} swallowed the failure"


def test_loaders_return_tools_on_success(config):
    ok = [SimpleNamespace(name="NOTION_SEARCH")]
    config.client = SimpleNamespace(tools=SimpleNamespace(get=lambda **_k: ok))

    assert config.get_custom_tools(toolkits=["NOTION"]) == ok


def _post_crew_with_gmail_tools(monkeypatch, tools):
    crew = PostCrew()
    monkeypatch.setattr(
        "epic_news.config.composio_config.ComposioConfig.__init__", lambda self: None, raising=False
    )
    monkeypatch.setattr(
        "epic_news.config.composio_config.ComposioConfig.get_gmail_email_tools",
        lambda self, include_send=True: tools,
        raising=False,
    )
    return crew


def test_send_tools_prefers_send_over_draft(monkeypatch):
    tools = [SimpleNamespace(name="GMAIL_SEND_EMAIL"), SimpleNamespace(name="GMAIL_CREATE_EMAIL_DRAFT")]
    crew = _post_crew_with_gmail_tools(monkeypatch, tools)

    selected = crew._get_send_tools()

    assert [t.name for t in selected] == ["GMAIL_SEND_EMAIL"]


def test_send_tools_falls_back_to_draft(monkeypatch):
    tools = [SimpleNamespace(name="GMAIL_CREATE_EMAIL_DRAFT")]
    crew = _post_crew_with_gmail_tools(monkeypatch, tools)

    selected = crew._get_send_tools()

    assert [t.name for t in selected] == ["GMAIL_CREATE_EMAIL_DRAFT"]
    assert crew.can_send() is True


def test_send_tools_empty_when_nothing_available(monkeypatch):
    crew = _post_crew_with_gmail_tools(monkeypatch, [])

    assert crew._get_send_tools() == []
    assert crew.can_send() is False


def test_send_tools_empty_when_composio_raises(monkeypatch):
    def boom(self):
        raise RuntimeError("composio down")

    monkeypatch.setattr("epic_news.config.composio_config.ComposioConfig.__init__", boom, raising=False)

    assert PostCrew()._get_send_tools() == []
