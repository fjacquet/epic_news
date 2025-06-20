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
from typing import Any, Dict, List

from crewai_tools import BaseTool  # type: ignore
from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore

_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "templates"
).resolve()


class RenderReportTool(BaseTool):
    """Tool for rendering standardized HTML reports."""

    name: str = "RenderReportTool"
    description: str = (
        "Render an HTML report using the shared Jinja2 template. "
        "Requires kwargs: title, sections (list of dict), and optional images, citations."
    )

    def __init__(self, template_dir: str | os.PathLike | None = None):
        super().__init__()
        self.template_dir: Path = Path(template_dir) if template_dir else _TEMPLATE_DIR
        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    # ---------------------------------------------------------------------
    # Internal render helper
    # ---------------------------------------------------------------------
    def _render(self, title: str, sections: List[Dict[str, Any]], **kwargs: Any) -> str:
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
