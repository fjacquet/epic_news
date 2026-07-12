"""Bounded per-section Markdown fragment generation for the holiday report."""

from typing import Any

from loguru import logger

_SYSTEM = (
    "Tu es un rédacteur de carnet de voyage. Rédige UNIQUEMENT la section demandée, "
    "en français, en Markdown propre (titres de niveau 2+, listes, gras, emojis). "
    "Pas de HTML, pas de JSON, pas de préambule."
)


def generate_fragment(heading: str, instruction: str, context: str, llm: Any) -> str:
    """Generate one Markdown section. On any failure/empty result, return a placeholder."""
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Section: {heading}\n\nConsigne: {instruction}\n\nContexte:\n{context}"},
    ]
    try:
        md = (llm.call(messages) or "").strip()
        if md:
            return md
        logger.warning("⚠️ Fragment '{}' returned empty; using placeholder", heading)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Fragment '{}' failed ({}); using placeholder", heading, exc)
    return f"> ⚠️ Section « {heading} » indisponible pour ce voyage."
