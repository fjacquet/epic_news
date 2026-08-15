"""Bounded per-section Markdown fragment generation via an LLM."""

from typing import Any

from loguru import logger

from epic_news.utils.interrupt import raise_if_cancelled

# Raised by concurrent.futures once the interpreter starts tearing down (e.g. after a
# Ctrl+C that cancelled the flow task but left this method running in a worker thread).
# Every later LLM call is guaranteed to fail the same way, so degrading to a placeholder
# would only produce a report made of placeholders. Let it propagate and kill the run.
_FATAL_MARKERS: tuple[str, ...] = (
    "cannot schedule new futures",
    "interpreter shutdown",
)


def placeholder_for(heading: str) -> str:
    """Return the marker body used when a section could not be narrated."""
    return f"> ⚠️ Section « {heading} » indisponible."


def _is_fatal(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _FATAL_MARKERS)


def generate_fragment(heading: str, instruction: str, context: str, llm: Any, system: str) -> str:
    """Generate one Markdown section. On an isolated failure, return a placeholder.

    Raises:
        RunCancelledError: the user interrupted the run before this section started.
        Exception: re-raised unchanged when the failure is unrecoverable for the whole
            run (executor/interpreter shutdown), so the caller aborts instead of
            emitting a report full of placeholders.
    """
    # Outside the try: a cancelled run must abort, never degrade to a placeholder.
    raise_if_cancelled(f"narration of section '{heading}'")
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
        if _is_fatal(exc):
            logger.error("💥 Fragment '{}' hit an unrecoverable failure ({}); aborting report", heading, exc)
            raise
        logger.warning("⚠️ Fragment '{}' failed ({}); using placeholder", heading, exc)
    return placeholder_for(heading)
