"""
Generic Renderer

Fallback renderer for crew types that don't have specialized renderers.
Provides basic HTML structure with BeautifulSoup.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class GenericRenderer(BaseRenderer):
    """Generic fallback renderer for any crew type."""

    def __init__(self):
        """Initialize the renderer."""

    def render(self, data: dict[str, Any], crew_type: str = "UNKNOWN") -> str:
        """
        Render generic content data to HTML.

        Args:
            data: Dictionary containing content data
            crew_type: Type of crew for context

        Returns:
            HTML string for generic content
        """
        # Create main container
        soup = self.create_soup("div", class_="generic-report")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, crew_type)

        # Add content sections
        self._add_content_sections(soup, container, data)

        # Add raw data if available
        self._add_raw_data(soup, container, data)


        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, crew_type: str) -> None:
        """Add generic header."""
        header_div = soup.new_tag("div", class_="generic-header")

        title_tag = soup.new_tag("h2")
        title_tag.string = f"📄 Rapport {crew_type}"
        header_div.append(title_tag)

        container.append(header_div)

    def _add_content_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add content sections based on available data."""
        content_div = soup.new_tag("div", class_="generic-content")

        # Handle common fields
        common_fields = ["title", "summary", "content", "description", "text"]

        for field in common_fields:
            value = data.get(field)
            if value and isinstance(value, str) and value.strip():
                section_div = soup.new_tag("div", class_="content-section")

                # Section title
                title_tag = soup.new_tag("h3")
                title_tag.string = field.title()
                section_div.append(title_tag)

                # Section content
                content_p = soup.new_tag("p")
                content_p.string = value
                section_div.append(content_p)

                content_div.append(section_div)

        # Handle lists
        for key, value in data.items():
            if isinstance(value, list) and value:
                section_div = soup.new_tag("div", class_="list-section")

                # Section title
                title_tag = soup.new_tag("h3")
                title_tag.string = key.replace("_", " ").title()
                section_div.append(title_tag)

                # List items
                ul = soup.new_tag("ul")
                for item in value:
                    li = soup.new_tag("li")
                    if isinstance(item, dict):
                        # Handle dict items
                        item_str = ", ".join([f"{k}: {v}" for k, v in item.items() if v])
                        li.string = item_str
                    else:
                        li.string = str(item)
                    ul.append(li)

                section_div.append(ul)
                content_div.append(section_div)

        if content_div.find_all():
            container.append(content_div)

    def _add_raw_data(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add raw data section for debugging."""
        if not data:
            return

        raw_div = soup.new_tag("div", class_="raw-data-section")

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "🔧 Données brutes"
        raw_div.append(title_tag)

        # Raw data as formatted text
        pre_tag = soup.new_tag("pre")
        code_tag = soup.new_tag("code")

        # Format data nicely
        formatted_data = []
        for key, value in data.items():
            if isinstance(value, str | int | float | bool):
                formatted_data.append(f"{key}: {value}")
            elif isinstance(value, list):
                formatted_data.append(f"{key}: [{len(value)} items]")
            elif isinstance(value, dict):
                formatted_data.append(f"{key}: {{{len(value)} fields}}")
            else:
                formatted_data.append(f"{key}: {type(value).__name__}")

        code_tag.string = "\n".join(formatted_data)
        pre_tag.append(code_tag)
        raw_div.append(pre_tag)

        container.append(raw_div)
