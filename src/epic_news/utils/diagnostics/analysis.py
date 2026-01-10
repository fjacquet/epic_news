"""Analysis helpers for debugging CrewAI outputs.

Public API:
- analyze_crewai_output
- log_state_keys
"""

from __future__ import annotations

from typing import Any

from loguru import logger


def log_state_keys(state_data: dict[str, Any], filter_keywords: list | None = None) -> None:
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
        analysis["data_types"][key] = type(value).__name__  # type: ignore[index]

        # Check for task outputs
        if isinstance(value, dict):
            if "pydantic" in value:
                analysis["has_pydantic"] = True
                analysis["task_outputs"][key] = {  # type: ignore[index]
                    "type": "pydantic",
                    "model": type(value["pydantic"]).__name__ if value["pydantic"] else None,
                }
            elif "raw" in value:
                analysis["has_raw"] = True
                preview = str(value["raw"]) if value["raw"] is not None else ""
                analysis["task_outputs"][key] = {  # type: ignore[index]
                    "type": "raw",
                    "content_preview": (preview[:100] + "...") if len(preview) > 100 else preview,
                }

    logger.info(f"📊 CrewAI Analysis for {crew_name}: {analysis}")
    return analysis
