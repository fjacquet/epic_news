"""Turn holiday research outputs into a DOCX via bounded fragments."""

from typing import Any

from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.utils.holiday_report.docx_builder import build_docx
from epic_news.utils.holiday_report.fragments import generate_fragment
from epic_news.utils.holiday_report.skeleton import generate_skeleton


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

    fragments: list[tuple[str, str]] = []
    fragments.append(
        (
            "Introduction",
            generate_fragment(
                "Introduction",
                "Présente le voyage, la culture et les points forts.",
                f"{summary}\n\n{destination}",
                llm,
            ),
        )
    )

    # Itinerary: skeleton then one fragment per day (bounded regardless of trip length).
    skeleton = generate_skeleton(itinerary, summary, llm)
    logger.info("🗓️ Itinerary skeleton: {} day(s)", len(skeleton.days))
    for i, day in enumerate(skeleton.days, start=1):
        heading = f"Itinéraire — Jour {i}" + (f" ({day.date})" if day.date else "")
        fragments.append(
            (
                heading,
                generate_fragment(
                    heading,
                    f"Détaille cette journée: {day.label}. Étapes: {', '.join(day.stops) or 'à préciser'}.",
                    f"{summary}\n\nRecherche itinéraire:\n{itinerary}",
                    llm,
                ),
            )
        )

    fragments.append(
        (
            "Hébergements",
            generate_fragment(
                "Hébergements",
                "Liste les hébergements recommandés avec adresse et fourchette de prix.",
                f"{summary}\n\n{lodging_dining}",
                llm,
            ),
        )
    )
    fragments.append(
        (
            "Restauration",
            generate_fragment(
                "Restauration",
                "Recommande restaurants et spécialités par étape.",
                f"{summary}\n\n{lodging_dining}",
                llm,
            ),
        )
    )
    fragments.append(
        (
            "Budget",
            generate_fragment(
                "Budget",
                "Détaille un budget en CHF, par catégorie, avec total.",
                f"{summary}\n\n{budget}",
                llm,
            ),
        )
    )
    fragments.append(
        (
            "Informations pratiques",
            generate_fragment(
                "Informations pratiques",
                "Checklist bagages, sécurité, contacts d'urgence, phrases utiles.",
                f"{summary}\n\n{destination}",
                llm,
            ),
        )
    )

    meta = {
        "title": f"Carnet de voyage — {inputs.get('destination', '')}",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return build_docx(fragments, meta, output_path)
