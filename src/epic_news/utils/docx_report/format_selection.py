"""Runtime HTML/DOCX selection: OUTPUT_FORMAT flag > parsed request intent > HTML."""

import os
import re
from typing import Any

_DOCX_PATTERN = re.compile(
    r"\b(docx|word\s+document|document\s+word|fichier\s+word|format\s+docx|en\s+docx|as\s+a\s+word\s+doc\w*)\b",
    re.IGNORECASE,
)


def parse_output_format(request: str | None) -> str | None:
    """Return "docx" if the request asks for a Word/DOCX document, else None."""
    if request and _DOCX_PATTERN.search(request):
        return "docx"
    return None


def resolve_output_format(state: Any) -> str:
    """Resolve the output format. Precedence: OUTPUT_FORMAT env > state.output_format > "html"."""
    env = os.getenv("OUTPUT_FORMAT")
    if env in ("html", "docx"):
        return env
    return getattr(state, "output_format", None) or "html"
