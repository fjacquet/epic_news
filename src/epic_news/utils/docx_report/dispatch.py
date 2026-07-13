"""Select and run the report renderer for a crew based on the resolved output format."""

from collections.abc import Callable
from typing import Any, cast

from loguru import logger

from epic_news.utils.docx_report.format_selection import resolve_output_format


def emit_report(
    state: Any,
    selected_crew: str,
    render_html: Callable[[], str],
    assemble_docx: Callable[[], str] | None = None,
) -> str:
    """Run the DOCX assembler when DOCX is requested and provided; else render HTML.

    `render_html` runs the crew's existing HTML render and returns its path.
    `assemble_docx` builds the DOCX and returns its path. Both are zero-arg closures
    built at the call site. Sets and returns `state.output_file`.
    """
    fmt = resolve_output_format(state)
    if fmt == "docx" and assemble_docx is not None:
        state.output_file = assemble_docx()
    else:
        if fmt == "docx":
            logger.warning("⚠️ DOCX requested but no assembler for {}; rendering HTML", selected_crew)
        state.output_file = render_html()
    return cast(str, state.output_file)
