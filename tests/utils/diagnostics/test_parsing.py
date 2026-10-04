"""Unit tests for epic_news.utils.diagnostics.parsing.

Covers the public API (parse_crewai_output) and the private helper
function (_attempt_json_repair) that
implement the JSON cleaning/repair logic used to coerce noisy CrewAI
LLM output into validated Pydantic models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, Field

from epic_news.utils.diagnostics.parsing import (
    _attempt_json_repair,
    parse_crewai_output,
)


class FakeCrewOutput:
    """Minimal stand-in for CrewAI's CrewOutput/TaskOutput objects."""

    def __init__(self, raw: str = "", output: Any = None):
        self.raw = raw
        if output is not None:
            self.output = output


class SimpleModel(BaseModel):
    name: str
    value: int


# Local models named to match the special-case string checks inside
# parse_crewai_output (the code branches on model_class.__name__, not on
# type identity), kept intentionally permissive so we can isolate the
# parsing/transform logic without needing the full production schemas.
class BookSummaryReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    table_of_contents: list[dict[str, Any]] = Field(default_factory=list)


class SalesProspectingReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    sales_metrics: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# parse_crewai_output: happy paths
# ---------------------------------------------------------------------------


def test_direct_pydantic_output_passthrough():
    """If report_content.output is already an instance of model_class, return it as-is."""
    model = SimpleModel(name="a", value=1)
    fake = FakeCrewOutput(output=model)
    result = parse_crewai_output(fake, SimpleModel)
    assert result is model


def test_valid_json_raw_parses_directly():
    fake = FakeCrewOutput(raw=json.dumps({"name": "Bob", "value": 42}))
    result = parse_crewai_output(fake, SimpleModel)
    assert result == SimpleModel(name="Bob", value=42)


def test_json_wrapped_in_triple_backticks_with_language_hint():
    raw = '```json\n{"name": "Alice", "value": 7}\n```'
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SimpleModel)
    assert result == SimpleModel(name="Alice", value=7)


def test_preamble_and_trailing_text_are_stripped():
    raw = 'Thought: I will answer now.\nFinal Answer: {"name": "Carl", "value": 3} \nThanks!'
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SimpleModel)
    assert result == SimpleModel(name="Carl", value=3)


def test_thousand_separator_numbers_are_sanitized():
    raw = '{"name": "Numbers", "value": 1,234}'
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SimpleModel)
    assert result.value == 1234


def test_smart_quotes_in_raw_are_sanitized():
    raw = '{"name": “Quoted”, "value": 5}'
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SimpleModel)
    assert result == SimpleModel(name="Quoted", value=5)


# ---------------------------------------------------------------------------
# parse_crewai_output: failure / fallback paths
# ---------------------------------------------------------------------------


def test_empty_raw_raises_value_error():
    fake = FakeCrewOutput(raw="")
    with pytest.raises(ValueError, match="produced no output"):
        parse_crewai_output(fake, SimpleModel)


def test_whitespace_only_raw_raises_value_error():
    fake = FakeCrewOutput(raw="   \n  ")
    with pytest.raises(ValueError, match="produced no output"):
        parse_crewai_output(fake, SimpleModel)


def test_no_json_content_raises_value_error_with_inputs_info():
    fake = FakeCrewOutput(raw="just plain text, no json here")
    with pytest.raises(ValueError, match="produced no valid JSON") as excinfo:
        parse_crewai_output(fake, SimpleModel, inputs={"topic": "x"})
    assert "Inputs were: {'topic': 'x'}" in str(excinfo.value)


def test_array_root_fails_model_validation_with_dict_only_model(tmp_path: Path, monkeypatch):
    """A bare JSON array parses fine but a plain BaseModel needs a mapping, so
    validation fails with the generic "Invalid ... data structure" message."""
    monkeypatch.chdir(tmp_path)
    fake = FakeCrewOutput(raw="preamble [1, 2, 3] trailing")
    with pytest.raises(ValueError, match="Invalid SimpleModel data structure"):
        parse_crewai_output(fake, SimpleModel)


def test_valid_json_wrong_schema_raises_data_structure_error(tmp_path: Path, monkeypatch):
    """Well-formed JSON that is missing required fields raises through the
    generic `except Exception` branch, not the JSONDecodeError branch."""
    monkeypatch.chdir(tmp_path)
    fake = FakeCrewOutput(raw='{"name": "OnlyName"}')
    with pytest.raises(ValueError, match="Invalid SimpleModel data structure"):
        parse_crewai_output(fake, SimpleModel)


def test_malformed_json_is_repaired_but_still_fails_model_validation(tmp_path: Path, monkeypatch):
    """`{a: 1, b: 2,}` is invalid JSON (unquoted keys); the repair step fixes
    it into valid JSON `{"a": 1, "b": 2}`, but SimpleModel still requires
    name/value fields, so this raises via the *generic Exception* branch
    inside the repair handler (message uses the *original* decode error)."""
    monkeypatch.chdir(tmp_path)
    fake = FakeCrewOutput(raw="{a: 1, b: 2,}")
    with pytest.raises(
        ValueError,
        match=r"Invalid JSON output from SimpleModel crew: Expecting property name",
    ):
        parse_crewai_output(fake, SimpleModel)
    # Confirms the debug artifact for the original failure was written.
    assert list((tmp_path / "debug").glob("failed_json_simplemodel_*.json"))


