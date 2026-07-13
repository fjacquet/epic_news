"""PESTEL → DOCX: fully narrated strategic analysis prose.

Consumes the flow's ``PestelReport`` (``models/crews/pestel_report.py``) — the model
``ReceptionFlow.generate_pestel`` produces. Every section is narrated (fed to the LLM);
there is no deterministic verbatim section in this report.
"""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.pestel_report import PestelDimension, PestelReport
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un analyste stratégique. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."
)

_DIMENSIONS: list[tuple[str, str]] = [
    ("Politique", "political"),
    ("Économique", "economic"),
    ("Social", "social"),
    ("Technologique", "technological"),
    ("Environnemental", "environmental"),
    ("Légal", "legal"),
]


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def _dimension_context(d: PestelDimension) -> str:
    return f"{d.summary}\n\n{d.impact_analysis}\n\nFacteurs clés :\n" + _bullets(d.key_factors)


def assemble_pestel_docx(model: PestelReport, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the PESTEL report as a DOCX: fully narrated strategic analysis prose."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = [
        Section(
            "Résumé exécutif",
            instruction="Reformule le résumé en prose fluide.",
            context=model.executive_summary or "",
        )
    ]
    for heading, field_name in _DIMENSIONS:
        dimension: PestelDimension = getattr(model, field_name)
        sections.append(
            Section(
                heading,
                instruction="Développe cette dimension en prose analytique.",
                context=_dimension_context(dimension),
            )
        )
    sections.append(
        Section(
            "Synthèse",
            instruction="Développe la synthèse en prose analytique.",
            context=model.synthesis or "",
        )
    )
    meta = {
        "title": model.topic or "Analyse PESTEL",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
