"""Parsing and JSON-repair utilities extracted from debug_utils.

Public API:
- parse_crewai_output
"""

from __future__ import annotations

import json
import os
import re
import time
from contextlib import suppress
from typing import Any

from loguru import logger
from pydantic import BaseModel


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
        return match.group(0).replace("\n", "\\n")

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
    repaired = re.sub(r'(\d+|true|false|null|"|})\s*({|\[|")', r"\1, \2", repaired)

    # Fix unquoted keys
    repaired = re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', repaired)

    # Fix single quotes used as string delimiters
    repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', repaired)
    repaired = re.sub(r":\s*'([^']*)'([,}])", r':"\1"\2', repaired)

    # Fix missing quotes around string values
    repaired = re.sub(r":\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])", r':"\1"\2', repaired)

    # Fix trailing commas in JSON objects and arrays
    repaired = re.sub(r",\s*}", "}", repaired)
    repaired = re.sub(r",\s*]", "]", repaired)

    # Fix missing commas between array elements or object properties
    repaired = re.sub(r'("[^"]*"|\d+|true|false|null)\s*(")', r"\1, \2", repaired)

    # Fix missing colons in object properties
    repaired = re.sub(r'"([^"]+)"\s+"([^"]+)"', r'"\1": "\2"', repaired)

    # Fix trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Fix missing commas between array/object elements
    repaired = re.sub(r"}\s*{", r"}, {", repaired)
    repaired = re.sub(r"]\s*\[", r"], [", repaired)

    # Count and fix unmatched braces/brackets
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

    # Handle case where JSON ends with a comma
    repaired = repaired.rstrip()
    if repaired.endswith(","):
        repaired = repaired[:-1]

    # Remove escaped quotes that shouldn't be escaped
    return re.sub(r'\\"', '"', repaired)


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


def parse_crewai_output[T: BaseModel](
    report_content: Any, model_class: type[T], inputs: dict | None = None
) -> T:
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
                if line.strip().startswith("{") or line.strip().startswith("["):
                    start_index = i
                    break
            cleaned_json = "\n".join(content_lines[start_index:])

    # Strip preamble text before JSON (e.g., "Thought:", "Final Answer:", etc.)
    # Find the first occurrence of { or [ which indicates JSON start
    json_start_brace = cleaned_json.find("{")
    json_start_bracket = cleaned_json.find("[")

    if json_start_brace == -1 and json_start_bracket == -1:
        # No JSON content found
        inputs_info = f" Inputs were: {inputs}" if inputs else ""
        raise ValueError(
            f"{model_class.__name__} crew produced no valid JSON. "
            f"Raw output started with: {cleaned_json[:100]}...{inputs_info}"
        )

    # Determine which comes first
    if json_start_brace == -1:
        json_start = json_start_bracket
    elif json_start_bracket == -1:
        json_start = json_start_brace
    else:
        json_start = min(json_start_brace, json_start_bracket)

    # Strip any preamble text before the JSON
    if json_start > 0:
        preamble = cleaned_json[:json_start].strip()
        if preamble:
            logger.debug(f"Stripped preamble before JSON: {preamble[:100]}...")
        cleaned_json = cleaned_json[json_start:]

    # Also strip any trailing text after the JSON (find matching closing brace/bracket)
    def find_json_end(text: str) -> int:
        """Find the end of a JSON object/array by matching braces/brackets."""
        if not text:
            return 0
        first_char = text[0]
        if first_char == "{":
            open_char, close_char = "{", "}"
        elif first_char == "[":
            open_char, close_char = "[", "]"
        else:
            return len(text)

        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return i + 1
        return len(text)

    json_end = find_json_end(cleaned_json)
    if json_end < len(cleaned_json):
        trailing = cleaned_json[json_end:].strip()
        if trailing:
            logger.debug(f"Stripped trailing text after JSON: {trailing[:100]}...")
        cleaned_json = cleaned_json[:json_end]

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

                def normalize_metric_type(v: str) -> str:  # type: ignore[misc]
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
        with suppress(Exception):
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(cleaned_json)
            logger.info(f"Saved problematic JSON to {debug_file}")

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
            with suppress(Exception):
                with open(repair_debug_file, "w", encoding="utf-8") as f:
                    f.write(repaired_json)
                logger.info(f"Saved repair attempt to {repair_debug_file}")

            raise ValueError(
                f"Invalid JSON output from {model_class.__name__} crew. Original error: {e}. Repair failed: {repair_error}"
            )
        except Exception as repair_error:
            logger.error(f"JSON repair attempt failed with unexpected error: {repair_error}")
            raise ValueError(f"Invalid JSON output from {model_class.__name__} crew: {e}")
    except Exception as e:
        logger.error(f"Failed to validate {model_class.__name__} model: {e}")
        raise ValueError(f"Invalid {model_class.__name__} data structure: {e}")
