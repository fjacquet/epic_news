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
        super().__init__()

    def render(self, data: dict[str, Any], *_ignore, **__ignore) -> str:
        """Return the rendered report as an HTML string."""
        soup = self.create_soup("div", class_="sales-prospecting-report")
        container = soup.div

        self._add_styles(soup)
        self._add_header(soup, container)
        self._add_company_overview(soup, container, data)
        self._add_key_contacts(soup, container, data)
        self._add_approach_strategy(soup, container, data)
        self._add_remaining_information(soup, container, data)
        self._add_raw_data(soup, container, data)

        return str(soup)

    @staticmethod
    def _add_header(soup: BeautifulSoup, container) -> None:
        header = soup.new_tag("div", **{"class": "report-header"})
        header.append(soup.new_tag("h1", string="Sales Prospecting Report"))
        container.append(header)

    @staticmethod
    def _add_company_overview(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        overview = data.get("company_overview")
        if not overview:
            return

        section = soup.new_tag("section", **{"class": "report-section"})
        section.append(soup.new_tag("h2", string="Company Overview"))
        section.append(soup.new_tag("p", string=overview))
        container.append(section)

    @staticmethod
    def _add_key_contacts(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        contacts = data.get("key_contacts")
        if not contacts:
            return

        section = soup.new_tag("section", **{"class": "report-section"})
        section.append(soup.new_tag("h2", string="Key Contacts"))

        grid = soup.new_tag("div", **{"class": "contacts-grid"})
        for contact in contacts:
            card = soup.new_tag("div", **{"class": "contact-card"})
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

        section = soup.new_tag("section", **{"class": "report-section"})
        section.append(soup.new_tag("h2", string="Approach Strategy"))
        section.append(soup.new_tag("p", string=strategy))
        container.append(section)

    @staticmethod
    def _add_remaining_information(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        info = data.get("remaining_information")
        if not info:
            return

        section = soup.new_tag("section", **{"class": "report-section"})
        section.append(soup.new_tag("h2", string="Remaining Information"))
        section.append(soup.new_tag("p", string=info))
        container.append(section)

    @staticmethod
    def _add_raw_data(soup: BeautifulSoup, container, data: dict[str, Any]) -> None:
        details = soup.new_tag("details", **{"class": "raw-data"})
        details.append(soup.new_tag("summary", string="View Raw Data"))
        pre = soup.new_tag("pre")
        code = soup.new_tag("code")
        code.string = json.dumps(data, indent=2, ensure_ascii=False)
        pre.append(code)
        details.append(pre)
        container.append(details)

    @staticmethod
    def _add_styles(soup: BeautifulSoup) -> None:
        style = soup.new_tag("style")
        style.string = """
            :root {
                --background-light: #ffffff;
                --text-light: #333;
                --header-light: #111827;
                --section-border-light: #e5e7eb;
                --card-bg-light: #f9fafb;
                --card-border-light: #e5e7eb;
                --raw-summary-light: #374151;
                --raw-pre-bg-light: #f3f4f6;

                --background-dark: #121212;
                --text-dark: #e0e0e0;
                --header-dark: #ffffff;
                --section-border-dark: #374151;
                --card-bg-dark: #1f2937;
                --card-border-dark: #374151;
                --raw-summary-dark: #d1d5db;
                --raw-pre-bg-dark: #111827;
            }

            .sales-prospecting-report {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                max-width: 800px;
                margin: 2rem auto;
                padding: 2rem;
                background-color: var(--background-light);
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: var(--text-light);
            }
            .report-header {
                text-align: center;
                margin-bottom: 2.5rem;
                border-bottom: 1px solid var(--section-border-light);
                padding-bottom: 1rem;
            }
            .report-header h1 {
                font-size: 2.25rem;
                font-weight: 700;
                color: var(--header-light);
            }
            .report-section {
                margin-bottom: 2rem;
            }
            .report-section h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--header-light);
                margin-bottom: 1rem;
                border-bottom: 1px solid var(--section-border-light);
                padding-bottom: 0.5rem;
            }
            .report-section p {
                line-height: 1.6;
                color: var(--text-light);
            }
            .contacts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
            }
            .contact-card {
                background-color: var(--card-bg-light);
                border: 1px solid var(--card-border-light);
                border-radius: 8px;
                padding: 1.5rem;
                transition: box-shadow 0.3s ease;
            }
            .contact-card:hover {
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            }
            .contact-card h3 {
                font-size: 1.125rem;
                font-weight: 600;
                margin: 0 0 0.5rem 0;
                color: var(--header-light);
            }
            .contact-card p {
                margin: 0.25rem 0;
                color: var(--text-light);
                font-size: 0.9rem;
            }
            .raw-data {
                margin-top: 2.5rem;
                border-top: 1px solid var(--section-border-light);
                padding-top: 1.5rem;
            }
            .raw-data summary {
                cursor: pointer;
                font-weight: 500;
                color: var(--raw-summary-light);
            }
            .raw-data pre {
                background-color: var(--raw-pre-bg-light);
                padding: 1rem;
                border-radius: 8px;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin-top: 1rem;
            }

            @media (prefers-color-scheme: dark) {
                .sales-prospecting-report {
                    background-color: var(--background-dark);
                    color: var(--text-dark);
                }
                .report-header {
                    border-bottom-color: var(--section-border-dark);
                }
                .report-header h1 {
                    color: var(--header-dark);
                }
                .report-section h2 {
                    color: var(--header-dark);
                    border-bottom-color: var(--section-border-dark);
                }
                .report-section p {
                    color: var(--text-dark);
                }
                .contact-card {
                    background-color: var(--card-bg-dark);
                    border-color: var(--card-border-dark);
                }
                .contact-card h3 {
                    color: var(--header-dark);
                }
                .contact-card p {
                    color: var(--text-dark);
                }
                .raw-data {
                    border-top-color: var(--section-border-dark);
                }
                .raw-data summary {
                    color: var(--raw-summary-dark);
                }
                .raw-data pre {
                    background-color: var(--raw-pre-bg-dark);
                }
            }
        """
        soup.append(style)
