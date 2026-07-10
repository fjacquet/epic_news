"""send_email must never mark an email as sent when it wasn't.

A real run logged `PostResult: status=success` for an email that was never delivered:
Composio returned HTTP 401, the distributor agent ran with zero send tools, and the
LLM self-reported success. The flow then set email_sent=True regardless of outcome,
suppressing any retry.
"""

from types import SimpleNamespace

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow


@pytest.fixture
def flow(monkeypatch, tmp_path) -> ReceptionFlow:
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "true")
    attachment = tmp_path / "report.html"
    attachment.write_text("<html></html>", encoding="utf-8")

    f = ReceptionFlow("test request")
    f.state.sendto = "someone@example.com"
    f.state.output_file = str(attachment)
    f.state.email_sent = False
    return f


def _stub_composio_available(monkeypatch):
    monkeypatch.setattr(main_mod, "CrewAIProvider", object, raising=False)


class _FakePostCrew:
    can_send_result = True
    kickoff_result: object = None

    def __init__(self):
        pass

    def can_send(self):
        return type(self).can_send_result


def test_email_not_marked_sent_when_no_send_tools(flow, monkeypatch):
    """The 401 case: no Gmail tool, so nothing can be delivered."""
    _FakePostCrew.can_send_result = False
    monkeypatch.setattr(main_mod, "PostCrew", _FakePostCrew)

    flow.send_email()

    assert flow.state.email_sent is False, "claimed delivery with no send tool"


def test_email_marked_sent_only_on_reported_success(flow, monkeypatch):
    _FakePostCrew.can_send_result = True
    monkeypatch.setattr(main_mod, "PostCrew", _FakePostCrew)
    result = SimpleNamespace(
        pydantic=SimpleNamespace(
            status="success",
            recipient_email="someone@example.com",
            subject="s",
            attachment_sent=True,
        )
    )
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda crew, inputs: result)

    flow.send_email()

    assert flow.state.email_sent is True


def test_reported_failure_does_not_mark_sent(flow, monkeypatch):
    _FakePostCrew.can_send_result = True
    monkeypatch.setattr(main_mod, "PostCrew", _FakePostCrew)
    result = SimpleNamespace(
        pydantic=SimpleNamespace(
            status="failure", recipient_email="someone@example.com", error_message="smtp down"
        )
    )
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda crew, inputs: result)

    flow.send_email()

    assert flow.state.email_sent is False


def test_missing_structured_output_does_not_mark_sent(flow, monkeypatch):
    _FakePostCrew.can_send_result = True
    monkeypatch.setattr(main_mod, "PostCrew", _FakePostCrew)
    monkeypatch.setattr(
        main_mod, "kickoff_flow", lambda crew, inputs: SimpleNamespace(pydantic=None, raw="blah")
    )

    flow.send_email()

    assert flow.state.email_sent is False


def test_kickoff_exception_does_not_mark_sent(flow, monkeypatch):
    _FakePostCrew.can_send_result = True
    monkeypatch.setattr(main_mod, "PostCrew", _FakePostCrew)

    def boom(crew, inputs):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(main_mod, "kickoff_flow", boom)

    flow.send_email()

    assert flow.state.email_sent is False


def test_already_sent_is_skipped(flow, monkeypatch):
    flow.state.email_sent = True

    def fail(*_a, **_k):  # pragma: no cover - must not be reached
        raise AssertionError("should not attempt a second send")

    monkeypatch.setattr(main_mod, "PostCrew", fail)

    flow.send_email()

    assert flow.state.email_sent is True
