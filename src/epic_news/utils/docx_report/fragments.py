"""Bounded per-section Markdown fragment generation via an LLM."""

from typing import Any

from loguru import logger


def generate_fragment(heading: str, instruction: str, context: str, llm: Any, system: str) -> str:
    """Generate one Markdown section. On any failure/empty result, return a placeholder."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Section: {heading}\n\nConsigne: {instruction}\n\nContexte:\n{context}"},
    ]
    try:
        md = (llm.call(messages) or "").strip()
        if md:
            return md
        logger.warning("⚠️ Fragment '{}' returned empty; using placeholder", heading)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash the report
        logger.warning("⚠️ Fragment '{}' failed ({}); using placeholder", heading, exc)
    return f"> ⚠️ Section « {heading} » indisponible."
