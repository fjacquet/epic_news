"""BOOK_SUMMARY → DOCX: narrated prose + deterministic lists (TOC, chapters, references)."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un critique littéraire. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."
)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Vide._"


def assemble_book_summary_docx(
    model: BookSummaryReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the BOOK_SUMMARY report as a DOCX: narrated prose + deterministic lists."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = []
    if model.summary:
        sections.append(
            Section("Résumé", instruction="Reformule le résumé en prose fluide.", context=model.summary)
        )
    sections.append(
        Section(
            "Table des matières",
            body=_bullets([entry.title for entry in model.table_of_contents]),
        )
    )
    for s in model.sections:
        sections.append(Section(s.title, instruction="Développe cette section en prose.", context=s.content))
    if model.chapter_summaries:
        sections.append(
            Section(
                "Résumés de chapitres",
                body=_bullets([f"Ch{c.chapter} — {c.title} : {c.focus}" for c in model.chapter_summaries]),
            )
        )
    sections.append(Section("Références", body=_bullets(model.references)))
    meta = {
        "title": model.title or "Résumé de livre",
        "date": inputs.get("current_date", ""),
        "author": model.author or "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
