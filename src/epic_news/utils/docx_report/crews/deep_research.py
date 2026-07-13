"""DEEPRESEARCH → DOCX: narrated prose + deterministic findings/sources."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un analyste de recherche. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."
)
_MAX_SECTIONS = 20


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def assemble_deep_research_docx(
    model: DeepResearchReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = [
        Section(
            "Résumé exécutif",
            instruction="Reformule le résumé en prose fluide.",
            context=model.executive_summary or "",
        ),
        Section("Principales conclusions", body=_bullets(list(model.key_findings or []))),
    ]
    for rs in (model.research_sections or [])[:_MAX_SECTIONS]:
        sections.append(
            Section(
                rs.section_title,
                instruction="Développe cette section en prose détaillée.",
                context=rs.content or "",
            )
        )
    sections.append(
        Section("Méthodologie", instruction="Décris la méthodologie.", context=model.methodology or "")
    )
    sections.append(
        Section(
            "Sources", body=f"{model.sources_count} sources — niveau de confiance : {model.confidence_level}."
        )
    )
    meta = {
        "title": model.title or model.topic or "Recherche",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
