"""
Book Summary Renderer

Renders book summary data to structured HTML using BeautifulSoup.
Replaces string concatenation with proper DOM manipulation.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class BookSummaryRenderer(BaseRenderer):
    """Renders book summary content with rich formatting and structure."""

    def render(self, data: dict[str, Any]) -> str:
        """
        Render book summary data to HTML.

        Args:
            data: Dictionary containing book summary data

        Returns:
            HTML string for book summary content
        """
        # Create main container
        soup = self.create_soup("div")
        soup.find("div")["class"] = "book-summary-report"
        container = soup.find("div")

        # Add book header
        self._add_book_header(soup, container, data)

        # Add summary section
        self._add_summary_section(soup, container, data)

        # Add table of contents
        self._add_table_of_contents(soup, container, data)

        # Add chapters section
        self._add_chapters_section(soup, container, data)

        # Add analysis sections
        self._add_analysis_sections(soup, container, data)

        # Add references
        self._add_references_section(soup, container, data)

        # Add CSS styles
        self._add_styles(soup)

        return soup.prettify()

    def _add_book_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add book header with title, author, and publication date."""
        header_div = soup.new_tag("div")
        header_div["class"] = "book-header"

        # Title
        title = data.get("title", "Livre")
        title_tag = soup.new_tag("h2")
        title_tag.string = f"📖 {title}"
        header_div.append(title_tag)

        # Meta information
        meta_div = soup.new_tag("div")
        meta_div["class"] = "book-meta"

        # Author
        author = data.get("author", "Auteur inconnu")
        author_p = soup.new_tag("p")
        author_strong = soup.new_tag("strong")
        author_strong.string = "✍️ Auteur:"
        author_p.append(author_strong)
        author_p.append(f" {author}")
        meta_div.append(author_p)

        # Publication date
        pub_date = data.get("publication_date", "")
        if pub_date:
            date_p = soup.new_tag("p")
            date_strong = soup.new_tag("strong")
            date_strong.string = "📅 Publication:"
            date_p.append(date_strong)
            date_p.append(f" {pub_date}")
            meta_div.append(date_p)

        header_div.append(meta_div)
        container.append(header_div)

    def _add_summary_section(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add book summary section."""
        summary = data.get("summary", "")
        if not summary:
            return

        summary_div = soup.new_tag("div")
        summary_div["class"] = "book-summary"

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "📋 Résumé"
        summary_div.append(title_tag)

        # Summary text
        summary_p = soup.new_tag("p")
        summary_p["class"] = "summary-text"
        summary_p.string = summary
        summary_div.append(summary_p)

        container.append(summary_div)

    def _add_table_of_contents(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add table of contents section."""
        toc_data = data.get("table_of_contents", [])
        if not toc_data:
            return

        toc_div = soup.new_tag("div")
        toc_div["class"] = "table-of-contents"

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "📖 Table des matières"
        toc_div.append(title_tag)

        # TOC list
        toc_ul = soup.new_tag("ul")
        toc_ul["class"] = "toc-list"

        for item in toc_data:
            chapter_title = item.get("title", "")
            chapter_id = item.get("id", "")

            if chapter_title:
                li = soup.new_tag("li")
                link = soup.new_tag("a", href=f"#{chapter_id}")
                link.string = chapter_title
                li.append(link)
                toc_ul.append(li)

        if toc_ul.find_all("li"):
            toc_div.append(toc_ul)
            container.append(toc_div)

    def _add_chapters_section(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add chapters section."""
        chapters = data.get("chapters", []) or data.get("chapter_summaries", [])
        if not chapters:
            return

        chapters_div = soup.new_tag("div")
        chapters_div["class"] = "chapters-section"

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "📑 Chapitres"
        chapters_div.append(title_tag)

        # Chapter items
        for chapter in chapters:
            ch_num = chapter.get("chapter", "")
            ch_title = chapter.get("title", "")
            ch_focus = chapter.get("focus", "")

            if ch_title:
                chapter_div = soup.new_tag("div")
                chapter_div["class"] = "chapter-item"

                # Chapter title
                ch_h4 = soup.new_tag("h4")
                ch_h4.string = f"📚 Chapitre {ch_num}: {ch_title}"
                chapter_div.append(ch_h4)

                # Chapter focus
                if ch_focus:
                    ch_p = soup.new_tag("p")
                    ch_p.string = ch_focus
                    chapter_div.append(ch_p)

                chapters_div.append(chapter_div)

        if chapters_div.find_all("div", class_="chapter-item"):
            container.append(chapters_div)

    def _add_analysis_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add detailed analysis sections."""
        sections = data.get("sections", [])
        if not sections:
            return

        analysis_div = soup.new_tag("div")
        analysis_div["class"] = "book-analysis"

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "📝 Analyse détaillée"
        analysis_div.append(title_tag)

        # Analysis sections
        for section in sections:
            sec_title = section.get("title", "")
            sec_content = section.get("content", "")
            sec_id = section.get("id", "")

            if sec_title and sec_content:
                section_div = soup.new_tag("div")
                section_div["class"] = "analysis-section"
                section_div["id"] = sec_id

                # Section title
                sec_h4 = soup.new_tag("h4")
                sec_h4.string = f"🔍 {sec_title}"
                section_div.append(sec_h4)

                # Section content
                sec_p = soup.new_tag("p")
                sec_p.string = sec_content
                section_div.append(sec_p)

                analysis_div.append(section_div)

        if analysis_div.find_all("div", class_="analysis-section"):
            container.append(analysis_div)

    def _add_references_section(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add references section."""
        references = data.get("references", [])
        if not references:
            return

        ref_div = soup.new_tag("div")
        ref_div["class"] = "references-section"

        # Title
        title_tag = soup.new_tag("h3")
        title_tag.string = "📚 Références"
        ref_div.append(title_tag)

        # References list
        ref_ul = soup.new_tag("ul")
        ref_ul["class"] = "references-list"

        for ref in references:
            if ref and ref.strip():
                li = soup.new_tag("li")
                link = soup.new_tag("a", href=ref, target="_blank", rel="noopener")
                link.string = f"🔗 {ref}"
                li.append(link)
                ref_ul.append(li)

        if ref_ul.find_all("li"):
            ref_div.append(ref_ul)
            container.append(ref_div)

    def _add_styles(self, soup: BeautifulSoup) -> None:
        """Add CSS styles for book summary formatting."""
        style_tag = soup.new_tag("style")
        style_tag.string = """
        .book-summary-report {
            max-width: 900px;
            margin: 0 auto;
        }
        .book-header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--container-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .book-header h2 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 2rem;
        }
        .book-meta {
            color: var(--text-color);
            font-size: 1.1rem;
        }
        .book-meta p {
            margin: 0.5rem 0;
        }
        .book-summary, .table-of-contents, .chapters-section, .book-analysis, .references-section {
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--container-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .book-summary h3, .table-of-contents h3, .chapters-section h3, .book-analysis h3, .references-section h3 {
            color: var(--heading-color);
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        .summary-text {
            font-size: 1.1rem;
            line-height: 1.6;
            color: var(--text-color);
        }
        .toc-list {
            list-style: none;
            padding: 0;
        }
        .toc-list li {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: rgba(0, 123, 179, 0.1);
            border-radius: 4px;
        }
        .toc-list a {
            color: var(--heading-color);
            text-decoration: none;
            font-weight: 500;
        }
        .toc-list a:hover {
            text-decoration: underline;
        }
        .chapter-item, .analysis-section {
            margin: 1.5rem 0;
            padding: 1rem;
            background: rgba(108, 117, 125, 0.1);
            border-radius: 6px;
            border-left: 4px solid var(--heading-color);
        }
        .chapter-item h4, .analysis-section h4 {
            color: var(--heading-color);
            margin-bottom: 0.5rem;
        }
        .chapter-item p, .analysis-section p {
            color: var(--text-color);
            line-height: 1.5;
            margin: 0;
        }
        .references-list {
            list-style: none;
            padding: 0;
        }
        .references-list li {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: rgba(40, 167, 69, 0.1);
            border-radius: 4px;
        }
        .references-list a {
            color: var(--heading-color);
            text-decoration: none;
        }
        .references-list a:hover {
            text-decoration: underline;
        }
        """
        soup.append(style_tag)
