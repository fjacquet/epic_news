"""Debug utilities for Epic News CrewAI system."""

import json
import os
import time
from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel

from epic_news.utils.directory_utils import ensure_output_directory

# logger = logging.getLogger(__name__)


def _attempt_json_repair(json_str: str) -> str:
    """
    Attempt to repair malformed JSON with comprehensive fixes for LLM-generated content.

    Args:
        json_str: The potentially malformed JSON string

    Returns:
        str: Repaired JSON string
    """
    import re

    repaired = json_str.strip()

    # 1. Fix common LLM JSON issues
    # Remove any leading/trailing non-JSON content
    if not repaired.startswith(("{", "[")):
        # Find first { or [
        start_match = re.search(r"[{\[]", repaired)
        if start_match:
            repaired = repaired[start_match.start() :]

    # 2. Fix missing colons after keys (common LLM error)
    # Pattern: "key" value -> "key": value
    repaired = re.sub(r'"([^"]+)"\s+(["{\d])', r'"\1": \2', repaired)

    # 3. Fix missing quotes around keys (but preserve already quoted keys)
    # Pattern: key: -> "key": (but not "key":)
    repaired = re.sub(r'(?<!["])\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', repaired)

    # 4. Fix missing quotes around string values (more precise)
    # Pattern: : word, -> : "word", (but not numbers, booleans, or already quoted)
    repaired = re.sub(r":\s*([a-zA-Z][a-zA-Z0-9\s]*?)(?=\s*[,}\]])", r': "\1"', repaired)

    # 4b. Fix missing colons in object properties
    # Pattern: "key" "value" -> "key": "value"
    repaired = re.sub(r'"([^"]+)"\s+"([^"]+)"', r'"\1": "\2"', repaired)

    # 5. Fix trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # 6. Fix missing commas between array/object elements
    # Pattern: } { -> }, {
    repaired = re.sub(r"}\s*{", r"}, {", repaired)
    repaired = re.sub(r"\]\s*\[", r"], [", repaired)

    # 7. Count and fix unmatched braces/brackets
    open_braces = repaired.count("{")
    close_braces = repaired.count("}")
    open_brackets = repaired.count("[")
    close_brackets = repaired.count("]")

    # Add missing closing braces
    if open_braces > close_braces:
        missing_braces = open_braces - close_braces
        repaired += "}" * missing_braces

    # Add missing closing brackets

    if open_brackets > close_brackets:
        missing_brackets = open_brackets - close_brackets
        repaired += "]" * missing_brackets

    # 8. Handle case where JSON ends with a comma
    repaired = repaired.rstrip()
    if repaired.endswith(","):
        repaired = repaired[:-1]

    # 9. Fix double quotes issues
    # Remove escaped quotes that shouldn't be escaped
    return re.sub(r'\\"', '"', repaired)


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


