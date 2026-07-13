"""COMPANY_NEWS → DOCX: narrated summary + deterministic per-section article bullets."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.company_news_report import ArticleItem, CompanyNewsReport
from epic_news.models.crews.company_news_report import Section as CompanyNewsSection
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un analyste d'actualité d'entreprise. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)


def _articles_body(articles: list[ArticleItem]) -> str:
    if not articles:
        return "_Aucun article._"
    return "\n".join(f"- {a.article} ({a.source}, {a.date}) — {a.citation}" for a in articles)


def assemble_company_news_docx(
    model: CompanyNewsReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the COMPANY_NEWS report as a DOCX: narrated summary + deterministic article bullets."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = [
        Section(
            "Résumé",
            instruction="Reformule le résumé en prose fluide.",
            context=model.summary,
        )
    ]
    news_sections: list[CompanyNewsSection] = model.sections
    for sec in news_sections:
        sections.append(Section(sec.titre, body=_articles_body(sec.contenu)))
    if model.notes:
        sections.append(
            Section("Notes", instruction="Reformule les notes en prose fluide.", context=model.notes)
        )
    meta = {
        "title": inputs.get("company") or inputs.get("topic") or "Actualités entreprise",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
