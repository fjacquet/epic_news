"""
Company News Renderer

Renders company news reports with structured sections, summary, and notes.
Handles nested sections and articles as per reporting standards.
"""

from typing import Any

from .base_renderer import BaseRenderer


class CompanyNewsRenderer(BaseRenderer):
    """Renders company news content with business-style formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], selected_crew: str | None = None) -> str:
        """
        Render company news data to HTML, removing all internal/raw CrewAI data.
        Only business news content is displayed: summary, sections, articles, and notes.
        """
        soup = self.create_soup("div", class_="company-news-report")
        # Get the root container element that was created by create_soup
        container = soup.find("div", class_="company-news-report")

        # Fallback: if container is still None, create it manually
        if container is None:
            container = soup.new_tag("div", **{"class": "company-news-report"})  # type: ignore[arg-type]
            soup.append(container)

        # Add summary as header
        self._add_summary(soup, container, data)

        # Add sections (with empty state handling)
        sections = data.get("sections", [])
        has_content = False

        # More robust content detection
        if sections:
            for section in sections:
                if section.get("contenu") and len(section.get("contenu", [])) > 0:
                    has_content = True
                    break

        if has_content:
            self._add_sections(soup, container, data)
        else:
            # Friendly message if no news
            empty_div = soup.new_tag("div", **{"class": "company-news-empty"})  # type: ignore[arg-type]
            empty_msg = soup.new_tag("p")
            empty_msg.string = "Aucune actualité vérifiable disponible pour cette période."
            empty_div.append(empty_msg)
            container.append(empty_div)  # type: ignore[attr-defined]

        # Add notes if present
        self._add_notes(soup, container, data)


        # Remove any raw/internal CrewAI fields if present (defensive, in case of legacy data)
        # This renderer does not output any fields named 'raw', 'expected_output', 'name', etc.
        # If such fields are present, they are simply ignored.

        return str(soup)

    def _add_summary(self, soup, container, data):
        if container is None:
            return
        summary = data.get("summary")
        if summary:
            header = soup.new_tag("header", **{"class": "company-news-header"})
            h2 = soup.new_tag("h2")
            h2.string = "📰 Synthèse stratégique 2025"
            header.append(h2)
            p = soup.new_tag("p")
            p.string = summary
            header.append(p)
            container.append(header)

    def _add_sections(self, soup, container, data):
        if container is None:
            return
        sections = data.get("sections", [])
        for section in sections:
            section_div = soup.new_tag("section", **{"class": "company-news-section"})
            title = soup.new_tag("h3")
            title.string = f"📌 {section.get('titre', 'Section')}"
            section_div.append(title)
            articles = section.get("contenu", [])
            for article in articles:
                article_div = soup.new_tag("div", **{"class": "company-news-article"})
                # Article title as link if possible
                article_title = article.get("article")
                if article_title and "[" in article_title and "](" in article_title:
                    # Extract Markdown link using a more robust pattern
                    import re

                    # Use search instead of match to find the pattern anywhere in the string
                    m = re.search(r"\[(.*?)\]\((.*?)\)", article_title)
                    if m:
                        title_text = m.group(1)
                        url = m.group(2)

                        # Create the link element
                        a = soup.new_tag(
                            "a",
                            href=url,
                            target="_blank",
                            rel="noopener",
                            **{"class": "company-article-link"},
                        )
                        a.string = title_text
                        article_div.append(a)
                    else:
                        # Fallback if regex doesn't match
                        span = soup.new_tag("span")
                        span.string = article_title
                        article_div.append(span)
                else:
                    # No markdown link format detected
                    span = soup.new_tag("span")
                    span.string = article_title or "Article"
                    article_div.append(span)
                # Meta info
                meta_div = soup.new_tag("div", **{"class": "company-news-meta"})
                if article.get("date"):
                    date_span = soup.new_tag("span", **{"class": "company-article-date"})
                    date_span.string = f"📅 {article['date']}"
                    meta_div.append(date_span)
                if article.get("source"):
                    source_span = soup.new_tag("span", **{"class": "company-article-source"})
                    source_span.string = f"📰 {article['source']}"
                    meta_div.append(source_span)
                article_div.append(meta_div)
                # Citation
                if article.get("citation"):
                    citation_div = soup.new_tag("blockquote", **{"class": "company-article-citation"})
                    citation_div.string = article["citation"]
                    article_div.append(citation_div)
                section_div.append(article_div)
            container.append(section_div)

    def _add_notes(self, soup, container, data):
        if container is None:
            return
        notes = data.get("notes")
        if notes:
            notes_div = soup.new_tag("div", **{"class": "company-news-notes"})
            h4 = soup.new_tag("h4")
            h4.string = "📝 Notes & sources"
            notes_div.append(h4)
            notes_p = soup.new_tag("p")
            notes_p.string = notes
            notes_div.append(notes_p)
            container.append(notes_div)
