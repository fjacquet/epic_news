import base64
import zipfile
from pathlib import Path

from docx import Document

from epic_news.utils.docx_report import build_docx, docx_builder

# 1x1 transparent PNG
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _all_text(path: str) -> str:
    """All visible text in a DOCX, including table cells (paragraphs miss those)."""
    doc = Document(path)
    chunks = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            chunks.extend(cell.text for cell in row.cells)
    return "\n".join(chunks)


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


def test_build_docx_applies_reference_doc(tmp_path: Path, monkeypatch):
    reference = tmp_path / "reference.docx"
    ref_doc = Document()
    ref_doc.styles["Normal"].font.name = "Reference Test Font"
    ref_doc.save(str(reference))
    monkeypatch.setattr(docx_builder, "_REFERENCE_DOC", reference)

    out = tmp_path / "styled.docx"
    build_docx([("Intro", "Texte.")], {"title": "Carnet"}, str(out))

    assert Document(str(out)).styles["Normal"].font.name == "Reference Test Font"


def test_build_docx_does_not_embed_local_files(tmp_path: Path, monkeypatch):
    """Untrusted markdown must not pull arbitrary local files into the DOCX."""
    secret = tmp_path / "secret.png"
    secret.write_bytes(_TINY_PNG)
    out = tmp_path / "guide.docx"

    build_docx(
        [("Intro", f"![leak]({secret.as_uri()})\n\n![hosts](file:///etc/hosts)\n\n![abs]({secret})")],
        {"title": "Carnet"},
        str(out),
    )

    with zipfile.ZipFile(out) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert media == []


def _media(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return [name for name in archive.namelist() if name.startswith("word/media/")]


def test_build_docx_embeds_images_inside_output(tmp_path: Path, monkeypatch):
    """Images our own code writes under output/ are still allowed."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output" / "charts").mkdir(parents=True)
    (tmp_path / "output" / "charts" / "c.png").write_bytes(_TINY_PNG)
    out = tmp_path / "output" / "guide.docx"

    build_docx(
        [("Intro", "![rel](output/charts/c.png)\n\n![abs](" + str(tmp_path / "output/charts/c.png") + ")")],
        {"title": "Carnet"},
        str(out),
    )

    assert len(_media(out)) >= 1


def test_build_docx_drops_traversal_and_remote_images(tmp_path: Path, monkeypatch):
    """`..` escapes, URLs and other schemes are dropped before pandoc fetches anything."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    (tmp_path / "secret.png").write_bytes(_TINY_PNG)
    out = tmp_path / "output" / "guide.docx"

    build_docx(
        [
            (
                "Intro",
                "![up](output/../secret.png)\n\n![net](http://127.0.0.1:9/x.png)\n\n"
                "![ref][r]\n\n[r]: file:///etc/hosts",
            )
        ],
        {"title": "Carnet"},
        str(out),
    )

    assert _media(out) == []
    assert "up" in _all_text(str(out))  # alt text kept


def test_build_docx_writer_pass_never_sees_forbidden_images(tmp_path: Path, monkeypatch):
    """pandoc 2.x fetches DOCX media before filters run, so forbidden images must
    already be gone from the AST handed to the DOCX writer pass."""
    monkeypatch.chdir(tmp_path)
    calls: list[tuple] = []
    real_convert = docx_builder.pypandoc.convert_text

    def spy(source, to, *args, **kwargs):
        calls.append((to, source))
        return real_convert(source, to, *args, **kwargs)

    monkeypatch.setattr(docx_builder.pypandoc, "convert_text", spy)
    build_docx(
        [("Intro", "![net](http://127.0.0.1:9/x.png) ![f](file:///etc/hosts) ![up](output/../s.png)")],
        {"title": "Carnet"},
        str(tmp_path / "output" / "guide.docx"),
    )

    docx_input = next(source for to, source in calls if to == "docx")
    assert "127.0.0.1" not in docx_input
    assert "/etc/hosts" not in docx_input
    assert "../s.png" not in docx_input


def test_build_docx_does_not_leak_image_root_into_metadata(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "output" / "guide.docx"
    build_docx([("Intro", "x")], {"title": "Carnet"}, str(out))

    with zipfile.ZipFile(out) as archive:
        blob = b"".join(archive.read(n) for n in archive.namelist() if n.startswith("docProps/"))
    assert str(tmp_path).encode() not in blob


def test_build_docx_survives_thematic_break_fences(tmp_path: Path):
    """LLM fragments use `---` separators; pandoc must not read them as YAML.

    Two `---` lines bracketing emphasized text (`*...*`) previously made pandoc's
    markdown reader parse the span as a YAML metadata block and die with exit 64
    (`while scanning an alias`). Body prose must never be treated as metadata.
    """
    out = tmp_path / "guide.docx"
    fragments = [
        (
            "Introduction",
            "Bienvenue.\n\n---\n*Note importante*\nTexte\n---\n\nFin.",
        ),
    ]
    result = build_docx(fragments, {"title": "Carnet", "date": "2026-07-16"}, str(out))

    assert result == str(out)
    assert out.exists() and out.stat().st_size > 0
    text = _all_text(str(out))
    assert "Note importante" in text
    assert "Fin." in text
