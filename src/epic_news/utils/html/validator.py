"""HTML validation helper for epic_news.

Uses BeautifulSoup4 to validate HTML, supporting all modern HTML5 tags and structures.
Following the project's design principles (KISS, YAGNI, DRY), this leverages an
established library instead of reinventing validation logic.

If the HTML is unparseable, a ValueError is raised so calling tasks can retry or fail fast.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

__all__ = ["validate_html"]


def validate_html(html: str, raise_on_error: bool = True) -> bool:
    """Validate HTML using BeautifulSoup4.

    BeautifulSoup is lenient and supports all HTML5 tags. This function mainly checks
    if the HTML can be parsed at all, which catches major structural issues.

    Args:
        html: The HTML string to validate
        raise_on_error: If True, raise ValueError on parse failure

    Returns:
        True if valid HTML, False if invalid (when raise_on_error=False)

    Raises:
        ValueError: When HTML cannot be parsed and raise_on_error=True
    """
    # Use html.parser which is built-in and handles HTML5 tags correctly
    soup = BeautifulSoup(html, "html.parser")

    # Basic structure validation - must have body and title
    if not soup.body:
        if raise_on_error:
            raise ValueError("HTML validation failed: Missing required <body> element")
        return False

    if not soup.title:
        if raise_on_error:
            raise ValueError("HTML validation failed: Missing required <title> element in <head>")
        return False

    return True
