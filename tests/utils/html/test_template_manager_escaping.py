from epic_news.utils.html.template_manager import TemplateManager

PAYLOAD = "<script>alert(1)</script>"


def test_report_title_is_escaped():
    html = TemplateManager().render_report("POEM", {"poem_title": PAYLOAD, "poem": "x"})

    assert PAYLOAD not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_error_fallback_escapes_exception_and_content(monkeypatch):
    manager = TemplateManager()

    def boom(_name="universal_report_template.html"):
        raise RuntimeError(PAYLOAD)

    monkeypatch.setattr(manager, "load_template", boom)
    html = manager.render_report("POEM", {"poem_title": "<img src=x onerror=alert(2)>"})

    assert PAYLOAD not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html
