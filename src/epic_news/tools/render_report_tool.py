"""RenderReportTool

Renders a standardized HTML report using a Jinja2 template. This tool ensures a
consistent look-and-feel across all crews and guarantees the output is a single
valid HTML5 document ready for downstream conversion to PDF or storage.

Inputs (passed via **kwargs):
    title (str):      Report title.
    sections (list):  Each item is a dict with `heading` and `content` keys.
    images (list):    Optional list of dicts with `src`, `alt`, `caption`.
    citations (list): Optional list of citation strings or HTML links.

Returns:
    str: Rendered HTML string.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
from pydantic import BaseModel, PrivateAttr

from src.epic_news.models.report_models import RenderReportToolSchema

# Try both possible template directories
_TEMPLATES_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "templates"
_TEMPLATES_SRC = Path(__file__).resolve().parent.parent / "templates"

# Use the first directory that exists
_TEMPLATE_DIR = _TEMPLATES_SRC if _TEMPLATES_SRC.exists() else _TEMPLATES_ROOT


class RenderReportTool(BaseTool):
    """Tool for rendering standardized HTML reports."""

    # Private attributes for Jinja2 environment and template directory
    _env: Environment = PrivateAttr()
    _template_dir: Path = PrivateAttr()

    name: str = "RenderReportTool"
    description: str = (
        "Render an HTML report using the shared Jinja2 template. "
        "Requires kwargs: title, sections (list of dict), and optional images, citations."
    )
    args_schema: type[BaseModel] = RenderReportToolSchema

    def __init__(self, template_dir: str | os.PathLike | None = None):
        """Initialize the tool and set up the Jinja2 environment."""
        super().__init__()
        if template_dir:
            self._template_dir = Path(template_dir)
        else:
            # Robustly determine the project root and then the templates directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            self._template_dir = Path(os.path.join(project_root, "templates"))

        if not self._template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self._template_dir}")

        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)), autoescape=select_autoescape(["html", "xml"])
        )
        self._env.filters["date"] = RenderReportTool._format_date

    # ---------------------------------------------------------------------
    # Jinja2 filter
    # ---------------------------------------------------------------------
    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format an ISO date string to a more readable format."""
        if not date_str:
            return ""
        try:
            # Handles both date and datetime ISO strings
            date_obj = _dt.datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            return date_obj.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return date_str  # Return original string if parsing fails

    # ---------------------------------------------------------------------
    # Internal render helper
    # ---------------------------------------------------------------------
    def _render(self, title: str, sections: list[dict[str, Any]], **kwargs: Any) -> str:
        """Render report_template.html with supplied context."""
        template = self._env.get_template("report_template.html")
        context = {
            "title": title,
            "date": _dt.date.today().isoformat(),
            "sections": sections,
            "images": kwargs.get("images", []),
            "citations": kwargs.get("citations", []),
        }
        html: str = template.render(**context)
        # Validate HTML; raise ValueError if invalid
        from epic_news.utils.validate_html import validate_html

        validate_html(html)
        return html

    # ------------------------------------------------------------------
    # CrewAI sync / async entry-points
    # ------------------------------------------------------------------
    def _run(self, *args: Any, **kwargs: Any) -> str:  # noqa: D401,E252
        # Accept positional overload: (title, sections, images=None, citations=None)
        if args:
            title = args[0]
            sections = args[1] if len(args) > 1 else []
            kwargs.setdefault("images", args[2] if len(args) > 2 else [])
            kwargs.setdefault("citations", args[3] if len(args) > 3 else [])
        else:
            title = kwargs.pop("title")
            sections = kwargs.pop("sections", [])
        return self._render(title=title, sections=sections, **kwargs)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # noqa: D401,E252
        return self._run(*args, **kwargs)
