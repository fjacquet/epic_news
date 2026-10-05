"""send_email mails the short text body and attaches the DOCX; it never reads the report."""

from pathlib import Path

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow
from epic_news.utils.docx_report import build_docx

EXPECTED_BODY = "Please find the report for 'Plan a week in the Alps' attached."


def _flow(monkeypatch, output_file: str) -> ReceptionFlow:
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "true")
    f = ReceptionFlow("Plan a week in the Alps")
    f.state.sendto = "someone@example.com"
    f.state.selected_crew = "holiday_planner"
    f.state.user_request = "Plan a week in the Alps"
    f.state.output_file = output_file
    f.state.email_sent = False
    return f


def test_docx_is_attached_with_the_short_body_and_never_read(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # build_docx only writes under ./output/
    docx_path = tmp_path / "output" / "itinerary.docx"
    build_docx(
        fragments=[("Jour 1", "Arrivée à **Montreux**.")],
        meta={"title": "Carnet de voyage", "date": "2026-07-16"},
        output_path=str(docx_path),
    )
    flow = _flow(monkeypatch, str(docx_path))
    captured = {}
    monkeypatch.setattr(main_mod, "send_report_email", lambda **kw: captured.update(kw) or {"id": "abc"})

    def no_read(self, *a, **k):
        raise AssertionError("the report must not be read as text")

    monkeypatch.setattr(Path, "read_text", no_read)

    flow.send_email()

    assert flow.state.email_sent is True
    assert captured["html_body"] == EXPECTED_BODY
    assert captured["attachment_path"] == str(docx_path)


@pytest.mark.parametrize("name", ["gone.docx", ""])
def test_missing_docx_is_not_sent(tmp_path, monkeypatch, name):
    flow = _flow(monkeypatch, str(tmp_path / name) if name else "")
    sent = []
    monkeypatch.setattr(main_mod, "send_report_email", lambda **kw: sent.append(kw))

    flow.send_email()

    assert sent == []
    assert flow.state.email_sent is False
