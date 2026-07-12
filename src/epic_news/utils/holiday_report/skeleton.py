"""Generate a small, bounded day-by-day skeleton that drives per-day fragment calls."""

import json
from typing import Any

from loguru import logger

from epic_news.models.holiday_report import ItineraryDay, ItinerarySkeleton

_PROMPT = (
    "Tu es un planificateur de voyage. À partir du résumé et de la recherche d'itinéraire, "
    "renvoie UNIQUEMENT un tableau JSON compact, un objet par jour, champs: "
    '"date" (str), "label" (str court), "stops" (liste de str). Pas de texte autour du JSON.'
)


def generate_skeleton(itinerary_research: str, trip_summary: str, llm: Any) -> ItinerarySkeleton:
    """Ask the LLM for a compact day list; fall back to a single day if parsing fails."""
    messages = [
        {"role": "system", "content": _PROMPT},
        {
            "role": "user",
            "content": f"Résumé:\n{trip_summary}\n\nRecherche itinéraire:\n{itinerary_research}",
        },
    ]
    try:
        raw = llm.call(messages)
        payload = json.loads(_extract_json_array(raw))
        days = [ItineraryDay.model_validate(d) for d in payload]
        if days:
            return ItinerarySkeleton(days=days)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Itinerary skeleton parse failed ({}); using single-day fallback", exc)
    return ItinerarySkeleton(days=[ItineraryDay(label="Itinéraire complet", stops=[])])


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found")
    return text[start : end + 1]
