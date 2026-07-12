"""Deterministic assembly of Markdown fragments into a single DOCX via Pandoc."""

from pathlib import Path

import pypandoc
from loguru import logger


def build_docx(fragments: list[tuple[str, str]], meta: dict[str, str], output_path: str) -> str:
    """Assemble ordered (heading, markdown_body) fragments into a DOCX with a TOC.

    Each fragment becomes a top-level (H1) section. Deterministic: no LLM, no network.
    """
    title = meta.get("title", "Guide")
    date = meta.get("date", "")

    parts: list[str] = [f"% {title}", f"% {meta.get('author', '')}", f"% {date}", ""]
    for heading, body in fragments:
        parts.append(f"# {heading}\n")
        parts.append(body.strip() + "\n")
    markdown = "\n".join(parts)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    extra_args = ["--toc", "--standalone"]
    pypandoc.convert_text(
        markdown, to="docx", format="markdown", outputfile=output_path, extra_args=extra_args
    )
    logger.info("📄 Holiday DOCX written to {}", output_path)
    return output_path
