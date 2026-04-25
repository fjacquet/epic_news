"""PESTEL Renderer.

Renders a PestelReport (six dimensions + synthesis) as structured HTML using
BeautifulSoup, mirroring the markdown layout produced by ``pestel_markdown``.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .base_renderer import BaseRenderer

_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("political", "Political", "🏛️"),
    ("economic", "Economic", "💰"),
    ("social", "Social", "👥"),
    ("technological", "Technological", "💻"),
    ("environmental", "Environmental", "🌍"),
    ("legal", "Legal", "⚖️"),
)


class PestelRenderer(BaseRenderer):
    """Render a PestelReport dictionary to HTML."""

    def __init__(self) -> None:
        pass

    def render(self, data: dict[str, Any]) -> str:
        soup = self.create_soup("div", class_="pestel-report")
        container = soup.find("div")

        topic = data.get("topic") or "Subject"
        generated_at = data.get("generated_at") or ""
        self.add_report_header(
            soup,
            container,
            f"PESTEL Analysis — {topic}",
            subtitle=f"Generated: {generated_at}" if generated_at else None,
        )

        self.render_text_section(
            soup, container, data.get("executive_summary"), "Executive Summary", icon="📋"
        )

        for key, heading, icon in _DIMENSIONS:
            self._render_dimension(soup, container, data.get(key), heading, icon)

        self.render_text_section(soup, container, data.get("synthesis"), "Synthesis", icon="🎯")

        return str(soup)

    def _render_dimension(
        self,
        soup: BeautifulSoup,
        container: Any,
        dim: dict[str, Any] | None,
        title: str,
        icon: str,
    ) -> None:
        if not dim:
            return
        section = self.create_section(soup, title, icon)

        if summary := dim.get("summary"):
            p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Summary: "
            p.append(strong)
            p.append(summary)
            section.append(p)

        factors = dim.get("key_factors") or []
        h3 = soup.new_tag("h3")
        h3.string = "Key Factors"
        section.append(h3)
        if factors:
            ul = soup.new_tag("ul")
            for factor in factors:
                li = soup.new_tag("li")
                li.string = str(factor)
                ul.append(li)
            section.append(ul)
        else:
            empty = soup.new_tag("p", **{"class": "empty-state"})  # type: ignore[arg-type]
            empty.string = "No factors identified."
            section.append(empty)

        if impact := dim.get("impact_analysis"):
            h3 = soup.new_tag("h3")
            h3.string = "Strategic Impact"
            section.append(h3)
            p = soup.new_tag("p")
            p.string = impact
            section.append(p)

        sources = dim.get("sources") or []
        if sources:
            h3 = soup.new_tag("h3")
            h3.string = "Sources"
            section.append(h3)
            ul = soup.new_tag("ul")
            for src in sources:
                li = soup.new_tag("li")
                src_text = str(src)
                if src_text.startswith(("http://", "https://")):
                    a = soup.new_tag("a", href=src_text)
                    a.string = src_text
                    a.attrs["target"] = "_blank"
                    a.attrs["rel"] = "noopener"
                    li.append(a)
                else:
                    li.string = src_text
                ul.append(li)
            section.append(ul)

        container.append(section)
