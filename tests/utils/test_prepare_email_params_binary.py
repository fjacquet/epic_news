"""A binary DOCX report must be attached, never routed into the HTML email body.

Task 7 wired `generate_holiday_plan` to set `state.output_file =
"output/holiday/itinerary.docx"`. `send_email` reads `output_file` as the UTF-8 email
body, so a binary DOCX reaching that path raises `UnicodeDecodeError`. `prepare_email_params`
must instead attach the DOCX and leave the HTML-body source empty so `send_email` falls
back to the short summary body.
"""

from types import SimpleNamespace

from epic_news.utils.report_utils import prepare_email_params


def _state(output_file: str) -> SimpleNamespace:
    return SimpleNamespace(
        sendto="dev@example.com",
        selected_crew="HOLIDAY_PLANNER",
        user_request="road trip",
        output_file=output_file,
    )


def test_docx_report_is_attached_not_used_as_body():
    params = prepare_email_params(_state("output/holiday/itinerary.docx"))
    assert params["attachment_path"] == "output/holiday/itinerary.docx"
    # body source must NOT be the binary file (send_email would read it as text and crash)
    assert params["output_file"] != "output/holiday/itinerary.docx"
    assert params["output_file"] in (None, "")
    assert params["body"]  # a non-empty short summary body exists


def test_non_docx_report_behaviour_unchanged(tmp_path):
    # A .html report still routes through resolve_report_html for both body and
    # attachment. resolve_report_html checks the filesystem, so use a real file
    # (mirrors tests/utils/test_report_html_resolution.py) rather than a dangling
    # path -- otherwise resolve_report_html legitimately returns None for both
    # branches and the equality below would be trivially true for the wrong reason.
    html = tmp_path / "report.html"
    html.write_text("<html></html>", encoding="utf-8")

    params = prepare_email_params(_state(str(html)))
    assert params["attachment_path"] == params["output_file"] == str(html)
