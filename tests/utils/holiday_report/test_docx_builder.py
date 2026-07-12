from pathlib import Path

from docx import Document

from epic_news.utils.holiday_report.docx_builder import build_docx


def test_build_docx_writes_headings_and_body(tmp_path: Path):
    out = tmp_path / "guide.docx"
    fragments = [
        ("Introduction", "Bienvenue à **Montreux**."),
        ("Jour 1", "- Départ\n- Route"),
    ]
    result = build_docx(fragments, {"title": "Carnet", "date": "2026-07-16"}, str(out))

    assert result == str(out)
    assert out.exists() and out.stat().st_size > 0
    text = "\n".join(p.text for p in Document(str(out)).paragraphs)
    assert "Introduction" in text
    assert "Jour 1" in text
    assert "Montreux" in text
