"""NEWSDAILY → DOCX: narrated summary + deterministic, union-aware region sections."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.news_daily_report import NewsDailyReport, NewsItem
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un rédacteur en chef. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)

_REGION_HEADINGS = [
    ("Suisse Romande", "suisse_romande"),
    ("Suisse", "suisse"),
    ("France", "france"),
    ("Europe", "europe"),
    ("Monde", "world"),
    ("Conflits", "wars"),
    ("Économie", "economy"),
]


def _region_body(value: list[NewsItem] | list[str] | str) -> str:
    if isinstance(value, str):
        return value.strip() or "_Aucune actualité._"
    if not value:  # empty list
        return "_Aucune actualité._"
    lines: list[str] = []
    for item in value:
        if isinstance(item, str):
            lines.append(f"- {item}")
        else:  # NewsItem
            text = item.titre
            if item.source:
                text += f" ({item.source})"
            if item.lien:
                text += f" — {item.lien}"
            lines.append(f"- {text}")
    return "\n".join(lines)


def _methodology_body(m: object) -> str | None:
    if not m:
        return None
    if isinstance(m, dict):
        return "\n".join(f"- **{k}** : {v}" for k, v in m.items())
    return str(m).strip()


def assemble_news_daily_docx(model: NewsDailyReport, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the NEWSDAILY report as a DOCX: narrated summary + deterministic region sections."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = []
    if model.summary:
        sections.append(
            Section(
                "Résumé",
                instruction="Reformule le résumé en prose fluide.",
                context=model.summary,
            )
        )
    for heading, field in _REGION_HEADINGS:
        sections.append(Section(heading, body=_region_body(getattr(model, field))))
    methodology_body = _methodology_body(model.methodology)
    if methodology_body is not None:
        sections.append(Section("Méthodologie", body=methodology_body))
    meta = {
        "title": inputs.get("topic") or "Revue de presse quotidienne",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
