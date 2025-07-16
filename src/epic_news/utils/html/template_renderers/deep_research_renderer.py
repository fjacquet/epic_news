"""
Deep Research Renderer

Renders deep research report data to structured HTML using BeautifulSoup.
Handles research sections, sources, and comprehensive analysis.
"""

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class DeepResearchRenderer(BaseRenderer):
    """Renders deep research report content with structured formatting."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()

    def render(self, data: dict[str, Any]) -> str:
        """
        Render deep research report data to HTML.

        Args:
            data: Dictionary containing deep research report data

        Returns:
            HTML string for deep research report content
        """
        # Create main container
        soup = self.create_soup("div", class_="deep-research-report")
        container = soup.find("div")

        # Add header
        self._add_header(soup, container, data)

        # Add executive summary
        self._add_executive_summary(soup, container, data)

        # Add key findings
        self._add_key_findings(soup, container, data)

        # Add research sections
        self._add_research_sections(soup, container, data)

        # Add methodology
        self._add_methodology(soup, container, data)

        # Add report metadata
        self._add_report_metadata(soup, container, data)

        return str(soup)

    def _add_header(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add report header with title and metadata."""
        header = soup.new_tag("div", **{"class": "report-header"})

        # Title
        title = data.get("title", "Rapport de Recherche Approfondie")
        title_tag = soup.new_tag("h1", **{"class": "report-title"})
        title_tag.string = f"🔬 {title}"
        header.append(title_tag)

        # Topic
        topic = data.get("topic", "")
        if topic:
            topic_tag = soup.new_tag("h2", **{"class": "report-topic"})
            topic_tag.string = f"Sujet: {topic}"
            header.append(topic_tag)

        # Metadata
        metadata_div = soup.new_tag("div", **{"class": "report-metadata"})

        # Research date
        research_date = data.get("research_date", "")
        if research_date:
            date_tag = soup.new_tag("p", **{"class": "research-date"})
            date_tag.string = f"📅 Date de recherche: {research_date}"
            metadata_div.append(date_tag)

        # Language
        language = data.get("language", "Français")
        lang_tag = soup.new_tag("p", **{"class": "language"})
        lang_tag.string = f"🌐 Langue: {language}"
        metadata_div.append(lang_tag)

        header.append(metadata_div)
        container.append(header)

    def _add_executive_summary(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add executive summary section."""
        summary = data.get("executive_summary", "")
        if not summary:
            return

        section = soup.new_tag("section", **{"class": "executive-summary"})

        title = soup.new_tag("h2", **{"class": "section-title"})
        title.string = "📋 Résumé Exécutif"
        section.append(title)

        summary_div = soup.new_tag("div", **{"class": "summary-content"})
        summary_p = soup.new_tag("p")
        summary_p.string = summary
        summary_div.append(summary_p)
        section.append(summary_div)

        container.append(section)

    def _add_key_findings(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add key findings section."""
        key_findings = data.get("key_findings", [])
        if not key_findings:
            return

        section = soup.new_tag("section", **{"class": "key-findings"})

        title = soup.new_tag("h2", **{"class": "section-title"})
        title.string = "🎯 Principales Découvertes"
        section.append(title)

        findings_div = soup.new_tag("div", **{"class": "findings-content"})
        findings_list = soup.new_tag("ul", **{"class": "findings-list"})

        for finding in key_findings:
            li = soup.new_tag("li", **{"class": "finding-item"})
            li.string = finding
            findings_list.append(li)

        findings_div.append(findings_list)
        section.append(findings_div)
        container.append(section)

    def _add_research_sections(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add research sections with content."""
        sections = data.get("research_sections", [])
        if not sections:
            return

        main_section = soup.new_tag("section", **{"class": "research-sections"})

        title = soup.new_tag("h2", **{"class": "section-title"})
        title.string = "🔍 Sections de Recherche"
        main_section.append(title)

        for i, section_data in enumerate(sections, 1):
            section_div = soup.new_tag("div", **{"class": "research-section"})

            # Section title
            section_title = section_data.get("section_title", f"Section {i}")
            title_tag = soup.new_tag("h3", **{"class": "subsection-title"})
            title_tag.string = section_title
            section_div.append(title_tag)

            # Section content
            content = section_data.get("content", "")
            if content:
                content_div = soup.new_tag("div", **{"class": "section-content"})
                # Split content into paragraphs
                paragraphs = content.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        p_tag = soup.new_tag("p")
                        p_tag.string = paragraph.strip()
                        content_div.append(p_tag)
                section_div.append(content_div)

            # Add sources for this section
            sources = section_data.get("sources", [])
            if sources:
                sources_div = soup.new_tag("div", **{"class": "section-sources"})
                sources_title = soup.new_tag("h4")
                sources_title.string = "📚 Sources"
                sources_div.append(sources_title)

                sources_list = soup.new_tag("ul", **{"class": "sources-list"})
                for source in sources:
                    li = soup.new_tag("li", **{"class": "source-item"})

                    # Source title and URL
                    source_title = source.get("title", "Source")
                    url = source.get("url", "")
                    if url:
                        link = soup.new_tag("a", href=url, target="_blank")
                        link.string = source_title
                        li.append(link)
                    else:
                        li.string = source_title

                    # Source type and summary
                    source_type = source.get("source_type", "")
                    summary = source.get("summary", "")
                    if source_type or summary:
                        details = soup.new_tag("div", **{"class": "source-details"})
                        if source_type:
                            type_span = soup.new_tag("span", **{"class": "source-type"})
                            type_span.string = f"({source_type})"
                            details.append(type_span)
                        if summary:
                            summary_span = soup.new_tag("span", **{"class": "source-summary"})
                            summary_span.string = f" - {summary}"
                            details.append(summary_span)
                        li.append(details)

                    sources_list.append(li)
                sources_div.append(sources_list)
                section_div.append(sources_div)

            main_section.append(section_div)

        container.append(main_section)

    def _add_report_metadata(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add report metadata section."""
        section = soup.new_tag("section", **{"class": "report-metadata"})

        title = soup.new_tag("h2", **{"class": "section-title"})
        title.string = "📊 Informations du Rapport"
        section.append(title)

        metadata_div = soup.new_tag("div", **{"class": "metadata-content"})

        # Report date
        report_date = data.get("report_date", "")
        if report_date:
            date_p = soup.new_tag("p", **{"class": "report-date"})
            date_p.string = f"📅 Date du rapport: {report_date}"
            metadata_div.append(date_p)

        # Sources count
        sources_count = data.get("sources_count", 0)
        if sources_count:
            count_p = soup.new_tag("p", **{"class": "sources-count"})
            count_p.string = f"📚 Nombre de sources: {sources_count}"
            metadata_div.append(count_p)

        # Confidence level
        confidence_level = data.get("confidence_level", "")
        if confidence_level:
            confidence_p = soup.new_tag("p", **{"class": "confidence-level"})
            confidence_p.string = f"🎯 Niveau de confiance: {confidence_level}"
            metadata_div.append(confidence_p)

        section.append(metadata_div)
        container.append(section)

    def _add_methodology(self, soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        """Add methodology section."""
        methodology = data.get("methodology", "")
        if not methodology:
            return

        section = soup.new_tag("section", **{"class": "methodology-section"})

        title = soup.new_tag("h2", **{"class": "section-title"})
        title.string = "🔬 Méthodologie"
        section.append(title)

        methodology_div = soup.new_tag("div", **{"class": "methodology-content"})
        methodology_p = soup.new_tag("p")
        methodology_p.string = methodology
        methodology_div.append(methodology_p)
        section.append(methodology_div)

        container.append(section)
