"""Regression coverage for commit 6c5da26 (fix(email): attach binary DOCX reports
instead of reading them as the body).

Before that fix, ``send_email`` read ``state.output_file`` as a UTF-8 email body and
only caught ``OSError``. A binary report (e.g. a DOCX holiday itinerary from
``docx_builder.build_docx``) raised an uncaught ``UnicodeDecodeError`` whenever
``EPIC_ENABLE_EMAIL`` was on, crashing the flow.

Two code paths in ``ReceptionFlow.send_email`` now guard against this, and each
needs its own binary fixture to actually exercise it:

1. ``.docx`` reports: ``prepare_email_params`` special-cases the ``.docx``
   extension and always returns ``output_file=None`` for the body source, so
   ``send_email`` takes its ``body_file is None`` ``else`` branch and never
   attempts to read the file at all.
2. Any other binary report (no matching ``.html`` sibling, extension not
   ``.docx``): ``resolve_report_html`` falls back to returning the file itself,
   so ``send_email`` *does* attempt ``Path(body_file).read_text(encoding="utf-8")``
   and must catch the resulting ``UnicodeDecodeError``.

Both scenarios must fall back to the short summary body and still attach and mail
the binary file without crashing.
"""

import pytest

import epic_news.main as main_mod
from epic_news.main import ReceptionFlow
from epic_news.utils.docx_report import build_docx

EXPECTED_SUMMARY_BODY = "Please find the report for 'Plan a week in the Alps' attached."


def _flow(monkeypatch, output_file: str) -> ReceptionFlow:
    monkeypatch.setenv("EPIC_ENABLE_EMAIL", "true")

    f = ReceptionFlow("Plan a week in the Alps")
    f.state.sendto = "someone@example.com"
    f.state.selected_crew = "holiday_planner"
    f.state.user_request = "Plan a week in the Alps"
    f.state.output_file = output_file
    f.state.email_sent = False
    return f


def test_docx_report_uses_summary_body_and_attaches_the_docx(tmp_path, monkeypatch):
    """The real-world case: a DOCX itinerary reaches send_email.

    prepare_email_params nulls the body source for any ``.docx`` output_file, so
    this exercises the ``body_file is None`` else branch in send_email.
    """
    docx_path = tmp_path / "itinerary.docx"
    build_docx(
        fragments=[("Jour 1", "Arrivée à **Montreux**.")],
        meta={"title": "Carnet de voyage", "date": "2026-07-16"},
        output_path=str(docx_path),
    )
    assert docx_path.exists() and docx_path.stat().st_size > 0

    flow = _flow(monkeypatch, str(docx_path))

    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return {"id": "abc"}

    monkeypatch.setattr(main_mod, "send_report_email", capture)

    flow.send_email()  # must not raise UnicodeDecodeError

    assert flow.state.email_sent is True
    assert captured["html_body"] == EXPECTED_SUMMARY_BODY
    assert captured["attachment_path"] == str(docx_path)


def test_non_docx_binary_report_triggers_unicode_decode_fallback(tmp_path, monkeypatch):
    """A binary report with no ``.docx`` extension and no ``.html`` sibling.

    resolve_report_html's generic fallback returns the file itself here (it isn't
    special-cased like ``.docx``), so send_email genuinely attempts to read it as
    UTF-8 and must catch the resulting UnicodeDecodeError.
    """
    binary_path = tmp_path / "report.bin"
    binary_path.write_bytes(b"\xff\xfe\x00\x01not valid utf-8 \x80\x81\x82")

    flow = _flow(monkeypatch, str(binary_path))

    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return {"id": "abc"}

    monkeypatch.setattr(main_mod, "send_report_email", capture)

    flow.send_email()  # must not raise UnicodeDecodeError

    assert flow.state.email_sent is True
    assert captured["html_body"] == EXPECTED_SUMMARY_BODY
    assert captured["attachment_path"] == str(binary_path)


@pytest.mark.parametrize("output_file_suffix", ["itinerary.docx", "report.bin"])
def test_binary_report_email_body_is_never_binary_bytes(tmp_path, monkeypatch, output_file_suffix):
    """Neither binary fallback path should ever leak raw bytes into the email body."""
    path = tmp_path / output_file_suffix
    if output_file_suffix.endswith(".docx"):
        build_docx(
            fragments=[("Intro", "Bienvenue.")],
            meta={"title": "Guide", "date": "2026-07-16"},
            output_path=str(path),
        )
    else:
        path.write_bytes(b"\x00\x01\x02\xff\xfe binary")

    flow = _flow(monkeypatch, str(path))

    captured = {}
    monkeypatch.setattr(main_mod, "send_report_email", lambda **kw: captured.update(kw) or {})

    flow.send_email()

    assert isinstance(captured["html_body"], str)
    assert "\x00" not in captured["html_body"]
    assert flow.state.email_sent is True
