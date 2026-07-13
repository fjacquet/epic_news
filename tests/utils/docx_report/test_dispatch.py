from types import SimpleNamespace

from epic_news.utils.docx_report.dispatch import emit_report


def _state(fmt=None):
    return SimpleNamespace(output_format=fmt, output_file="")


def test_html_default_calls_render(monkeypatch):
    monkeypatch.delenv("OUTPUT_FORMAT", raising=False)
    st = _state(None)
    called = {}

    def render():
        called["html"] = True
        return "out/x.html"

    out = emit_report(st, "SAINT", render, assemble_docx=lambda: "out/x.docx")
    assert called.get("html") and out == "out/x.html" and st.output_file == "out/x.html"


def test_docx_requested_runs_assembler(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    st = _state(None)
    out = emit_report(st, "SAINT", lambda: "out/x.html", assemble_docx=lambda: "out/x.docx")
    assert out == "out/x.docx" and st.output_file == "out/x.docx"


def test_docx_requested_no_assembler_falls_back(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    st = _state(None)
    out = emit_report(st, "SAINT", lambda: "out/x.html", assemble_docx=None)
    assert out == "out/x.html" and st.output_file == "out/x.html"
