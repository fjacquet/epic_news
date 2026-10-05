import pytest

from epic_news.utils.docx_report.docx_builder import build_docx


def test_build_docx_refuses_paths_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="output/"):
        build_docx([("Intro", "text")], {"title": "T"}, "../evil.docx")
