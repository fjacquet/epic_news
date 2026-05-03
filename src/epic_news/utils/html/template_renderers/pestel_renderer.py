"""PESTEL Renderer.

Renders a PestelReport (six dimensions + synthesis) as structured HTML using
BeautifulSoup, mirroring the markdown layout produced by ``pestel_markdown``.
"""

from __future__ import annotations

import re
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

# Numbered bold heading at start of line: "1. **Title** :"
_IMPACT_HEADING_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+\.\s+)?\*\*([^*\n]+?)\*\*\s*:\s*",
    re.MULTILINE,
)

_IMPACT_BUCKETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("opportunity-card", "✅", "Opportunités", ("opportun",)),
    ("threat-card", "⚠️", "Risques & Menaces", ("menace", "risque")),
    ("recommendation-card", "💡", "Recommandations", ("recommand",)),
)


def _classify_heading(title: str) -> str | None:
    """Return the impact bucket key matching ``title``, or None."""
    lowered = title.strip().lower()
    for bucket in _IMPACT_BUCKETS:
        key, needles = bucket[0], bucket[3]
        if any(n in lowered for n in needles):
            return key
    return None


def _split_impact_into_buckets(
    text: str,
) -> tuple[str, dict[str, str], str] | None:
    """Try to split impact text into Opportunités / Risques / Recommandations.

    Returns a tuple ``(prologue, buckets, epilogue)`` when at least two buckets
    are detected and every detected heading classifies into a known bucket.
    Otherwise returns ``None`` so callers fall back to flat markdown rendering.
    """
    matches = list(_IMPACT_HEADING_RE.finditer(text))
    if len(matches) < 2:
        return None

    classified: list[tuple[re.Match[str], str]] = []
    for match in matches:
        bucket = _classify_heading(match.group(1))
        if bucket is None:
            return None
        classified.append((match, bucket))

    buckets: dict[str, str] = {}
    for i, (match, bucket) in enumerate(classified):
        end = classified[i + 1][0].start() if i + 1 < len(classified) else len(text)
        body = text[match.end() : end].strip()
        # If multiple headings share a bucket, append.
        if bucket in buckets:
            buckets[bucket] = f"{buckets[bucket]}\n\n{body}"
        else:
            buckets[bucket] = body

    if len(buckets) < 2:
        return None

    prologue = text[: classified[0][0].start()].strip()
    return prologue, buckets, ""  # epilogue intentionally folded into last bucket


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
            soup,
            container,
            data.get("executive_summary"),
            "Executive Summary",
            icon="📋",
            as_markdown=True,
        )

        for key, heading, icon in _DIMENSIONS:
            self._render_dimension(soup, container, data.get(key), heading, icon)

        self.render_text_section(
            soup,
            container,
            data.get("synthesis"),
            "Synthesis",
            icon="🎯",
            as_markdown=True,
        )

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
            self._render_impact(soup, section, impact)

        sources = dim.get("sources") or []
        if sources:
            self._render_sources(soup, section, sources)

        container.append(section)

    def _render_impact(self, soup: BeautifulSoup, section: Any, impact: str) -> None:
        """Render impact text either as 3 categorical cards or as flat markdown."""
        split = _split_impact_into_buckets(impact)
        if split is None:
            self.render_markdown_block(section, impact)
            return

        prologue, buckets, _ = split
        if prologue:
            self.render_markdown_block(section, prologue)

        grid = soup.new_tag("div", **{"class": "cards-grid impact-grid"})  # type: ignore[arg-type]
        for bucket in _IMPACT_BUCKETS:
            key, icon, label = bucket[0], bucket[1], bucket[2]
            body = buckets.get(key)
            if not body:
                continue
            card = soup.new_tag("div", **{"class": key})  # type: ignore[arg-type]
            h4 = soup.new_tag("h4")
            h4.string = f"{icon} {label}"
            card.append(h4)
            self.render_markdown_block(card, body)
            grid.append(card)
        section.append(grid)

    def _render_sources(self, soup: BeautifulSoup, section: Any, sources: list[Any]) -> None:
        """Render sources inside a collapsible <details> for visual breathing room."""
        details = soup.new_tag("details", **{"class": "sources-details"})  # type: ignore[arg-type]
        summary_tag = soup.new_tag("summary")
        summary_tag.string = f"Sources ({len(sources)})"
        details.append(summary_tag)

        ul = soup.new_tag("ul")
        for src in sources:
            li = soup.new_tag("li")
            src_text = str(src).strip()
            url_match = re.search(r"https?://\S+", src_text)
            if url_match:
                url = url_match.group(0).rstrip(".,);]")
                # Render the prefix text, then the link
                prefix = src_text[: url_match.start()].rstrip(" ,:")
                if prefix:
                    li.append(prefix + " ")
                a = soup.new_tag("a", href=url)
                a.string = url
                a.attrs["target"] = "_blank"
                a.attrs["rel"] = "noopener"
                li.append(a)
                suffix = src_text[url_match.start() + len(url_match.group(0)) :]
                if suffix:
                    li.append(suffix)
            else:
                li.string = src_text
            ul.append(li)
        details.append(ul)
        section.append(details)
