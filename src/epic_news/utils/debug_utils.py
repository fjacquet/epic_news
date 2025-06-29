"""Debug utilities for Epic News CrewAI system."""

import json
import logging
import os
import time
from typing import Any

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
