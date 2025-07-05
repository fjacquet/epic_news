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

        # Add styles
        self._add_styles(soup)

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

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for generic formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .generic-report {
            max-width: 800px;
            margin: 0 auto;
        }
        .generic-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .generic-header h2 {
            color: var(--heading-color);
            margin: 0;
        }
        .generic-content, .raw-data-section {
            margin: 1.5rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .content-section, .list-section {
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(108, 117, 125, 0.1);
            border-radius: 6px;
        }
        .content-section h3, .list-section h3, .raw-data-section h3 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 1.2rem;
        }
        .content-section p {
            color: var(--text-color);
            line-height: 1.5;
            margin: 0;
        }
        .list-section ul {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        .list-section li {
            color: var(--text-color);
            margin: 0.25rem 0;
        }
        .raw-data-section pre {
            background: rgba(0, 0, 0, 0.05);
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            margin: 0;
        }
        .raw-data-section code {
            color: var(--text-color);
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
        }
        """
        soup.append(style_tag)
