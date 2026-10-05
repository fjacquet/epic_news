"""Parse a CrewAI output into a Pydantic model.

Model-specific fixes live on the models as `mode="before"` validators; this module
only finds the JSON (repairing it with json_repair when it is not valid) and validates.

Public API:
- parse_crewai_output
"""

import json
import re
from typing import Any

import json_repair
from loguru import logger
from pydantic import BaseModel, ValidationError

_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
_SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def _sanitize(text: str) -> str:
    """Drop thousand separators inside numbers (1,234,567) and straighten smart quotes."""
    return _THOUSANDS.sub("", text).translate(_SMART_QUOTES)


def _load(text: str) -> Any:
    """First JSON value in `text`; json_repair only when it is not valid JSON.

    raw_decode stops after the first value, so prose after it (citations like [1],
    markdown, a closing fence) is ignored; json_repair would read it as more JSON.
    """
    try:
        return json.JSONDecoder().raw_decode(text)[0]
    except ValueError:
        return json_repair.loads(text)


def parse_crewai_output[T: BaseModel](
    report_content: Any, model_class: type[T], inputs: dict | None = None
) -> T:
    """Return `model_class` from a CrewAI output (pydantic passthrough, or repaired raw JSON).

    Raises:
        ValueError: empty output, no JSON, unrepairable JSON, or data that does not fit the model.
    """
    name = model_class.__name__
    output = getattr(report_content, "output", None)
    if isinstance(output, model_class):
        return output

    raw = (getattr(report_content, "raw", "") or "").strip()
    if not raw:
        inputs_info = f" Inputs were: {inputs}" if inputs else ""
        raise ValueError(
            f"{name} crew produced no output. Check input variables and crew configuration.{inputs_info}"
        )

    match = re.search(r"[\[{]", raw)
    if match is None:
        raise ValueError(f"{name} crew produced no valid JSON. Raw output started with: {raw[:200]!r}")
    if match.start():
        logger.debug(f"Skipping {match.start()} characters before the JSON in {name} output")

    try:
        data = _load(_sanitize(raw[match.start() :]))
    except Exception as exc:  # noqa: BLE001 - any repair failure is reported the same way
        raise ValueError(f"Invalid JSON output from {name} crew: {exc}") from exc
    if not isinstance(data, dict | list):
        raise ValueError(f"Invalid JSON output from {name} crew: could not read a JSON object")

    try:
        return model_class.model_validate(data)
    except (ValidationError, TypeError, AttributeError) as exc:  # before-validators may raise these
        raise ValueError(f"Invalid {name} data structure: {exc}") from exc
