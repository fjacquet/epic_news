"""Unit tests for epic_news.utils.diagnostics.parsing.

Covers the public API (parse_crewai_output) and the private helper
functions (_attempt_json_repair, _transform_holiday_planner_data) that
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
    _transform_holiday_planner_data,
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


class HolidayPlannerReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    itinerary: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[Any] = Field(default_factory=list)
    accommodations: list[dict[str, Any]] = Field(default_factory=list)


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


def test_holiday_planner_coerces_day_date_activities_and_transforms_sources_and_accommodations():
    raw = json.dumps(
        {
            "itinerary": [{"day": 1, "date": 20260715, "activities": "single-activity"}],
            "sources": ["https://example.com/a", {"title": "B", "url": "y", "type": "z"}],
            "accommodations": [{"nom": "Hotel X", "adresse": "1 rue"}],
        }
    )
    fake = FakeCrewOutput(raw=raw)
    result = parse_crewai_output(fake, HolidayPlannerReport)

    # int day/date coerced to strings; scalar activities wrapped in a list.
    assert result.itinerary == [{"day": "1", "date": "20260715", "activities": ["single-activity"]}]

    # URL strings converted to Source-like dicts; existing dicts pass through.
    assert result.sources == [
        {"title": "a", "url": "https://example.com/a", "type": "reference"},
        {"title": "B", "url": "y", "type": "z"},
    ]

    # French nom/adresse renamed to name/address; description defaults to name.
    assert result.accommodations == [{"name": "Hotel X", "address": "1 rue", "description": "Hotel X"}]


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


def test_repair_mangles_python_style_booleans_and_none_bug():
    """Documents a genuine quirk: after True/False/None -> true/false/null
    substitution, the later "missing quotes around string values" regex
    re-wraps those bare keyword tokens (plus the following comma) into a
    single malformed string value instead of leaving them as JSON literals.
    This means booleans/None surrounded by commas do NOT round-trip as
    booleans/null through _attempt_json_repair."""
    repaired = _attempt_json_repair('{"a": True, "b": False, "c": None}')
    parsed = json.loads(repaired)
    assert parsed == {"a": "true, ", "b": "false, ", "c": "null, "}


# ---------------------------------------------------------------------------
# _transform_holiday_planner_data: direct unit tests
# ---------------------------------------------------------------------------


def test_transform_converts_url_strings_and_passes_through_dict_sources():
    data = {
        "sources": [
            "https://example.com/page",
            {"title": "Existing", "url": "x", "type": "y"},
            "https://example.com/",  # trailing slash -> empty title -> "Source"
        ]
    }
    result = _transform_holiday_planner_data(data)
    assert result["sources"] == [
        {"title": "page", "url": "https://example.com/page", "type": "reference"},
        {"title": "Existing", "url": "x", "type": "y"},
        {"title": "Source", "url": "https://example.com/", "type": "reference"},
    ]


def test_transform_leaves_empty_sources_list_untouched():
    data = {"sources": []}
    result = _transform_holiday_planner_data(data)
    assert result["sources"] == []


def test_transform_leaves_non_list_sources_untouched():
    data = {"sources": "not-a-list"}
    result = _transform_holiday_planner_data(data)
    assert result["sources"] == "not-a-list"


def test_transform_no_sources_key_is_a_no_op():
    data = {"unrelated": True}
    result = _transform_holiday_planner_data(data)
    assert result == {"unrelated": True}


def test_transform_itinerary_derives_day_from_jour_and_deletes_jour():
    data = {"itinerary": [{"jour": "Jour 2 - 15 Juillet"}]}
    result = _transform_holiday_planner_data(data)
    # "jour" is deleted as soon as "day" is derived, so no "date" key is set
    # in this path (the date-derivation branch below never gets to run).
    assert result["itinerary"] == [{"day": 2}]


def test_transform_itinerary_defaults_day_to_1_when_jour_has_no_second_token():
    data = {"itinerary": [{"jour": "Jour"}]}
    result = _transform_holiday_planner_data(data)
    assert result["itinerary"] == [{"day": 1}]


def test_transform_itinerary_jour_without_jour_substring_yields_empty_item():
    data = {"itinerary": [{"jour": "Somewhere"}]}
    result = _transform_holiday_planner_data(data)
    # "Jour" substring not found -> "day" never set; "jour" still deleted.
    assert result["itinerary"] == [{}]


def test_transform_itinerary_derives_date_only_when_day_already_present():
    """When 'day' is already set, the jour-deletion branch is skipped, so
    'jour' survives into the second block which derives 'date' from it by
    splitting on '-'. This leaves a stray French 'jour' key in the output."""
    data = {"itinerary": [{"day": 1, "jour": "Something-15 Juillet"}]}
    result = _transform_holiday_planner_data(data)
    assert result["itinerary"] == [{"day": 1, "jour": "Something-15 Juillet", "date": "15 Juillet"}]


def test_transform_itinerary_date_defaults_to_tbd_without_dash():
    data = {"itinerary": [{"day": 1, "jour": "NoDashHere"}]}
    result = _transform_holiday_planner_data(data)
    assert result["itinerary"] == [{"day": 1, "jour": "NoDashHere", "date": "TBD"}]


def test_transform_accommodations_renames_french_fields_and_fills_defaults():
    data = {"accommodations": [{"nom": "Hotel Test", "adresse": "123 Street"}]}
    result = _transform_holiday_planner_data(data)
    assert result["accommodations"] == [
        {"name": "Hotel Test", "address": "123 Street", "description": "Hotel Test"}
    ]


def test_transform_accommodations_empty_dict_gets_defaults():
    data = {"accommodations": [{}]}
    result = _transform_holiday_planner_data(data)
    assert result["accommodations"] == [
        {"address": "Address not specified", "description": "Accommodation option"}
    ]


def test_transform_accommodations_keeps_nom_when_name_already_present():
    data = {"accommodations": [{"name": "Already named", "nom": "ShouldStay"}]}
    result = _transform_holiday_planner_data(data)
    # "nom" is only renamed/deleted when "name" is absent; here it survives.
    assert result["accommodations"] == [
        {
            "name": "Already named",
            "nom": "ShouldStay",
            "address": "Address not specified",
            "description": "Already named",
        }
    ]