def test_unrepairable_json_raises_with_both_original_and_repair_errors(tmp_path: Path, monkeypatch):
    """Severely malformed JSON that also fails to parse after repair raises
    via the JSONDecodeError branch, whose message embeds both errors."""
    monkeypatch.chdir(tmp_path)
    fake = FakeCrewOutput(raw='{"name": "Broken, "value": }}}{{{')
    with pytest.raises(
        ValueError,
        match=r"Invalid JSON output from SimpleModel crew\. Original error: .*Repair failed:",
    ):
        parse_crewai_output(fake, SimpleModel)
    assert list((tmp_path / "debug").glob("failed_json_simplemodel_*.json"))
    assert list((tmp_path / "debug").glob("repair_attempt_simplemodel_*.json"))


# ---------------------------------------------------------------------------
# parse_crewai_output: model-specific special-case handling
# ---------------------------------------------------------------------------


def test_book_summary_report_coerces_table_of_contents_ids_to_strings():
    raw = json.dumps(
        {
            "table_of_contents": [
                {"id": 1, "title": "Chap1"},
                {"id": "2", "title": "Chap2"},
            ]
        }
    )
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, BookSummaryReport)
    assert result.table_of_contents == [
        {"id": "1", "title": "Chap1"},
        {"id": "2", "title": "Chap2"},
    ]


def test_sales_prospecting_wraps_non_dict_metric_value_and_normalizes_type_and_trend():
    raw = json.dumps({"sales_metrics": {"metrics": [{"type": "revenue", "value": 100}]}})
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SalesProspectingReport)
    metric = result.sales_metrics["metrics"][0]
    # "revenue" -> "currency" via normalize_metric_type; bare numeric value gets
    # wrapped with trend "flat", which normalize_trend_direction maps to "stable".
    assert metric == {"type": "currency", "value": {"value": 100, "unit": "", "trend": "stable"}}


def test_sales_prospecting_picks_first_numeric_value_from_dict_without_value_key():
    raw = json.dumps(
        {"sales_metrics": {"metrics": [{"type": "growth", "value": {"current": 50, "note": "text"}}]}}
    )
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SalesProspectingReport)
    metric = result.sales_metrics["metrics"][0]
    # "growth" isn't in the metric-type mapping so it defaults to "numeric".
    assert metric == {"type": "numeric", "value": {"value": 50, "unit": "", "trend": "stable"}}


def test_sales_prospecting_drops_metric_with_no_numeric_value_available():
    raw = json.dumps(
        {
            "sales_metrics": {
                "metrics": [
                    {"type": "text", "value": {"note": "no numbers here"}},
                    {"type": "revenue", "value": 100},
                ]
            }
        }
    )
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SalesProspectingReport)
    metrics = result.sales_metrics["metrics"]
    # The first metric has no numeric value anywhere in its value dict, so it
    # is silently dropped; only the second metric survives.
    assert len(metrics) == 1
    assert metrics[0]["type"] == "currency"


def test_sales_prospecting_normalizes_trend_when_value_dict_already_complete():
    raw = json.dumps(
        {"sales_metrics": {"metrics": [{"type": "rating", "value": {"value": 4, "trend": "increasing"}}]}}
    )
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, SalesProspectingReport)
    metric = result.sales_metrics["metrics"][0]
    assert metric == {"type": "rating", "value": {"value": 4, "trend": "up"}}


# ---------------------------------------------------------------------------
# _attempt_json_repair: direct unit tests
# ---------------------------------------------------------------------------


def test_repair_replaces_smart_quotes():
    repaired = _attempt_json_repair("{“key”: “value”}")
    assert json.loads(repaired) == {"key": "value"}


def test_repair_strips_trailing_comma_in_object():
    repaired = _attempt_json_repair('{"a": 1, "b": 2,}')
    assert json.loads(repaired) == {"a": 1, "b": 2}


def test_repair_strips_trailing_comma_in_array():
    repaired = _attempt_json_repair('["a", "b",]')
    assert json.loads(repaired) == ["a", "b"]


def test_repair_quotes_unquoted_object_keys():
    repaired = _attempt_json_repair("{a: 1, b: 2}")
    assert json.loads(repaired) == {"a": 1, "b": 2}


def test_repair_converts_single_quotes_to_double_quotes():
    repaired = _attempt_json_repair("{'a': 1, 'b': 2}")
    assert json.loads(repaired) == {"a": 1, "b": 2}


def test_repair_fixes_unmatched_closing_braces():
    repaired = _attempt_json_repair('{"a": 1, "b": {"c": 2}')
    assert json.loads(repaired) == {"a": 1, "b": {"c": 2}}


def test_repair_fixes_unmatched_closing_brackets():
    repaired = _attempt_json_repair('["a", "b", ["c"]')
    assert json.loads(repaired) == ["a", "b", ["c"]]


def test_repair_inserts_missing_comma_between_lines():
    repaired = _attempt_json_repair('{\n"a": 1\n"b": 2\n}')
    assert json.loads(repaired) == {"a": 1, "b": 2}


def test_repair_quotes_bare_string_value():
    repaired = _attempt_json_repair('{"a": hello}')
    assert json.loads(repaired) == {"a": "hello"}


def test_repair_removes_unnecessary_escaped_quotes():
    repaired = _attempt_json_repair('{"a": \\"hello\\"}')
    assert json.loads(repaired) == {"a": "hello"}


def test_repair_strips_trailing_comma_after_final_closing_brace():
    repaired = _attempt_json_repair('{"a": 1},')
    assert json.loads(repaired) == {"a": 1}


def test_repair_converts_python_style_booleans_and_none_to_json_literals():
    """Python-style True/False/None must round-trip as JSON literals
    (true/false/null), not get re-wrapped into string values by the later
    "missing quotes around string values" repair step."""
    repaired = _attempt_json_repair('{"a": True, "b": False, "c": None}')
    parsed = json.loads(repaired)
    assert parsed == {"a": True, "b": False, "c": None}
