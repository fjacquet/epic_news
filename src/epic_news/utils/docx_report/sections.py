"""Section spec for DOCX assembly: narrated (LLM) or deterministic (verbatim body)."""

from dataclasses import dataclass


@dataclass
class Section:
    """One report section. `body` set → used verbatim (deterministic, no LLM).
    Otherwise narrated from `instruction` + `context`."""

    heading: str
    instruction: str | None = None
    context: str | None = None
    body: str | None = None
