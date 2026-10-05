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

    A report never carries placeholder or invented content:
    - a narrated section whose context is empty or blank is dropped before narration
      (the LLM would write it from nothing); an info line names it. Deterministic
      sections are kept as they are. If no section is left, raise ValueError.
    - if any narration degrades to a placeholder, raise RuntimeError before writing,
      so the run stops and the previous output is not overwritten.

    Narrated sections run in parallel (DOCX_FRAGMENT_CONCURRENCY, default 3); output keeps
    section order.
    """
    kept: list[Section] = []
    for section in sections:
        if section.body is None and not (section.context or "").strip():
            logger.info("Section '{}' dropped: no context to narrate from", section.heading)
            continue
        kept.append(section)
    if not kept:
        raise ValueError(
            f"no section left to write after dropping empty-context sections; refusing to write {output_path}"
        )

    def _render(section: Section) -> str:
        if section.body is not None:
            return section.body
        return generate_fragment(
            section.heading, section.instruction or "", section.context or "", llm, system
        )

    bodies = bounded_map(_render, kept, "DOCX_FRAGMENT_CONCURRENCY")
    fragments = [(s.heading, body) for s, body in zip(kept, bodies, strict=True)]
    narrated = [s for s in kept if s.body is None]
    degraded = [
        s.heading
        for s, body in zip(kept, bodies, strict=True)
        if s.body is None and body == placeholder_for(s.heading)
    ]

    if degraded:
        message = (
            f"{len(degraded)}/{len(narrated)} narrated sections degraded to a placeholder "
            f"({', '.join(degraded)}); refusing to write {output_path}"
        )
        logger.error("💥 {}", message)
        raise RuntimeError(message)

    return build_docx(fragments, meta, output_path)
