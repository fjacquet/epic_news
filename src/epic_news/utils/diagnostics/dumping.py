"""State dumping and serialization utilities extracted from debug_utils.

Public API:
- dump_crewai_state
- make_serializable
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from loguru import logger

from epic_news.utils.directory_utils import ensure_output_directory


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
    if os.environ.get("DEBUG_STATE", "false").lower() != "true":
        return ""
    try:
        # Create debug directory if it doesn't exist
        ensure_output_directory(debug_dir)

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
