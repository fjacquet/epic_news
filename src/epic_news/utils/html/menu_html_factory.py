"""
Factory function to convert a WeeklyMenuPlan (or compatible dict) to HTML using TemplateManager.
Follows the deterministic HTML rendering pattern used across the epic_news project, similar to
`daily_news_html_factory.daily_news_to_html`.
"""

from __future__ import annotations

import os
from typing import Any

from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.utils.debug_utils import parse_crewai_output
from epic_news.utils.directory_utils import ensure_output_directory
from epic_news.utils.html.template_manager import TemplateManager

# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def menu_to_html(menu_plan: Any, html_file: str | None = None, title: str | None = None) -> str:  # noqa: ANN401
    """Convert a *validated* WeeklyMenuPlan (Pydantic model, CrewOutput, or dict) to HTML.

    Args:
        menu_plan: WeeklyMenuPlan instance, CrewOutput, or compatible dict.
        html_file: Optional path where the resulting HTML will be written.
        title: Optional title override for the report.

    Returns:
        The rendered HTML string.
    """

    # ---------------------------------------------------------------------
    # 1. Parse / normalise the input so that we always work with a *dict*.
    # ---------------------------------------------------------------------
    if hasattr(menu_plan, "raw"):
        # CrewOutput coming directly from CrewAI → parse with utility helper
        content_data = parse_crewai_output(menu_plan, WeeklyMenuPlan)
    elif isinstance(menu_plan, WeeklyMenuPlan):
        content_data = menu_plan.model_dump()
    elif hasattr(menu_plan, "model_dump"):
        # Another pydantic model compatible with WeeklyMenuPlan
        content_data = menu_plan.model_dump()
    elif isinstance(menu_plan, dict):
        content_data = menu_plan
    else:
        raise ValueError(f"Unsupported `menu_plan` type for HTML rendering: {type(menu_plan).__name__}")

    # Map field names for renderer compatibility
    if "daily_menus" in content_data and "daily_plans" not in content_data:
        content_data["daily_plans"] = content_data["daily_menus"]

    # Inject optional title if provided – renderer will use it as-is
    if title:
        content_data["title"] = title

    # ---------------------------------------------------------------------
    # 2. Render via TemplateManager which will delegate to MenuRenderer.
    # ---------------------------------------------------------------------
    template_manager = TemplateManager()
    html = template_manager.render_report("MENU", content_data)

    # ---------------------------------------------------------------------
    # 3. Persist to disk if requested.
    # ---------------------------------------------------------------------
    if html_file:
        ensure_output_directory(os.path.dirname(html_file))
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

    return html
