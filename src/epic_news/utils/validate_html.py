"""HTML validation helper for epic_news.

Uses lxml's HTML parser to ensure the generated HTML is well-formed. This is a
lightweight fallback that works cross-platform without external `tidy` binary
dependencies. If parsing errors are detected, a **ValueError** is raised so
calling tasks can retry or fail fast.
"""
from __future__ import annotations

from typing import List

from lxml import etree  # type: ignore

__all__ = ["validate_html"]


def _collect_errors(html: str) -> List[str]:
    """Parse HTML and return list of error strings (empty if none)."""
    parser = etree.HTMLParser(recover=False)
    try:
        etree.fromstring(html.encode("utf-8"), parser)
    except etree.XMLSyntaxError as exc:  # pragma: no cover
        # `exc.error_log` contains structured messages
        return [str(e) for e in exc.error_log]
    return []


def validate_html(html: str, raise_on_error: bool = True) -> bool:  # noqa: D401
    """Validate `html` string.

    Returns True if valid, False otherwise (or raises if *raise_on_error*).
    """
    errors = _collect_errors(html)
    if errors:
        if raise_on_error:
            err = "\n".join(errors)
            raise ValueError(f"HTML validation failed:\n{err}")
        return False
    return True
