"""Turn a list of Section specs into a DOCX, narrating or passing through per section."""

from typing import Any

from epic_news.utils.docx_report.docx_builder import build_docx
from epic_news.utils.docx_report.fragments import generate_fragment
from epic_news.utils.docx_report.sections import Section


def assemble_fragments(
    sections: list[Section], meta: dict[str, str], output_path: str, llm: Any, system: str
) -> str:
    """Render each Section (deterministic body verbatim, else LLM-narrated) → DOCX."""
    fragments: list[tuple[str, str]] = []
    for s in sections:
        if s.body is not None:
            fragments.append((s.heading, s.body))
        else:
            fragments.append(
                (s.heading, generate_fragment(s.heading, s.instruction or "", s.context or "", llm, system))
            )
    return build_docx(fragments, meta, output_path)
