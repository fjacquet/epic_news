"""Turn holiday research outputs into a DOCX via bounded fragments."""

from typing import Any

from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.utils.docx_report import Section, assemble_fragments
from epic_news.utils.holiday_report.skeleton import generate_skeleton

MAX_ITINERARY_DAYS = 31

_PERSONA = (
    "Tu es un rédacteur de carnet de voyage. Rédige UNIQUEMENT la section demandée, "
    "en français, en Markdown propre (titres de niveau 2+, listes, gras, emojis). "
    "Pas de HTML, pas de JSON, pas de préambule."
)


def _task_raw(crew_result: Any, index: int) -> str:
    try:
        return crew_result.tasks_output[index].raw or ""
    except (AttributeError, IndexError, TypeError):
        return ""


def _trip_summary(inputs: dict) -> str:
    return (
        f"Voyage: {inputs.get('family', '')} — {inputs.get('origin', '')} — "
        f"{inputs.get('duration', '')} — {inputs.get('destination', '')}. "
        f"Préférences: {inputs.get('user_preferences_and_constraints', '')}"
    )


def assemble_holiday_docx(crew_result: Any, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the holiday DOCX from research outputs using bounded fragment calls."""
    llm = llm or LLMConfig.get_openrouter_llm()
    summary = _trip_summary(inputs)

    destination = _task_raw(crew_result, 0)
    lodging_dining = _task_raw(crew_result, 1)
    itinerary = _task_raw(crew_result, 2)
    budget = _task_raw(crew_result, 3)

    sections: list[Section] = [
        Section(
            "Introduction",
            "Présente le voyage, la culture et les points forts.",
            f"{summary}\n\n{destination}",
        )
    ]

    # Itinerary: skeleton then one fragment per day (bounded regardless of trip length).
    skeleton = generate_skeleton(itinerary, summary, llm)
    logger.info("🗓️ Itinerary skeleton: {} day(s)", len(skeleton.days))
    if len(skeleton.days) > MAX_ITINERARY_DAYS:
        logger.warning(
            "⚠️ Itinerary skeleton has {} days, exceeding cap of {}; dropping {} day(s)",
            len(skeleton.days),
            MAX_ITINERARY_DAYS,
            len(skeleton.days) - MAX_ITINERARY_DAYS,
        )
    for i, day in enumerate(skeleton.days[:MAX_ITINERARY_DAYS], start=1):
        heading = f"Itinéraire — Jour {i}" + (f" ({day.date})" if day.date else "")
        sections.append(
            Section(
                heading,
                f"Détaille cette journée: {day.label}. Étapes: {', '.join(day.stops) or 'à préciser'}.",
                f"{summary}\n\nRecherche itinéraire:\n{itinerary}",
            )
        )

    sections.append(
        Section(
            "Hébergements",
            "Liste les hébergements recommandés avec adresse et fourchette de prix.",
            f"{summary}\n\n{lodging_dining}",
        )
    )
    sections.append(
        Section(
            "Restauration",
            "Recommande restaurants et spécialités par étape.",
            f"{summary}\n\n{lodging_dining}",
        )
    )
    sections.append(
        Section(
            "Budget",
            "Détaille un budget en CHF, par catégorie, avec total.",
            f"{summary}\n\n{budget}",
        )
    )
    sections.append(
        Section(
            "Informations pratiques",
            "Checklist bagages, sécurité, contacts d'urgence, phrases utiles.",
            f"{summary}\n\n{destination}",
        )
    )

    meta = {
        "title": f"Carnet de voyage — {inputs.get('destination', '')}",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
