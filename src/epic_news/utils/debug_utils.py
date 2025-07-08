"""Debug utilities for Epic News CrewAI system."""

import json
import os
import re
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
    repaired = json_str

    # Replace smart quotes with straight quotes
    repaired = repaired.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # Escape unescaped newlines within strings
    def escape_newlines(match):
        return match.group(0).replace('\n', '\\n')

    repaired = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', escape_newlines, repaired)


    # Try to detect and fix common JSON errors by line
    lines = repaired.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        # Fix missing commas at the end of lines
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if (
                (
                    line.strip().endswith(('"', "'", "}", "]", "true", "false", "null"))
                    or line.strip().rstrip("0123456789").strip() != line.strip()
                )
                and next_line.startswith(('"', "'", "{", "["))
                and not line.strip().endswith((",", "{", "[", ":"))
            ):
                line = line.rstrip() + ","

        fixed_lines.append(line.strip())

    # Rejoin the fixed lines
    repaired = "\n".join(fixed_lines)

    # Fix common issues
    repaired = repaired.replace("'", '"')
    repaired = repaired.replace("True", "true")
    repaired = repaired.replace("False", "false")
    repaired = repaired.replace("None", "null")
    repaired = repaired.replace("NaN", "null")
    repaired = repaired.replace("Infinity", "null")
    repaired = repaired.replace("-Infinity", "null")

    # Fix trailing commas in arrays and objects
    repaired = re.sub(r",\s*}", "}", repaired)
    repaired = re.sub(r",\s*]", "]", repaired)

    # Fix missing commas between elements
    repaired = re.sub(r'(\d+|true|false|null|"|})\s*({|\[|")', r'\1, \2', repaired)

    # Fix unquoted keys
    repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)

    # Fix single quotes used as string delimiters
    repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', repaired)
    repaired = re.sub(r":\s*'([^']*)'([,}])", r':"\1"\2', repaired)

    # Fix missing quotes around string values
    repaired = re.sub(r":\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])", r':"\1"\2', repaired)

    # Fix trailing commas in JSON objects and arrays
    repaired = re.sub(r",\s*}", "}", repaired)
    repaired = re.sub(r",\s*]", "]", repaired)

    # Fix missing commas between array elements or object properties
    repaired = re.sub(r'("[^"]*"|\d+|true|false|null)\s*(")', r'\1, \2', repaired)

    # 4b. Fix missing colons in object properties
    # Pattern: "key" "value" -> "key": "value"
    repaired = re.sub(r'"([^"]+)"\s+"([^"]+)"', r'"\1": "\2"', repaired)

    # 5. Fix trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r'\1', repaired)

    # 6. Fix missing commas between array/object elements
    # Pattern: } { -> }, {
    repaired = re.sub(r"}\s*{", r"}, {", repaired)
    repaired = re.sub(r"]\s*\[", r"], [", repaired)

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
            # Extract content, assuming first line might be a language hint (e.g., "json")
            content_lines = lines[1:-1]
            # Find the start of the JSON content
            start_index = 0
            for i, line in enumerate(content_lines):
                if line.strip().startswith('{') or line.strip().startswith('['):
                    start_index = i
                    break
            cleaned_json = "\n".join(content_lines[start_index:])


        # --- Sanitize common issues -------------------------------------------------

    def _sanitize_json(text: str) -> str:
        """Fix common JSON issues like 1,000 style numbers and smart quotes."""
        # Remove commas used as thousand separators inside numbers (1,234,567)
        text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)
        # Replace smart quotes with straight quotes
        return text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    cleaned_json = _sanitize_json(cleaned_json)

    # Parse and validate JSON
    try:
        parsed_data = json.loads(cleaned_json)

        # $Special handling for BookSummaryReport: coerce table_of_contents IDs to strings
        if model_class.__name__ == "BookSummaryReport" and "table_of_contents" in parsed_data:
            for entry in parsed_data["table_of_contents"]:
                if "id" in entry and not isinstance(entry["id"], str):
                    entry["id"] = str(entry["id"])

                # $Special handling for SalesProspectingReport: clean metrics list
        if model_class.__name__ == "SalesProspectingReport" and "sales_metrics" in parsed_data:
            try:
                from epic_news.utils.data_normalization import normalize_metric_type
            except ImportError:

                def normalize_metric_type(v: str):
                    return v

            metrics = parsed_data.get("sales_metrics", {}).get("metrics", [])
            cleaned_metrics = []
            for metric in metrics:
                # Normalize metric type synonyms
                m_type = metric.get("type")
                if m_type:
                    metric["type"] = normalize_metric_type(m_type)
                # Ensure metric has a proper value dict
                val_field = metric.get("value")
                if not isinstance(val_field, dict):
                    # numeric or string, wrap into dict
                    metric["value"] = {"value": val_field, "unit": "", "trend": "flat"}
                else:
                    if "value" not in val_field:
                        # Try to pick the first numeric entry as value
                        numeric_val = None
                        for v in val_field.values():
                            if isinstance(v, int | float):
                                numeric_val = v
                                break
                        if numeric_val is not None:
                            metric["value"] = {"value": numeric_val, "unit": "", "trend": "flat"}
                        else:
                            # skip metric if cannot determine value
                            continue
                cleaned_metrics.append(metric)
            parsed_data["sales_metrics"]["metrics"] = cleaned_metrics

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

        # $Special handling for SalesProspectingReport: ensure proper metric types and trend directions
        if model_class.__name__ == "SalesProspectingReport" and "sales_metrics" in parsed_data:
            from epic_news.utils.data_normalization import normalize_structured_data_report

            if "sales_metrics" in parsed_data:
                parsed_data["sales_metrics"] = normalize_structured_data_report(parsed_data["sales_metrics"])

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