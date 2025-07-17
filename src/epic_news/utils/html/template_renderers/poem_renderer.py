"""
Poem Renderer

Renders poem data to structured HTML using BeautifulSoup.
Handles verses, themes, and poetic structure.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class PoemRenderer(BaseRenderer):
    """Renders poem content with artistic formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render poem data to HTML.

        Args:
            data: Dictionary containing poem data

        Returns:
            HTML string for poem content
        """
        # Create main container
        soup = self.create_soup("div", class_="poem-report")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add poem content
        self._add_poem_content(soup, container, data)

        # Add analysis
        self._add_analysis(soup, container, data)

        # Add styles
        self._add_styles(soup)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add poem header."""
        header_div = soup.new_tag("div", class_="poem-header")

        title = data.get("title", "Poème")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"🌌 {title}"
        header_div.append(title_tag)

        # Add theme if available
        theme = data.get("theme")
        if theme:
            theme_p = soup.new_tag("p", class_="poem-theme")
            theme_p.string = f"Thème: {theme}"
            header_div.append(theme_p)

        container.append(header_div)

    def _add_poem_content(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add poem verses and content."""
        content_div = soup.new_tag("div", class_="poem-content")

        # Handle verses
        verses = data.get("verses", [])
        if verses:
            for i, verse in enumerate(verses, 1):
                verse_div = soup.new_tag("div", class_="verse")

                verse_title = soup.new_tag("h4")
                verse_title.string = f"Strophe {i}"
                verse_div.append(verse_title)

                verse_content = soup.new_tag("div", class_="verse-content")

                if isinstance(verse, dict):
                    verse_text = verse.get("content") or verse.get("text", "")
                else:
                    verse_text = str(verse)

                # Split lines and add line breaks
                lines = verse_text.split("\n")
                for _, line in enumerate(lines):
                    if line.strip():
                        line_p = soup.new_tag("p", class_="verse-line")
                        line_p.string = line.strip()
                        verse_content.append(line_p)

                verse_div.append(verse_content)
                content_div.append(verse_div)

        # Handle full poem text if no verses
        elif data.get("poem") or data.get("content"):
            poem_text = data.get("poem") or data.get("content")
            poem_div = soup.new_tag("div", class_="full-poem")

            lines = poem_text.split("\n")
            for line in lines:
                if line.strip():
                    line_p = soup.new_tag("p", class_="poem-line")
                    line_p.string = line.strip()
                    poem_div.append(line_p)

            content_div.append(poem_div)

        if content_div.find_all():
            container.append(content_div)

    def _add_analysis(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add poem analysis section."""
        analysis = data.get("analysis") or data.get("interpretation")
        if not analysis:
            return

        analysis_div = soup.new_tag("div", class_="poem-analysis")

        title_tag = soup.new_tag("h3")
        title_tag.string = "🔍 Analyse Poétique"
        analysis_div.append(title_tag)

        if isinstance(analysis, str):
            analysis_p = soup.new_tag("p")
            analysis_p.string = analysis
            analysis_div.append(analysis_p)
        elif isinstance(analysis, dict):
            for key, value in analysis.items():
                section_div = soup.new_tag("div", class_="analysis-section")

                section_title = soup.new_tag("h4")
                section_title.string = key.replace("_", " ").title()
                section_div.append(section_title)

                section_p = soup.new_tag("p")
                section_p.string = str(value)
                section_div.append(section_p)

                analysis_div.append(section_div)

        container.append(analysis_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for poem formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .poem-report {
            max-width: 700px;
            margin: 0 auto;
        }
        .poem-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .poem-header h2 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }
        .poem-theme {
            color: var(--text-color);
            font-style: italic;
            margin: 0;
        }
        .poem-content {
            margin: 2rem 0;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .verse, .full-poem {
            margin: 1.5rem 0;
            padding: 1rem;
            background: rgba(108, 117, 125, 0.05);
            border-radius: 6px;
            border-left: 4px solid var(--heading-color);
        }
        .verse h4 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        .verse-content, .full-poem {
            font-family: 'Georgia', 'Times New Roman', serif;
        }
        .verse-line, .poem-line {
            color: var(--text-color);
            line-height: 1.8;
            margin: 0.5rem 0;
            padding-left: 1rem;
            font-size: 1.1rem;
        }
        .poem-analysis {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .poem-analysis h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .analysis-section {
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(108, 117, 125, 0.1);
            border-radius: 6px;
        }
        .analysis-section h4 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .analysis-section p {
            color: var(--text-color);
            line-height: 1.5;
            margin: 0;
        }
        """
        soup.append(style_tag)
