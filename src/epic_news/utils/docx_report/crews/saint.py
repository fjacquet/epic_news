"""SAINT → DOCX: narrated prose + deterministic sources."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.utils.docx_report import Section, assemble_fragments

_PERSONA = (
    "Tu es un hagiographe. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre (titres niveau 2+, listes, gras). Pas de HTML, pas de JSON, pas de préambule."
)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def assemble_saint_docx(model: SaintData, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the SAINT report as a DOCX: narrated prose + deterministic sources."""
    llm = llm or LLMConfig.get_openrouter_llm()
    sections: list[Section] = [
        Section(
            "Biographie",
            instruction="Rédige la biographie en prose fluide.",
            context=model.biography or "",
        ),
        Section(
            "Signification",
            instruction="Développe la signification en prose fluide.",
            context=model.significance or "",
        ),
        Section(
            "Miracles",
            instruction="Décris les miracles en prose fluide.",
            context=model.miracles or "",
        ),
        Section(
            "Lien avec la Suisse",
            instruction="Développe le lien avec la Suisse en prose fluide.",
            context=model.swiss_connection or "",
        ),
        Section(
            "Prière & Réflexion",
            instruction="Rédige la prière et la réflexion en prose fluide.",
            context=model.prayer_reflection or "",
        ),
        Section("Sources", body=_bullets(model.sources)),
    ]
    meta = {
        "title": model.saint_name or "Saint du jour",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
