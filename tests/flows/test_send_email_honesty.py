"""send_email must never mark an email as sent when it wasn't.

A real run logged `PostResult: status=success` for an email that was never delivered:
Composio returned HTTP 401, the distributor agent ran with zero send tools, and the
LLM self-reported success. The flow then set email_sent=True regardless of outcome,
suppressing any retry.

A later run failed the opposite way: the agent *had* a working Gmail tool but replaced
the validated recipient with the literal placeholder "[EMAIL]", so Gmail rejected the
address. Delivery is now deterministic -- no LLM sits between the validated inputs and
the Gmail API -- and email_sent reflects only what the API confirmed.
"""

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow
from epic_news.utils.email_sender import EmailDeliveryError

BODY = "<html><body>report</body></html>"


@pytest.fixture
def flow(monkeypatch, tmp_path) -> ReceptionFlow:
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "true")
    report = tmp_path / "report.html"
    report.write_text(BODY, encoding="utf-8")

    f = ReceptionFlow("test request")
    f.state.sendto = "someone@example.com"
    f.state.output_file = str(report)
    f.state.email_sent = False
    return f


def test_email_marked_sent_only_on_confirmed_delivery(flow, monkeypatch):
    monkeypatch.setattr(main_mod, "send_report_email", lambda **_kw: {"id": "abc"})

    flow.send_email()

    assert flow.state.email_sent is True


def test_delivery_error_does_not_mark_sent(flow, monkeypatch):
    """The 401 / no-send-tool / rejected-recipient cases all surface here."""

    def boom(**_kw):
        raise EmailDeliveryError("Composio reported failure")

    monkeypatch.setattr(main_mod, "send_report_email", boom)

    flow.send_email()

    assert flow.state.email_sent is False, "claimed delivery after a delivery error"


def test_unexpected_exception_does_not_mark_sent(flow, monkeypatch):
    def boom(**_kw):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(main_mod, "send_report_email", boom)

    flow.send_email()

    assert flow.state.email_sent is False


def test_unreadable_report_does_not_mark_sent(flow, monkeypatch):
    flow.state.output_file = "/nonexistent/report.html"

    def fail(**_kw):  # pragma: no cover - must not be reached
        raise AssertionError("must not send when the body cannot be read")

    monkeypatch.setattr(main_mod, "send_report_email", fail)

    flow.send_email()

    assert flow.state.email_sent is False


def test_already_sent_is_skipped(flow, monkeypatch):
    flow.state.email_sent = True

    def fail(**_kw):  # pragma: no cover - must not be reached
        raise AssertionError("should not attempt a second send")

    monkeypatch.setattr(main_mod, "send_report_email", fail)

    flow.send_email()

    assert flow.state.email_sent is True


def test_disabled_by_env_does_not_send(flow, monkeypatch):
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "false")

    def fail(**_kw):  # pragma: no cover - must not be reached
        raise AssertionError("EPIC_ENABLE_EMAIL=false must not send")

    monkeypatch.setattr(main_mod, "send_report_email", fail)

    flow.send_email()


def test_the_real_report_html_is_the_body_and_attachment(flow, monkeypatch):
    """Regression: the flow used to mail raw JSON as the body and attach it too."""
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return {}

    monkeypatch.setattr(main_mod, "send_report_email", capture)

    flow.send_email()

    assert captured["html_body"] == BODY
    assert captured["recipient"] == "someone@example.com"
    assert str(captured["attachment_path"]).endswith("report.html")


def test_recipient_is_never_a_placeholder(flow, monkeypatch):
    """The model emitted "[EMAIL]"; the flow must pass the address it validated."""
    captured = {}
    monkeypatch.setattr(main_mod, "send_report_email", lambda **kw: captured.update(kw) or {})

    flow.send_email()

    assert "@" in captured["recipient"]
    assert "[" not in captured["recipient"]
