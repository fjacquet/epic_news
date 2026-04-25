"""Sales Prospecting Renderer

Converts validated sales prospecting data into a visually appealing HTML fragment.
This renderer is designed to be modern, clean, and easily readable, aligning
with the goal of producing a "perfect report".

Sections rendered:
1. Header
2. Company Overview
3. Key Contacts
4. Approach Strategy
5. Remaining Information
6. Collapsible raw JSON (for debugging)
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer


class SalesProspectingRenderer(BaseRenderer):
    """Render a sales prospecting report into a modern HTML fragment."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()  # type: ignore[safe-super]

    def render(self, data: dict[str, Any], *_ignore, **__ignore) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="sales-prospecting-report")
        container = soup.div

        self._add_header(soup, container)
        self._add_company_overview(soup, container, data)
        self._add_key_contacts(soup, container, data)
        self._add_approach_strategy(soup, container, data)
        self._add_remaining_information(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})  # type: ignore[arg-type]
        header.append(soup.new_tag("h1", string="Sales Prospecting Report"))
        container.append(header)

    @staticmethod
    def _add_company_overview(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        overview = data.get("company_overview")
        if not overview:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        section.append(soup.new_tag("h2", string="Company Overview"))
        section.append(soup.new_tag("p", string=overview))
        container.append(section)

    @staticmethod
    def _add_key_contacts(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        contacts = data.get("key_contacts")
        if not contacts:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        section.append(soup.new_tag("h2", string="Key Contacts"))

        grid = soup.new_tag("div", **{"class": "contacts-grid"})  # type: ignore[arg-type]
        for contact in contacts:
            card = soup.new_tag("div", **{"class": "contact-card"})  # type: ignore[arg-type]
            card.append(soup.new_tag("h3", string=contact.get("name", "N/A")))
            card.append(soup.new_tag("p", string=contact.get("role", "N/A")))
            card.append(soup.new_tag("p", string=contact.get("department", "N/A")))
            card.append(soup.new_tag("p", string=contact.get("contact_info", "N/A")))
            grid.append(card)

        section.append(grid)
        container.append(section)

    @staticmethod
    def _add_approach_strategy(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        strategy = data.get("approach_strategy")
        if not strategy:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        section.append(soup.new_tag("h2", string="Approach Strategy"))
        section.append(soup.new_tag("p", string=strategy))
        container.append(section)

    @staticmethod
    def _add_remaining_information(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        info = data.get("remaining_information")
        if not info:
            return

        section = soup.new_tag("section", **{"class": "report-section"})  # type: ignore[arg-type]
        section.append(soup.new_tag("h2", string="Remaining Information"))
        section.append(soup.new_tag("p", string=info))
        container.append(section)

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        details = soup.new_tag("details", **{"class": "raw-data"})  # type: ignore[arg-type]
        details.append(soup.new_tag("summary", string="View Raw Data"))
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        container.append(details)
