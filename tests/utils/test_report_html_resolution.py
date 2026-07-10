"""The email body must be the rendered HTML report, never the crew's raw JSON.

`state.output_file` is the crew's *write target* (`report.json`). Crews render
`report.html` beside it but never update the state, so the email step used to mail
raw JSON as the body -- the agent duly reported `html_preserved: false` -- and attach
that same JSON file.
"""

from epic_news.utils.report_utils import prepare_email_params, resolve_report_html


class _State:
    selected_crew = "DEEPRESEARCH"
    user_request = "topic"
    sendto = "someone@example.com"

    def __init__(self, output_file: str):
        self.output_file = output_file


def test_prefers_the_html_sibling_of_a_json_target(tmp_path):
    (tmp_path / "report.json").write_text("{}", encoding="utf-8")
    html = tmp_path / "report.html"
    html.write_text("<html></html>", encoding="utf-8")

    assert resolve_report_html(str(tmp_path / "report.json")) == str(html)


def test_returns_html_target_unchanged(tmp_path):
    html = tmp_path / "report.html"
    html.write_text("<html></html>", encoding="utf-8")

    assert resolve_report_html(str(html)) == str(html)


def test_falls_back_to_the_json_when_no_html_was_rendered(tmp_path):
    json_file = tmp_path / "report.json"
    json_file.write_text("{}", encoding="utf-8")

    assert resolve_report_html(str(json_file)) == str(json_file)


def test_missing_html_target_returns_none(tmp_path):
    assert resolve_report_html(str(tmp_path / "gone.html")) is None


def test_missing_everything_returns_none(tmp_path):
    assert resolve_report_html(str(tmp_path / "gone.json")) is None


def test_blank_and_non_string_inputs_return_none():
    assert resolve_report_html("") is None
    assert resolve_report_html("   ") is None
    assert resolve_report_html(None) is None


def test_email_params_body_and_attachment_are_the_html_report(tmp_path):
    (tmp_path / "report.json").write_text('{"a": 1}', encoding="utf-8")
    html = tmp_path / "report.html"
    html.write_text("<html></html>", encoding="utf-8")

    params = prepare_email_params(_State(str(tmp_path / "report.json")))

    assert params["output_file"] == str(html), "body must be the HTML report"
    assert params["attachment_path"] == str(html), "attachment must be the HTML report"
    assert not params["output_file"].endswith(".json")
