"""Turn a list of Section specs into a DOCX, narrating or passing through per section."""

from typing import Any

from loguru import logger

from epic_news.utils.docx_report.docx_builder import build_docx
from epic_news.utils.docx_report.fragments import generate_fragment, placeholder_for
from epic_news.utils.docx_report.sections import Section


def assemble_fragments(
    sections: list[Section], meta: dict[str, str], output_path: str, llm: Any, system: str
) -> str:
    """Render each Section (deterministic body verbatim, else LLM-narrated) → DOCX.

    A single failed narration degrades to a placeholder, but a report whose majority is
    placeholders is not a report: it would silently overwrite the previous, good output
    with an empty shell. In that case abort before writing anything.
    """
    fragments: list[tuple[str, str]] = []
    placeholders = 0
    for s in sections:
        if s.body is not None:
            fragments.append((s.heading, s.body))
            continue
        fragment = generate_fragment(s.heading, s.instruction or "", s.context or "", llm, system)
        placeholders += fragment == placeholder_for(s.heading)
        fragments.append((s.heading, fragment))

    if placeholders * 2 > len(sections):
        logger.error(
            "💥 {}/{} sections degraded to a placeholder; refusing to write {}",
            placeholders,
            len(sections),
            output_path,
        )
        raise RuntimeError(
            f"{placeholders}/{len(sections)} sections degraded to a placeholder; "
            f"refusing to write {output_path}"
        )

    return build_docx(fragments, meta, output_path)
