"""SALES_PROSPECTING → DOCX: narrated overview/strategy/insights + deterministic contacts table."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.docx_report.tables import md_table

_PERSONA = (
    "Tu es un consultant commercial. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)


def assemble_sales_prospecting_docx(
    model: SalesProspectingReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the SALES_PROSPECTING report as a DOCX: narrated sections + deterministic contacts table."""
    llm = llm or LLMConfig.get_openrouter_llm()
    contacts_rows = [
        {
            "name": c.name,
            "role": c.role,
            "department": c.department,
            "contact_info": c.contact_info,
        }
        for c in model.key_contacts
    ]
    sections = [
        Section(
            "Aperçu de l'entreprise",
            instruction="Reformule l'aperçu de l'entreprise en prose fluide.",
            context=model.company_overview,
        ),
        Section(
            "Contacts clés",
            body=md_table(
                contacts_rows,
                [
                    ("Nom", "name"),
                    ("Rôle", "role"),
                    ("Département", "department"),
                    ("Coordonnées", "contact_info"),
                ],
            ),
        ),
        Section(
            "Stratégie d'approche",
            instruction="Reformule la stratégie d'approche en prose fluide.",
            context=model.approach_strategy,
        ),
        Section(
            "Informations complémentaires",
            instruction="Reformule les informations complémentaires en prose fluide.",
            context=model.remaining_information,
        ),
    ]
    meta = {
        "title": inputs.get("company") or inputs.get("topic") or "Prospection commerciale",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
