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
    # LLM fragment bodies use `---` as section separators. Pandoc's markdown reader
    # otherwise treats a `---`-delimited span as a YAML metadata block, and emphasis
    # markers (`*`) inside it are read as YAML aliases → "Pandoc died with exitcode 64".
    # Disable the extension so every `---` stays a thematic break; the deterministic
    # `% title` block uses the independent pandoc_title_block extension and is unaffected.
    pypandoc.convert_text(
        markdown,
        to="docx",
        format="markdown-yaml_metadata_block",
        outputfile=output_path,
        extra_args=extra_args,
    )
    logger.info("📄 Holiday DOCX written to {}", output_path)
    return output_path
