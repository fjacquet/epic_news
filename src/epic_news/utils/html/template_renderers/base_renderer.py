"""
Base Renderer Abstract Class

Defines the interface for all HTML content renderers.
Uses BeautifulSoup for structured HTML generation.

Provides shared helper methods for common rendering patterns:
- add_report_header: Standard header with title and optional subtitle
- add_raw_json_section: Collapsible raw JSON for debugging
- render_dict_as_cards: Render dictionary as info cards
- render_list_as_cards: Render list items as cards in a grid
"""

import json
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

    # -------------------------------------------------------------------------
    # Shared Helper Methods - Use these to reduce code duplication
    # -------------------------------------------------------------------------

    def add_report_header(
        self,
        soup: BeautifulSoup,
        container: Any,
        title: str,
        subtitle: str | None = None,
    ) -> None:
        """
        Add a standard report header with title and optional subtitle.

        Args:
            soup: BeautifulSoup object
            container: Parent element to append to
            title: Main title text (can include emoji)
            subtitle: Optional subtitle (e.g., company name)
        """
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        h1 = soup.new_tag("h1")
        h1.string = title
        header.append(h1)
        if subtitle:
            h2 = soup.new_tag("h2")
            h2.string = subtitle
            header.append(h2)
        container.append(header)

    def add_raw_json_section(
        self,
        soup: BeautifulSoup,
        container: Any,
        data: dict[str, Any],
        title: str = "Données brutes",
    ) -> None:
        """
        Add a collapsible raw JSON section for debugging.

        Args:
            soup: BeautifulSoup object
            container: Parent element to append to
            data: Data to serialize as JSON
            title: Section title
        """
        details = soup.new_tag("details", **{"class": "raw-data"})  # type: ignore[arg-type]
        summary = soup.new_tag("summary")
        summary.string = title
        details.append(summary)
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        container.append(details)

    def add_section_title(
        self,
        soup: BeautifulSoup,
        section: Any,
        title: str,
        icon: str = "",
    ) -> None:
        """
        Add a section title with optional icon.

        Args:
            soup: BeautifulSoup object
            section: Section element to add title to
            title: Title text
            icon: Optional emoji icon
        """
        h2 = soup.new_tag("h2")
        h2.string = f"{icon} {title}" if icon else title
        section.append(h2)

    def create_section(
        self,
        soup: BeautifulSoup,
        title: str,
        icon: str = "",
        css_class: str = "report-section",
    ) -> Any:
        """
        Create a new section element with title.

        Args:
            soup: BeautifulSoup object
            title: Section title
            icon: Optional emoji icon
            css_class: CSS class for the section

        Returns:
            The created section element
        """
        section = soup.new_tag("section", **{"class": css_class})  # type: ignore[arg-type]
        self.add_section_title(soup, section, title, icon)
        return section

    def render_dict_as_cards(
        self,
        soup: BeautifulSoup,
        container: Any,
        data: dict[str, Any] | None,
        title: str,
        icon: str = "",
        card_class: str = "info-card",
    ) -> None:
        """
        Render a dictionary as a section with info cards.

        Args:
            soup: BeautifulSoup object
            container: Parent element to append to
            data: Dictionary to render (key-value pairs), or None to skip
            title: Section title
            icon: Optional emoji icon
            card_class: CSS class for cards
        """
        if not data:
            return

        section = self.create_section(soup, title, icon)

        for key, value in data.items():
            card = soup.new_tag("div", **{"class": card_class})  # type: ignore[arg-type]
            card_title = soup.new_tag("h3")
            card_title.string = key.replace("_", " ").title()
            card.append(card_title)

            if isinstance(value, list):
                ul = soup.new_tag("ul")
                for item in value:
                    li = soup.new_tag("li")
                    li.string = str(item)
                    ul.append(li)
                card.append(ul)
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    p = soup.new_tag("p")
                    strong = soup.new_tag("strong")
                    strong.string = f"{sub_key.replace('_', ' ').title()}: "
                    p.append(strong)
                    p.append(str(sub_val))
                    card.append(p)
            else:
                p = soup.new_tag("p")
                p.string = str(value) if value else "N/A"
                card.append(p)

            section.append(card)

        container.append(section)

    def render_list_as_cards(
        self,
        soup: BeautifulSoup,
        container: Any,
        items: list[dict[str, Any]] | None,
        title: str,
        icon: str = "",
        card_class: str = "info-card",
        title_key: str | None = None,
    ) -> None:
        """
        Render a list of dictionaries as cards in a grid.

        Args:
            soup: BeautifulSoup object
            container: Parent element to append to
            items: List of dictionaries to render, or None to skip
            title: Section title
            icon: Optional emoji icon
            card_class: CSS class for cards
            title_key: Key to use for card title (first key if None)
        """
        if not items:
            return

        section = self.create_section(soup, title, icon)
        grid = soup.new_tag("div", **{"class": "cards-grid"})  # type: ignore[arg-type]

        for item in items:
            card = soup.new_tag("div", **{"class": card_class})  # type: ignore[arg-type]

            # Determine card title
            if title_key and title_key in item:
                card_title_text = str(item[title_key])
            elif item:
                first_key = next(iter(item.keys()))
                card_title_text = str(item[first_key])
            else:
                card_title_text = "Item"

            card_title = soup.new_tag("h3")
            card_title.string = card_title_text
            card.append(card_title)

            # Render remaining fields
            for key, value in item.items():
                if title_key and key == title_key:
                    continue
                if not title_key and key == next(iter(item.keys())):
                    continue

                p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = f"{key.replace('_', ' ').title()}: "
                p.append(strong)
                p.append(str(value) if value else "N/A")
                card.append(p)

            grid.append(card)

        section.append(grid)
        container.append(section)

    def render_text_section(
        self,
        soup: BeautifulSoup,
        container: Any,
        text: str | None,
        title: str,
        icon: str = "",
    ) -> None:
        """
        Render a simple text section.

        Args:
            soup: BeautifulSoup object
            container: Parent element to append to
            text: Text content
            title: Section title
            icon: Optional emoji icon
        """
        if not text:
            return

        section = self.create_section(soup, title, icon)
        p = soup.new_tag("p")
        p.string = text
        section.append(p)
        container.append(section)

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
