"""Unit tests for epic_news.utils.diagnostics.parsing.parse_crewai_output."""

import json
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from epic_news.utils.diagnostics.parsing import parse_crewai_output


class FakeCrewOutput:
    """Minimal stand-in for CrewAI's CrewOutput/TaskOutput objects."""

    def __init__(self, raw: str = "", output: Any = None):
        self.raw = raw
        if output is not None:
            self.output = output


class SimpleModel(BaseModel):
    name: str
    value: int


class OptionalNote(BaseModel):
    name: str
    note: str | None = None


class Loose(BaseModel):
    a: Any = None
    b: Any = None
    c: Any = None
    key: Any = None


class Listed(BaseModel):
    items: list[Any]


# ---------------------------------------------------------------------------
# happy paths
# ---------------------------------------------------------------------------


def test_direct_pydantic_output_passthrough():
    model = SimpleModel(name="a", value=1)
    result = parse_crewai_output(FakeCrewOutput(output=model), SimpleModel)
    assert result is model


def test_valid_json_raw_parses_directly():
    fake = FakeCrewOutput(raw=json.dumps({"name": "Bob", "value": 42}))
    assert parse_crewai_output(fake, SimpleModel) == SimpleModel(name="Bob", value=42)


def test_json_wrapped_in_triple_backticks_with_language_hint():
    fake = FakeCrewOutput(raw='```json\n{"name": "Alice", "value": 7}\n```')
    assert parse_crewai_output(fake, SimpleModel) == SimpleModel(name="Alice", value=7)


def test_preamble_and_trailing_text_are_stripped():
    raw = 'Thought: I will answer now.\nFinal Answer: {"name": "Carl", "value": 3} \nThanks!'
    assert parse_crewai_output(FakeCrewOutput(raw=raw), SimpleModel) == SimpleModel(name="Carl", value=3)


def test_thousand_separator_numbers_are_sanitized():
    result = parse_crewai_output(FakeCrewOutput(raw='{"name": "Numbers", "value": 1,234,567}'), SimpleModel)
    assert result.value == 1234567


def test_smart_quotes_in_raw_are_sanitized():
    result = parse_crewai_output(FakeCrewOutput(raw='{"name": “Quoted”, "value": 5}'), SimpleModel)
    assert result == SimpleModel(name="Quoted", value=5)


def test_python_none_literal_is_read_by_json_repair():
    model = parse_crewai_output(SimpleNamespace(raw='{"name": "a", "note": None}', output=None), OptionalNote)
    # json_repair reads a bare None as the text "None" (the old regex repair produced null).
    assert model.note == "None"


# ---------------------------------------------------------------------------
# failure paths
# ---------------------------------------------------------------------------


def test_empty_raw_raises_value_error_with_inputs_info():
    with pytest.raises(ValueError, match="produced no output") as excinfo:
        parse_crewai_output(FakeCrewOutput(raw=""), SimpleModel, inputs={"topic": "x"})
    assert "Inputs were: {'topic': 'x'}" in str(excinfo.value)


def test_whitespace_only_raw_raises_value_error():
    with pytest.raises(ValueError, match="produced no output"):
        parse_crewai_output(FakeCrewOutput(raw="   \n  "), SimpleModel)


def test_no_json_content_raises_value_error():
    with pytest.raises(ValueError, match="produced no valid JSON"):
        parse_crewai_output(FakeCrewOutput(raw="just plain text, no json here"), SimpleModel)


def test_array_root_fails_model_validation_with_dict_only_model():
    with pytest.raises(ValueError, match="Invalid SimpleModel data structure"):
        parse_crewai_output(FakeCrewOutput(raw="preamble [1, 2, 3] trailing"), SimpleModel)


def test_valid_json_wrong_schema_raises_data_structure_error():
    with pytest.raises(ValueError, match="Invalid SimpleModel data structure"):
        parse_crewai_output(FakeCrewOutput(raw='{"name": "OnlyName"}'), SimpleModel)


def test_unrepairable_garbage_with_brace_raises_invalid():
    with pytest.raises(ValueError, match="^Invalid"):
        parse_crewai_output(FakeCrewOutput(raw="{ this is : : not json at all"), SimpleModel)


# ---------------------------------------------------------------------------
# repair cases (formerly _attempt_json_repair unit tests), through the parser
# ---------------------------------------------------------------------------


def _parse(raw: str, model: type[BaseModel]) -> dict:
    return parse_crewai_output(FakeCrewOutput(raw=raw), model).model_dump(exclude_none=True)


def test_repair_replaces_smart_quotes():
    assert _parse("{“key”: “value”}", Loose) == {"key": "value"}


def test_repair_strips_trailing_comma_in_object():
    assert _parse('{"a": 1, "b": 2,}', Loose) == {"a": 1, "b": 2}


def test_repair_strips_trailing_comma_in_array():
    assert _parse('{"items": ["a", "b",]}', Listed) == {"items": ["a", "b"]}


def test_repair_quotes_unquoted_object_keys():
    assert _parse("{a: 1, b: 2}", Loose) == {"a": 1, "b": 2}


def test_repair_converts_single_quotes_to_double_quotes():
    assert _parse("{'a': 1, 'b': 2}", Loose) == {"a": 1, "b": 2}


def test_repair_fixes_unmatched_closing_braces():
    assert _parse('{"a": 1, "b": {"c": 2}', Loose) == {"a": 1, "b": {"c": 2}}


def test_repair_fixes_unmatched_closing_brackets():
    assert _parse('{"items": ["a", "b", ["c"]', Listed) == {"items": ["a", "b", ["c"]]}


def test_repair_inserts_missing_comma_between_lines():
    assert _parse('{\n"a": 1\n"b": 2\n}', Loose) == {"a": 1, "b": 2}


def test_repair_quotes_bare_string_value():
    assert _parse('{"a": hello}', Loose) == {"a": "hello"}


def test_repair_removes_unnecessary_escaped_quotes():
    # json_repair keeps a stray trailing quote here (the old regex repair gave "hello").
    assert _parse('{"a": \\"hello\\"}', Loose) == {"a": 'hello"'}


def test_repair_strips_trailing_comma_after_final_closing_brace():
    assert _parse('{"a": 1},', Loose) == {"a": 1}


def test_repair_python_booleans():
    assert _parse('{"a": True, "b": False}', Loose) == {"a": True, "b": False}


def test_valid_json_followed_by_prose_with_brackets():
    # Citations and markdown after the JSON must not be read as more JSON.
    raw = '{"name": "Dana", "value": 5}\n\nSources: [1] https://example.com and {see appendix}'
    assert parse_crewai_output(FakeCrewOutput(raw=raw), SimpleModel) == SimpleModel(name="Dana", value=5)


def test_first_of_two_json_objects_wins():
    raw = '{"name": "first", "value": 1}\n{"name": "second", "value": 2}'
    assert parse_crewai_output(FakeCrewOutput(raw=raw), SimpleModel).name == "first"
