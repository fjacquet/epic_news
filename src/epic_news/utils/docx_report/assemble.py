"""Turn a list of Section specs into a DOCX, narrating or passing through per section."""

from typing import Any

from loguru import logger

from epic_news.utils.concurrency import bounded_map
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

    Narrated sections run in parallel (DOCX_FRAGMENT_CONCURRENCY, default 3); output keeps
    section order.
    """

    def _render(section: Section) -> str:
        if section.body is not None:
            return section.body
        return generate_fragment(
            section.heading, section.instruction or "", section.context or "", llm, system
        )

    bodies = bounded_map(_render, sections, "DOCX_FRAGMENT_CONCURRENCY")
    fragments = [(s.heading, body) for s, body in zip(sections, bodies, strict=True)]
    placeholders = sum(
        1
        for s, body in zip(sections, bodies, strict=True)
        if s.body is None and body == placeholder_for(s.heading)
    )

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
