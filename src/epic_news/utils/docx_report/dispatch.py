"""Write a crew's report: the DOCX assembler is the only output format (spec S5, decision 6)."""

from collections.abc import Callable
from typing import Any


def emit_report(state: Any, assemble_docx: Callable[[], str]) -> str:
    """Run the DOCX assembler and record its path in `state.output_file`.

    Errors propagate: a report that cannot be built stops the run (nothing is emailed).
    """
    path = assemble_docx()
    state.output_file = path
    return path
