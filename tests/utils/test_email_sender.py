"""The deterministic Gmail sender must refuse bad input and never fake success.

Every guard here corresponds to a way the previous, agent-driven send actually failed
in production:

* the model passed the placeholder "[EMAIL]" as the recipient -> Gmail 400;
* it passed a *local path* as ``attachment``, which Composio reads as an already
  uploaded S3 key -> 404;
* a tool-less agent reported ``status="success"`` for a run it never sent.

``tools.execute`` also returns a plain ``dict``. ``getattr(response, "successful")``
silently yields ``None``, which would turn every real delivery into a reported
failure -- so the success check must use item access.
"""

from pathlib import Path
from typing import Any

import pytest

from epic_news.utils import email_sender
from epic_news.utils.email_sender import (
    GMAIL_SEND_EMAIL,
    EmailDeliveryError,
    send_report_email,
)


class FakeTools:
    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def execute(self, slug: str, arguments: dict, **kwargs):
        self.calls.append({"slug": slug, "arguments": arguments, **kwargs})
        return self.response


class FakeClient:
    def __init__(self, response: dict[str, Any]):
        self.tools = FakeTools(response)


def _ok() -> FakeClient:
    return FakeClient({"successful": True, "error": None, "data": {"id": "msg-1"}})


@pytest.fixture
def report(tmp_path) -> Path:
    f = tmp_path / "report.html"
    f.write_text("<html>hi</html>", encoding="utf-8")
    return f


def test_sends_html_with_expected_arguments():
    client = _ok()

    data = send_report_email(recipient="a@b.com", subject="Subject", html_body="<p>x</p>", client=client)

    assert data == {"id": "msg-1"}
    call = client.tools.calls[0]
    assert call["slug"] == GMAIL_SEND_EMAIL
    assert call["arguments"]["recipient_email"] == "a@b.com"
    assert call["arguments"]["is_html"] is True
    assert "attachment" not in call["arguments"], "no attachment must send no attachment key"


def test_manual_execution_pins_a_toolkit_version():
    """Without an explicit version the SDK raises ToolVersionRequiredError."""
    client = _ok()

    send_report_email(recipient="a@b.com", subject="s", html_body="x", client=client)

    assert client.tools.calls[0]["version"], "version must be passed to tools.execute"


@pytest.mark.parametrize("bad", ["[EMAIL]", "", "plainuser", "me"])
def test_rejects_recipients_without_a_domain(bad):
    """The exact string the model substituted, plus its neighbours."""
    client = _ok()

    with pytest.raises(EmailDeliveryError, match="not a valid email"):
        send_report_email(recipient=bad, subject="s", html_body="x", client=client)

    assert not client.tools.calls, "must not call Gmail with a bad recipient"


@pytest.mark.parametrize("empty", ["", "   ", "\n"])
def test_rejects_empty_body(empty):
    client = _ok()

    with pytest.raises(EmailDeliveryError, match="empty report body"):
        send_report_email(recipient="a@b.com", subject="s", html_body=empty, client=client)

    assert not client.tools.calls


def test_rejects_missing_attachment(tmp_path):
    client = _ok()

    with pytest.raises(EmailDeliveryError, match="Attachment does not exist"):
        send_report_email(
            recipient="a@b.com",
            subject="s",
            html_body="x",
            attachment_path=tmp_path / "gone.html",
            client=client,
        )

    assert not client.tools.calls


def test_attachment_is_passed_as_an_absolute_path(report):
    """Composio auto-uploads a local path only when it resolves inside the allowlist."""
    client = _ok()

    send_report_email(recipient="a@b.com", subject="s", html_body="x", attachment_path=report, client=client)

    sent = client.tools.calls[0]["arguments"]["attachment"]
    assert Path(sent).is_absolute()
    assert Path(sent) == report.resolve()


def test_failure_response_raises():
    client = FakeClient({"successful": False, "error": "Invalid email format", "data": {}})

    with pytest.raises(EmailDeliveryError, match="Invalid email format"):
        send_report_email(recipient="a@b.com", subject="s", html_body="x", client=client)


def test_failure_without_error_message_still_raises():
    client = FakeClient({"successful": False, "error": None, "data": {}})

    with pytest.raises(EmailDeliveryError, match="without an error"):
        send_report_email(recipient="a@b.com", subject="s", html_body="x", client=client)


def test_success_is_read_by_item_access_not_getattr():
    """A dict has no ``.successful`` attribute; getattr would yield None -> false failure."""
    response = {"successful": True, "error": None, "data": {}}
    assert getattr(response, "successful", None) is None  # the trap

    send_report_email(recipient="a@b.com", subject="s", html_body="x", client=FakeClient(response))


def test_build_client_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)

    with pytest.raises(EmailDeliveryError, match="COMPOSIO_API_KEY"):
        email_sender.build_client()


def test_build_client_confines_uploads_to_the_output_dir(monkeypatch, tmp_path):
    """Auto-upload must never be able to read outside our generated reports."""
    captured = {}
    monkeypatch.setenv("COMPOSIO_API_KEY", "test-key-not-real")
    monkeypatch.setenv("EPIC_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(email_sender, "Composio", lambda **kw: captured.update(kw) or object())

    email_sender.build_client()

    assert captured["dangerously_allow_auto_upload_download_files"] is True
    assert captured["file_upload_dirs"] == [str(tmp_path.resolve())]
