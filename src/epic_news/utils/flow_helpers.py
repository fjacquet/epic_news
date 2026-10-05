"""Pure helpers factoring repeated boilerplate in ReceptionFlow generate_* methods.

load_or_parse_model: try deterministic JSON load → model_validate, fallback to
parse_crewai_output for robust JSON extraction from crew raw output.
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ValidationError

from epic_news.utils.diagnostics.parsing import parse_crewai_output


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