def _transform_holiday_planner_data(parsed_data: dict) -> dict:
    """Helper function to transform HolidayPlannerReport data."""
    # Convert URL strings to Source objects
    if "sources" in parsed_data:
        sources = parsed_data["sources"]
        if sources and isinstance(sources, list):
            converted_sources = []
            for source in sources:
                if isinstance(source, str):  # URL string
                    converted_sources.append(
                        {
                            "title": source.split("/")[-1] or "Source",
                            "url": source,
                            "type": "reference",
                        }
                    )
                elif isinstance(source, dict):
                    converted_sources.append(source)
            parsed_data["sources"] = converted_sources

    # Handle French-to-English field mapping for itinerary
    if "itinerary" in parsed_data and isinstance(parsed_data["itinerary"], list):
        for day_item in parsed_data["itinerary"]:
            if isinstance(day_item, dict):
                if "jour" in day_item and "day" not in day_item:
                    jour_text = day_item["jour"]
                    if "Jour" in jour_text:
                        day_num = jour_text.split()[1] if len(jour_text.split()) > 1 else "1"
                        day_item["day"] = int(day_num.replace("-", "").strip())
                    del day_item["jour"]
                if "date" not in day_item and "jour" in day_item:
                    jour_text = day_item["jour"]
                    parts = jour_text.split("-")
                    day_item["date"] = parts[1].strip() if len(parts) > 1 else "TBD"

    # Handle French-to-English field mapping for accommodations
    if "accommodations" in parsed_data and isinstance(parsed_data["accommodations"], list):
        for accommodation in parsed_data["accommodations"]:
            if isinstance(accommodation, dict):
                if "nom" in accommodation and "name" not in accommodation:
                    accommodation["name"] = accommodation["nom"]
                    del accommodation["nom"]
                if "adresse" in accommodation and "address" not in accommodation:
                    accommodation["address"] = accommodation["adresse"]
                    del accommodation["adresse"]
                if "address" not in accommodation:
                    accommodation["address"] = "Address not specified"
                if "description" not in accommodation:
                    accommodation["description"] = accommodation.get("name", "Accommodation option")
    return parsed_data


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

        # $Special handling for BookSummaryReport: coerce table_of_contents IDs to strings
        if model_class.__name__ == "BookSummaryReport" and "table_of_contents" in parsed_data:
            for entry in parsed_data["table_of_contents"]:
                if "id" in entry and not isinstance(entry["id"], str):
                    entry["id"] = str(entry["id"])

        # $Special handling for HolidayPlannerReport: robustly handle day/jour fields
        if model_class.__name__ == "HolidayPlannerReport" and "itinerary" in parsed_data:
            for day in parsed_data["itinerary"]:
                # Handle 'day' or 'jour' fields that may be int or str
                for key in ["day", "jour"]:
                    if key in day and not isinstance(day[key], str):
                        day[key] = str(day[key])
                # If 'date' is present and not a string, coerce to string
                if "date" in day and not isinstance(day["date"], str):
                    day["date"] = str(day["date"])
                # If 'activities' is present, ensure it's a list
                if "activities" in day and not isinstance(day["activities"], list):
                    day["activities"] = [day["activities"]]
                # If any string operation is needed, always check type
                if "jour" in day:
                    jour_text = day["jour"]
                    if isinstance(jour_text, str) and "Jour" in jour_text:
                        pass  # safe to do string ops

        # $Special handling for HolidayPlannerReport: comprehensive data transformation
        if model_class.__name__ == "HolidayPlannerReport":
            parsed_data = _transform_holiday_planner_data(parsed_data)

        return model_class.model_validate(parsed_data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed at line {e.lineno}, column {e.colno}: {e.msg}")
        logger.error(f"Error position (char {e.pos}): '{cleaned_json[max(0, e.pos - 20) : e.pos + 20]}'")

        # Save problematic JSON for debugging
        debug_file = f"debug/failed_json_{model_class.__name__.lower()}_{int(time.time())}.json"
        os.makedirs("debug", exist_ok=True)
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(cleaned_json)
            logger.info(f"Saved problematic JSON to {debug_file}")
        except Exception:
            pass  # Don't fail if we can't save debug file

        # Try comprehensive JSON repair
        try:
            logger.info("Attempting comprehensive JSON repair...")
            repaired_json = _attempt_json_repair(cleaned_json)

            # Log what repairs were attempted
            if repaired_json != cleaned_json:
                logger.info(f"JSON repair made {len(repaired_json) - len(cleaned_json)} character changes")

            parsed_data = json.loads(repaired_json)

            # Apply same special handling as above
            if model_class.__name__ == "BookSummaryReport" and "table_of_contents" in parsed_data:
                for entry in parsed_data["table_of_contents"]:
                    if "id" in entry and not isinstance(entry["id"], str):
                        entry["id"] = str(entry["id"])

            # Apply same HolidayPlannerReport handling as above
            if model_class.__name__ == "HolidayPlannerReport":
                parsed_data = _transform_holiday_planner_data(parsed_data)

            logger.info("Successfully repaired and parsed JSON")
            return model_class.model_validate(parsed_data)
        except json.JSONDecodeError as repair_error:
            logger.error(
                f"JSON repair failed at line {repair_error.lineno}, column {repair_error.colno}: {repair_error.msg}"
            )
            logger.error(
                f"Repair error position (char {repair_error.pos}): '{repaired_json[max(0, repair_error.pos - 20) : repair_error.pos + 20]}'"
            )

            # Save repaired JSON attempt for debugging
            repair_debug_file = f"debug/repair_attempt_{model_class.__name__.lower()}_{int(time.time())}.json"
            try:
                with open(repair_debug_file, "w", encoding="utf-8") as f:
                    f.write(repaired_json)
                logger.info(f"Saved repair attempt to {repair_debug_file}")
            except Exception:
                pass

            raise ValueError(
                f"Invalid JSON output from {model_class.__name__} crew. Original error: {e}. Repair failed: {repair_error}"
            )
        except Exception as repair_error:
            logger.error(f"JSON repair attempt failed with unexpected error: {repair_error}")
            raise ValueError(f"Invalid JSON output from {model_class.__name__} crew: {e}")
    except Exception as e:
        logger.error(f"Failed to validate {model_class.__name__} model: {e}")
        raise ValueError(f"Invalid {model_class.__name__} data structure: {e}")
