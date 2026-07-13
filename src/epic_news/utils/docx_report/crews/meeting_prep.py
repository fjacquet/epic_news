"""MEETING_PREP → DOCX: narrated summary/overview + deterministic profile/table/lists."""

from typing import Any

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.docx_report.tables import md_table

_PERSONA = (
    "Tu es un conseiller d'affaires. Rédige UNIQUEMENT la section demandée, en français, "
    "en Markdown propre. Pas de HTML, pas de JSON, pas de préambule."
)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "_Aucune._"


def assemble_meeting_prep_docx(
    model: MeetingPrepReport, inputs: dict, output_path: str, llm: Any = None
) -> str:
    """Build the MEETING_PREP report as a DOCX: narrated summary/overview + deterministic rest."""
    llm = llm or LLMConfig.get_openrouter_llm()

    cp = model.company_profile
    profile_body = (
        f"**Nom :** {cp.name}\n\n"
        f"**Secteur :** {cp.industry}\n\n"
        f"**Position sur le marché :** {cp.market_position}\n\n"
        f"**Produits clés :**\n{_bullets(cp.key_products)}"
    )

    participants_rows = [
        {"name": p.name, "role": p.role, "background": p.background} for p in model.participants
    ]
    participants_body = md_table(
        participants_rows, [("Nom", "name"), ("Rôle", "role"), ("Contexte", "background")]
    )

    if model.talking_points:
        talking_points_body = "\n\n".join(
            f"### {tp.topic}\n\n"
            f"**Points clés :**\n{_bullets(tp.key_points)}\n\n"
            f"**Questions :**\n{_bullets(tp.questions)}"
            for tp in model.talking_points
        )
    else:
        talking_points_body = "_Aucun point._"

    if model.strategic_recommendations:
        recommendations_body = "\n\n".join(
            f"### {r.area}\n\n{r.suggestion}\n\n_Résultat attendu : {r.expected_outcome}_"
            for r in model.strategic_recommendations
        )
    else:
        recommendations_body = "_Aucune recommandation._"

    if model.additional_resources:
        resources_body = "\n".join(
            f"- **{res.title}** : {res.description}" + (f" ({res.link})" if res.link else "")
            for res in model.additional_resources
        )
    else:
        resources_body = "_Aucune ressource._"

    sections = [
        Section(
            "Résumé",
            instruction="Reformule le résumé en prose fluide.",
            context=model.summary or "",
        ),
        Section("Profil de l'entreprise", body=profile_body),
        Section("Participants", body=participants_body),
        Section(
            "Aperçu du secteur",
            instruction="Développe cet aperçu du secteur en prose détaillée.",
            context=model.industry_overview or "",
        ),
        Section("Points de discussion", body=talking_points_body),
        Section("Recommandations stratégiques", body=recommendations_body),
        Section("Ressources", body=resources_body),
    ]
    meta = {
        "title": model.title or "Préparation de réunion",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
