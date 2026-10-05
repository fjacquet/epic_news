from types import SimpleNamespace

import pytest

from epic_news.utils.docx_report.dispatch import emit_report


def test_emit_report_sets_output_file_to_the_docx():
    state = SimpleNamespace(output_file=None)
    assert emit_report(state, lambda: "output/x/report.docx") == "output/x/report.docx"
    assert state.output_file == "output/x/report.docx"


def test_emit_report_propagates_assembler_errors():
    state = SimpleNamespace(output_file="before")
    with pytest.raises(RuntimeError):
        emit_report(state, lambda: (_ for _ in ()).throw(RuntimeError("pandoc failed")))
    assert state.output_file == "before"
