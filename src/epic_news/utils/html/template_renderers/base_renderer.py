"""
Base Renderer Abstract Class

Defines the interface for all HTML content renderers.
Uses BeautifulSoup for structured HTML generation.
"""

from abc import ABC, abstractmethod
from typing import Any

from bs4 import BeautifulSoup


class BaseRenderer(ABC):
    """Abstract base class for all HTML content renderers."""

    @abstractmethod
    def __init__(self):
        """Initialize the renderer."""

    @abstractmethod
    def render(self, data: dict[str, Any]) -> str:
        """
        Render content data to HTML string.

        Args:
            data: Dictionary containing content data

        Returns:
            HTML string for the content body
        """

    def create_soup(self, tag: str = "div", **attrs) -> BeautifulSoup:
        """
        Create a new BeautifulSoup object with a root element.

        Args:
            tag: Root HTML tag name
            **attrs: HTML attributes for the root tag

        Returns:
            BeautifulSoup object with root element
        """
        soup = BeautifulSoup(f"<{tag}></{tag}>", "html.parser")
        root = soup.find(tag)

        # Set attributes
        for key, value in attrs.items():
            # Convert Python naming to HTML (class_ -> class)
            if key.endswith("_"):
                key = key[:-1]
            root[key] = value  # type: ignore[index]

        return soup

    def add_section(
        self, soup: BeautifulSoup, parent_selector: str, tag: str, content: str = "", **attrs
    ) -> None:
        """
        Add a new section to the soup.

        Args:
            soup: BeautifulSoup object to modify
            parent_selector: CSS selector for parent element
            tag: HTML tag to create
            content: Text content for the element
            **attrs: HTML attributes
        """
        parent = soup.select_one(parent_selector)
        if parent:
            new_tag = soup.new_tag(tag, **attrs)
            if content:
                new_tag.string = content
            parent.append(new_tag)

    def escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            HTML-escaped text
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
