"""Debug utilities for Epic News CrewAI system."""

import json
import logging
import os
import time
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def dump_crewai_state(state_data: dict[str, Any], crew_name: str, debug_dir: str = "debug") -> str:
    """
    Dump CrewAI state to a JSON file for debugging purposes.

    Args:
        state_data: The state data dictionary to dump
        crew_name: Name of the crew (used in filename)
        debug_dir: Directory to save debug files (default: "debug")

    Returns:
        str: Path to the created debug file, or empty string if failed
    """
    try:
        # Create debug directory if it doesn't exist
        os.makedirs(debug_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = int(time.time())
        debug_file = os.path.join(debug_dir, f"crewai_state_{crew_name.lower()}_{timestamp}.json")

        # Convert state_data to JSON-serializable format
        serializable_state = make_serializable(state_data)

        # Write to file with proper encoding
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, indent=2, ensure_ascii=False)

        logger.info(f"🐛 CrewAI state dumped to: {debug_file}")
        return debug_file

    except Exception as e:
        logger.warning(f"⚠️ Failed to dump state to JSON: {e}")
        return ""


def make_serializable(obj: Any) -> Any:
    """
    Convert any object to a JSON-serializable format.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable representation of the object
    """
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        # Pydantic models
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        # Custom objects with attributes
        return {k: make_serializable(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list | tuple):
        # Lists and tuples
        return [make_serializable(item) for item in obj]
    if isinstance(obj, dict):
        # Dictionaries
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, str | int | float | bool):
        # Basic types
        return obj
    # Fallback to string representation
    return str(obj)


def log_state_keys(state_data: dict[str, Any], filter_keywords: list = None) -> None:
    """
    Log state data keys, optionally filtering by keywords.

    Args:
        state_data: The state data dictionary
        filter_keywords: Optional list of keywords to filter keys (case-insensitive)
    """
    logger.info(f"🔍 State data keys: {list(state_data.keys())}")

    if filter_keywords:
        for key in state_data:
            if any(keyword.lower() in key.lower() for keyword in filter_keywords):
                logger.info(f"📋 Found filtered data - {key}: {state_data[key]}")


def analyze_crewai_output(state_data: dict[str, Any], crew_name: str) -> dict[str, Any]:
    """
    Analyze CrewAI output structure and return summary information.

    Args:
        state_data: The state data dictionary
        crew_name: Name of the crew being analyzed

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "crew_name": crew_name,
        "total_keys": len(state_data),
        "task_outputs": {},
        "data_types": {},
        "has_pydantic": False,
        "has_raw": False,
    }

    for key, value in state_data.items():
        # Analyze data types
        analysis["data_types"][key] = type(value).__name__

        # Check for task outputs
        if isinstance(value, dict):
            if "pydantic" in value:
                analysis["has_pydantic"] = True
                analysis["task_outputs"][key] = {
                    "type": "pydantic",
                    "model": type(value["pydantic"]).__name__ if value["pydantic"] else None,
                }
            elif "raw" in value:
                analysis["has_raw"] = True
                analysis["task_outputs"][key] = {
                    "type": "raw",
                    "content_preview": str(value["raw"])[:100] + "..."
                    if len(str(value["raw"])) > 100
                    else str(value["raw"]),
                }

    logger.info(f"📊 CrewAI Analysis for {crew_name}: {analysis}")
    return analysis


T = TypeVar("T", bound=BaseModel)


def parse_crewai_output(report_content: Any, model_class: type[T], inputs: dict = None) -> T:
    """
    Parse CrewAI output to a Pydantic model with robust JSON cleaning.

    Handles common CrewAI output patterns:
    - Direct pydantic output in report_content.output
    - JSON wrapped in triple backticks in report_content.raw
    - Empty or malformed output with clear error messages

    Args:
        report_content: CrewAI output object
        model_class: Pydantic model class to validate against
        inputs: Optional inputs dict for error reporting

    Returns:
        Validated Pydantic model instance

    Raises:
        ValueError: If output is empty or invalid
    """
    # Check if we have direct pydantic output
    if hasattr(report_content, "output") and isinstance(report_content.output, model_class):
        return report_content.output

    # Extract and clean raw JSON output
    raw_json = getattr(report_content, "raw", "")
    if not raw_json or not raw_json.strip():
        inputs_info = f" Inputs were: {inputs}" if inputs else ""
        raise ValueError(
            f"{model_class.__name__} crew produced no output. "
            f"Check input variables and crew configuration.{inputs_info}"
        )

    # Remove triple backticks if present
    cleaned_json = raw_json.strip()
    if cleaned_json.startswith("```") and cleaned_json.endswith("```"):
        lines = cleaned_json.split("\n")
        if len(lines) > 2:
            cleaned_json = "\n".join(lines[1:-1])

    # Parse and validate JSON
    try:
        parsed_data = json.loads(cleaned_json)

        # $$$Special handling for BookSummaryReport: coerce table_of_contents IDs to strings
        if model_class.__name__ == "BookSummaryReport" and "table_of_contents" in parsed_data:
            for entry in parsed_data["table_of_contents"]:
                if "id" in entry and not isinstance(entry["id"], str):
                    entry["id"] = str(entry["id"])

        return model_class.model_validate(parsed_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON. Raw output was: {raw_json[:500]}...")
        raise ValueError(f"Invalid JSON output from {model_class.__name__} crew: {e}")
    except Exception as e:
        logger.error(f"Failed to validate {model_class.__name__} model: {e}")
        raise ValueError(f"Invalid {model_class.__name__} data structure: {e}")
