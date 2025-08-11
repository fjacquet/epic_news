"""Deprecated: use epic_news.utils.diagnostics instead.
This module re-exports the public API for backward compatibility.
"""

from warnings import warn

from epic_news.utils.diagnostics import (
    analyze_crewai_output,
    dump_crewai_state,
    log_state_keys,
    make_serializable,
    parse_crewai_output,
)

__all__ = [
    "parse_crewai_output",
    "dump_crewai_state",
    "make_serializable",
    "analyze_crewai_output",
    "log_state_keys",
]

warn(
    "epic_news.utils.debug_utils is deprecated; import from epic_news.utils.diagnostics instead",
    DeprecationWarning,
    stacklevel=2,
)
