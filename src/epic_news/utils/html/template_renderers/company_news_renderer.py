"""
Company News Renderer

Renders company news reports with structured sections, summary, and notes.
Handles nested sections and articles as per reporting standards.
"""

from typing import Any

from .base_renderer import BaseRenderer


class CompanyNewsRenderer(BaseRenderer):
    """Renders company news content with business-style formatting."""

    def render(self, data: dict[str, Any], selected_crew: str = None) -> str:
        """
        Render company news data to HTML, removing all internal/raw CrewAI data.
        Only business news content is displayed: summary, sections, articles, and notes.
        """
        soup = self.create_soup("div", class_="company-news-report")
        # Get the root container element that was created by create_soup
        container = soup.find("div", class_="company-news-report")

        # Fallback: if container is still None, create it manually
        if container is None:
            container = soup.new_tag("div", **{"class": "company-news-report"})
            soup.append(container)

        # Add summary as header
        self._add_summary(soup, container, data)

        # Add sections (with empty state handling)
        sections = data.get("sections", [])
        if sections and any(section.get("contenu") for section in sections):
            self._add_sections(soup, container, data)
        else:
            # Friendly message if no news
            empty_div = soup.new_tag("div", **{"class": "company-news-empty"})
            empty_msg = soup.new_tag("p")
            empty_msg.string = "Aucune actualité vérifiable disponible pour cette période."
            empty_div.append(empty_msg)
            container.append(empty_div)

        # Add notes if present
        self._add_notes(soup, container, data)

        # Add styles
        self._add_styles(soup)

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
                    # Extract Markdown link
                    import re

                    m = re.match(r"\\[(.*?)\\]\\((.*?)\\)", article_title)
                    if m:
                        a = soup.new_tag(
                            "a",
                            href=m.group(2),
                            target="_blank",
                            rel="noopener",
                            **{"class": "company-article-link"},
                        )
                        a.string = m.group(1)
                        article_div.append(a)
                    else:
                        article_div.append(soup.new_tag("span", string=article_title))
                else:
                    article_div.append(soup.new_tag("span", string=article_title or "Article"))
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

    def _add_styles(self, soup):
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .company-news-report {
            max-width: 900px;
            margin: 0 auto;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: var(--container-bg, #fff);
            border-radius: 12px;
            border: 1px solid var(--border-color, #ddd);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            padding: 2rem 2.5rem;
        }
        .company-news-header {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        .company-news-header h2 {
            font-size: 2rem;
            color: var(--heading-color, #2a2a2a);
            margin-bottom: 0.5rem;
        }
        .company-news-section {
            margin-bottom: 2.2rem;
        }
        .company-news-section h3 {
            color: #1e88e5;
            font-size: 1.3rem;
            margin-bottom: 0.9rem;
        }
        .company-news-article {
            background: var(--section-bg, #f9f9fd);
            border-radius: 8px;
            border: 1px solid var(--border-color, #eee);
            margin-bottom: 1.1rem;
            padding: 1.1rem 1.3rem;
        }
        .company-article-link {
            font-weight: bold;
            font-size: 1.08rem;
            color: #1565c0;
            text-decoration: underline;
        }
        .company-news-meta {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .company-article-date, .company-article-source {
            margin-right: 1.2rem;
            color: #757575;
            font-size: 0.97rem;
        }
        .company-article-citation {
            margin-top: 0.7rem;
            margin-bottom: 0.7rem;
            font-style: italic;
            color: #333;
            border-left: 3px solid #90caf9;
            padding-left: 1rem;
            background: #f1f8ff;
        }
        .company-news-notes {
            border-top: 1px solid #bdbdbd;
            margin-top: 2.5rem;
            padding-top: 1.2rem;
            color: #444;
        }
        .company-news-notes h4 {
            font-size: 1.1rem;
            color: #388e3c;
            margin-bottom: 0.4rem;
        }
        """
        # Find the container and prepend the style tag
        container = soup.find("div", class_="company-news-report")
        if container:
            container.insert(0, style_tag)
        else:
            # Fallback: append to the soup root
            soup.append(style_tag)
