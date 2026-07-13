"""FINDAILY → DOCX: narrated summary + deterministic analysis/suggestion tables (exact figures)."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.docx_report.tables import md_table

_PERSONA = (
    "Tu es un analyste financier. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de chiffres inventés."
)


def assemble_fin_daily_docx(model: FinancialReport, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the FINDAILY report as a DOCX: narrated summary + deterministic tables."""
    llm = llm or LLMConfig.get_openrouter_llm()
    analyses_rows = [
        {"asset_class": a.asset_class, "summary": a.summary, "details": "; ".join(a.details)}
        for a in model.analyses
    ]
    suggestions_rows = [
        {"asset_class": s.asset_class, "suggestion": s.suggestion, "rationale": s.rationale}
        for s in model.suggestions
    ]
    sections = [
        Section(
            "Résumé exécutif",
            instruction="Reformule le résumé en prose fluide.",
            context=model.executive_summary or "",
        ),
        Section(
            "Analyses",
            body=md_table(
                analyses_rows,
                [("Classe d'actif", "asset_class"), ("Résumé", "summary"), ("Détails", "details")],
            ),
        ),
        Section(
            "Suggestions",
            body=md_table(
                suggestions_rows,
                [
                    ("Classe d'actif", "asset_class"),
                    ("Suggestion", "suggestion"),
                    ("Justification", "rationale"),
                ],
            ),
        ),
    ]
    meta = {
        "title": model.title or "Rapport financier",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
