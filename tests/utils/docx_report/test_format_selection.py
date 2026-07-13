from types import SimpleNamespace

import pytest

from epic_news.utils.docx_report.format_selection import parse_output_format, resolve_output_format


@pytest.mark.parametrize(
    "req",
    [
        "génère le rapport en DOCX",
        "give me a Word document",
        "je veux un fichier Word",
        "export as docx",
        "format docx s'il te plaît",
    ],
)
def test_parse_detects_docx(req):
    assert parse_output_format(req) == "docx"


@pytest.mark.parametrize("req", ["get the daily news report", "fais un rapport PESTEL", "", None])
def test_parse_defaults_none(req):
    assert parse_output_format(req) is None


def test_resolve_flag_wins(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "docx")
    assert resolve_output_format(SimpleNamespace(output_format="html")) == "docx"


def test_resolve_parsed_then_default(monkeypatch):
    monkeypatch.delenv("OUTPUT_FORMAT", raising=False)
    assert resolve_output_format(SimpleNamespace(output_format="docx")) == "docx"
    assert resolve_output_format(SimpleNamespace(output_format=None)) == "html"


def test_resolve_ignores_invalid_flag(monkeypatch):
    monkeypatch.setenv("OUTPUT_FORMAT", "pdf")
    assert resolve_output_format(SimpleNamespace(output_format=None)) == "html"
