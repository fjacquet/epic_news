"""POEM → DOCX: deterministic, no LLM. The poem is the report; it is not narrated."""

from typing import Any

from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.utils.docx_report import build_docx


def _stanzas_markdown(poem: str) -> str:
    """Keep each line break inside a stanza (two trailing spaces) and blank lines between stanzas."""
    stanzas = [s for s in poem.replace("\r\n", "\n").split("\n\n") if s.strip()]
    return "\n\n".join("  \n".join(line.strip() for line in s.strip().split("\n")) for s in stanzas)


def assemble_poem_docx(model: PoemJSONOutput, inputs: dict, output_path: str, llm: Any = None) -> str:
    """Build the poem as a DOCX. `llm` is unused (kept for the common assembler signature)."""
    fragments = [("Poème", _stanzas_markdown(model.poem or ""))]
    meta = {
        "title": model.title or "Poème",
        "date": inputs.get("current_date", ""),
        "author": "Epic News",
    }
    return build_docx(fragments, meta, output_path)
