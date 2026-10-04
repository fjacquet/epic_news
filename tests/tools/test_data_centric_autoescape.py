import json

from epic_news.tools.data_centric_tools import StructuredReportTool


def test_structured_report_html_escapes_untrusted_fields():
    payload = "<script>alert(1)</script>"
    result = json.loads(
        StructuredReportTool()._run(title=payload, description=payload, generate_html=True)
    )

    assert "error" not in result
    assert payload not in result["html"]
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in result["html"]
