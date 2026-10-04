"""Deterministic assembly of Markdown fragments into a single DOCX via Pandoc."""

from pathlib import Path

import pypandoc
from loguru import logger

_REFERENCE_DOC = Path(__file__).parent / "reference.docx"
_SAFE_IMAGES_FILTER = Path(__file__).parent / "safe_images.lua"


def build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str:
    """Assemble ordered (heading, markdown_body) fragments into a DOCX with a TOC.

    Each fragment becomes a top-level (H1) section. Deterministic: no LLM, no network.
    """
    title = meta.get("title", "Rapport")
    date = meta.get("date", "")
    parts: list[str] = [f"% {title}", f"% {meta.get('author', 'Epic News')}", f"% {date}", ""]
    for heading, body in fragments:
        parts.append(f"# {heading}\n")
        parts.append((body or "").strip() + "\n")
    markdown = "\n".join(parts)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # Fragments are LLM output: pass 1 (markdown -> JSON, no resource fetching) drops
    # every image outside output/; pass 2 writes the DOCX from the cleaned AST, so
    # pandoc only ever fetches allowed images. Two passes because pandoc 2.x fetches
    # DOCX media before running filters. (--sandbox is not an option: distro pandoc
    # builds cannot write DOCX under it.)
    # LLM fragment bodies use `---` as separators. Disable yaml_metadata_block so every
    # `---` stays a thematic break (otherwise Pandoc dies with exitcode 64).
    cleaned = pypandoc.convert_text(
        markdown,
        to="json",
        format="markdown-yaml_metadata_block",
        extra_args=[
            "--lua-filter",
            str(_SAFE_IMAGES_FILTER),
            "--metadata",
            f"epic_image_root={Path('output').resolve()}",
        ],
    )
    extra_args = ["--toc", "--standalone"]
    if _REFERENCE_DOC.exists():
        extra_args += ["--reference-doc", str(_REFERENCE_DOC)]
    pypandoc.convert_text(
        cleaned,
        to="docx",
        format="json",
        outputfile=output_path,
        extra_args=extra_args,
    )
    logger.info("📄 DOCX written to {}", output_path)
    return output_path
