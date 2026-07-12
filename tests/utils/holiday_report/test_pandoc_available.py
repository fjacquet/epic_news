from pathlib import Path

import pypandoc


def test_pandoc_markdown_to_docx(tmp_path: Path):
    out = tmp_path / "out.docx"
    pypandoc.convert_text(
        "# Title\n\nHello **world**.",
        to="docx",
        format="markdown",
        outputfile=str(out),
    )
    assert out.exists()
    assert out.stat().st_size > 0
