"""Pure helpers factoring repeated boilerplate in ReceptionFlow generate_* methods.

Two module-level helpers:
- load_or_parse_model: try deterministic JSON load → model_validate, fallback to
  parse_crewai_output for robust JSON extraction from crew raw output.
- render_and_write_html: render via TemplateManager and persist to disk, creating
  the parent directory once (replaces inline os.makedirs usage).
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ValidationError

from epic_news.utils.diagnostics.parsing import parse_crewai_output
from epic_news.utils.html.template_manager import TemplateManager


def load_or_parse_model[T: BaseModel](
    json_path: str | Path,
    model_cls: type[T],
    fallback_output: object,
    inputs: dict | None = None,
    label: str = "",
) -> T:
    """Load a Pydantic model from a JSON file, falling back to CrewAI output parsing.

    Args:
        json_path: Path to the JSON file written by the crew's output_pydantic.
        model_cls: Pydantic model class to validate against.
        fallback_output: Raw crew output (used when JSON file is missing/invalid).
        inputs: Optional inputs dict forwarded to parse_crewai_output for error reporting.
        label: Human-readable label for log messages.

    Returns:
        Validated Pydantic model instance.
    """
    path = Path(json_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        model = model_cls.model_validate(data)
        logger.info(f"📄 Loaded {label or model_cls.__name__} model from {path}")
        return model
    except (OSError, json.JSONDecodeError, ValidationError):
        return parse_crewai_output(fallback_output, model_cls, inputs)


def render_and_write_html(
    selected_crew: str,
    model: BaseModel,
    html_path: str | Path,
) -> Path:
    """Render the model via TemplateManager and write the resulting HTML to disk.

    Args:
        selected_crew: Crew identifier used by TemplateManager for title/body routing.
        model: Pydantic model providing the content data via model_dump().
        html_path: Destination HTML file (parent directory created if missing).

    Returns:
        The final output path.
    """
    html = TemplateManager().render_report(
        selected_crew=selected_crew,
        content_data=model.model_dump(),
    )
    out = Path(html_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
