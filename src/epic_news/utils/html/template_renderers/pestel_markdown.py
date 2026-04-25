"""Pure helper rendering a PestelReport as structured Markdown.

PESTEL is the only crew that ships a Markdown report (chosen as the sole
output format for this analysis). All other crews continue to use the
HTML rendering pipeline.
"""

from __future__ import annotations

from epic_news.models.crews.pestel_report import PestelDimension, PestelReport


def _render_dimension(heading: str, dim: PestelDimension) -> list[str]:
    parts = [
        "",
        heading,
        "",
        f"**Summary**: {dim.summary}",
        "",
        "**Key factors**:",
    ]
    parts.extend([f"- {factor}" for factor in dim.key_factors] or ["- _(none identified)_"])
    parts.extend(["", f"**Impact**: {dim.impact_analysis}"])
    if dim.sources:
        parts.extend(["", "**Sources**:"])
        parts.extend(f"- {src}" for src in dim.sources)
    return parts


def pestel_to_markdown(report: PestelReport) -> str:
    """Render a PestelReport as a deterministic Markdown document."""
    sections = [
        ("## 🏛️ Political", report.political),
        ("## 💰 Economic", report.economic),
        ("## 👥 Social", report.social),
        ("## 💻 Technological", report.technological),
        ("## 🌍 Environmental", report.environmental),
        ("## ⚖️ Legal", report.legal),
    ]
    parts: list[str] = [
        f"# PESTEL Analysis — {report.topic}",
        f"_Generated: {report.generated_at}_",
        "",
        "## Executive Summary",
        "",
        report.executive_summary,
    ]
    for heading, dim in sections:
        parts.extend(_render_dimension(heading, dim))
    parts.extend(["", "## 🎯 Synthesis", "", report.synthesis, ""])
    return "\n".join(parts)
