"""The bundled reference.docx drives fonts, A4 page, palette and table look of every DOCX."""

import re
import zipfile
from pathlib import Path

import pytest

from epic_news.utils.docx_report.docx_builder import build_docx

_MARKDOWN = (
    "Intro paragraph.\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n\n- item one\n- item two\n\n```\ncode\n```\n"
)


@pytest.fixture(scope="module")
def docx_parts(tmp_path_factory) -> dict[str, str]:
    out = Path(tmp_path_factory.mktemp("docx")) / "report.docx"
    build_docx([("Section", _MARKDOWN)], {"title": "Titre", "date": "2026-10-04"}, str(out))
    with zipfile.ZipFile(out) as zf:
        return {name: zf.read(name).decode("utf-8") for name in zf.namelist() if name.endswith(".xml")}


def _style(styles: str, style_id: str) -> str:
    match = re.search(rf'<w:style [^>]*w:styleId="{style_id}".*?</w:style>', styles, re.S)
    assert match, f"style {style_id} missing"
    return match.group(0)


def test_body_font_is_segoe_ui_light_10pt(docx_parts):
    defaults = re.search(r"<w:docDefaults>.*?</w:docDefaults>", docx_parts["word/styles.xml"], re.S)
    assert defaults
    assert 'w:ascii="Segoe UI Light"' in defaults.group(0)
    assert '<w:sz w:val="20"' in defaults.group(0)
    assert 'w:val="fr-CH"' in defaults.group(0)


def test_page_is_a4_with_footer_page_numbers(docx_parts):
    document = docx_parts["word/document.xml"]
    assert 'w:w="11906"' in document
    assert 'w:h="16838"' in document
    footers = [text for name, text in docx_parts.items() if name.startswith("word/footer")]
    assert footers, "no footer part"
    assert any("PAGE" in text and "NUMPAGES" in text for text in footers)


def test_headings_use_theme_palette(docx_parts):
    styles = docx_parts["word/styles.xml"]
    assert 'w:val="0056B3"' in _style(styles, "Heading1")
    assert 'w:val="2980B9"' in _style(styles, "Heading2")
    assert 'w:val="2C3E50"' in _style(styles, "Heading3")


def test_table_header_row_is_shaded(docx_parts):
    table = _style(docx_parts["word/styles.xml"], "Table")
    first_row = re.search(r'<w:tblStylePr w:type="firstRow">.*?</w:tblStylePr>', table, re.S)
    assert first_row
    assert 'w:fill="0056B3"' in first_row.group(0)


def test_only_code_blocks_are_monospace(docx_parts):
    styles = docx_parts["word/styles.xml"]
    assert "Consolas" in _style(styles, "SourceCode")
    # inline `code` must keep the body font (LLMs backtick transport names, brands...)
    assert "Consolas" not in _style(styles, "VerbatimChar")
