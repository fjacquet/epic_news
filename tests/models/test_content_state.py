"""Tests for ContentState helpers — pure logic, no LLM."""

from __future__ import annotations

import datetime

import pytest

from epic_news.models.content_state import ContentState, CrewCategories
from epic_news.models.crews.pestel_report import PestelDimension, PestelReport
from epic_news.models.extracted_info import ExtractedInfo


def test_pestel_category_registered() -> None:
    assert CrewCategories.PESTEL == "PESTEL"
    assert CrewCategories.to_dict()["PESTEL"] == "PESTEL"


def test_pestel_report_field_accepts_none_and_instance() -> None:
    state = ContentState()
    assert state.pestel_report is None

    dim = PestelDimension(summary="s", impact_analysis="i")
    state.pestel_report = PestelReport(
        topic="x",
        executive_summary="e",
        political=dim,
        economic=dim,
        social=dim,
        technological=dim,
        environmental=dim,
        legal=dim,
        synthesis="s",
        generated_at="2026-04-25",
    )
    assert state.pestel_report.topic == "x"


def test_to_crew_inputs_without_extracted_info_has_required_placeholders() -> None:
    state = ContentState(user_request="hello")
    inputs = state.to_crew_inputs()
    for key in ("user_preferences_and_constraints", "context", "original_message", "target_audience"):
        assert key in inputs
    assert inputs["user_request"] == "hello"


def test_to_crew_inputs_maps_extracted_info_to_topic_and_company() -> None:
    state = ContentState(
        extracted_info=ExtractedInfo(
            main_subject_or_activity="rapport PESTEL Reyl",
            target_company="Reyl",
            destination_location="Geneva",
            event_or_trip_duration="5 days",
        )
    )
    inputs = state.to_crew_inputs()
    assert inputs["topic"] == "rapport PESTEL Reyl"
    assert inputs["company"] == "Reyl"
    assert inputs["destination"] == "Geneva"
    assert inputs["duration"] == "5 days"
    assert inputs["target"] in ("Reyl", "rapport PESTEL Reyl")


def test_to_crew_inputs_falls_back_topic_when_field_missing() -> None:
    """If 'topic' is not directly set, main_subject_or_activity must hydrate it."""
    state = ContentState(
        extracted_info=ExtractedInfo(main_subject_or_activity="something interesting")
    )
    inputs = state.to_crew_inputs()
    assert inputs["topic"] == "something interesting"


def test_to_crew_inputs_injects_computed_fields() -> None:
    state = ContentState()
    inputs = state.to_crew_inputs()
    assert "season" in inputs
    assert "current_date" in inputs
    # Validate ISO date format
    datetime.datetime.strptime(inputs["current_date"], "%Y-%m-%d")


def test_to_crew_inputs_includes_topic_slug_field() -> None:
    """topic_slug is always present in inputs (even if empty when not pre-set)."""
    state = ContentState(extracted_info=ExtractedInfo(main_subject_or_activity="Hello World"))
    inputs = state.to_crew_inputs()
    assert "topic_slug" in inputs


def test_to_crew_inputs_uses_explicit_topic_slug_when_set() -> None:
    state = ContentState(topic_slug="my-explicit-slug")
    inputs = state.to_crew_inputs()
    assert inputs["topic_slug"] == "my-explicit-slug"


def test_to_crew_inputs_drops_none_values_but_keeps_required_placeholders() -> None:
    state = ContentState()
    inputs = state.to_crew_inputs()
    # Required placeholders are empty strings, never None
    assert inputs["context"] == ""
    assert inputs["original_message"] == ""
    # No None values in the final dict
    assert all(v is not None for v in inputs.values())


@pytest.mark.parametrize(
    "category",
    [
        "POEM",
        "COOKING",
        "MENU",
        "PESTEL",
        "DEEPRESEARCH",
        "OPEN_SOURCE_INTELLIGENCE",
        "FINDAILY",
        "RSS",
    ],
)
def test_categories_dict_contains_known_crew(category: str) -> None:
    assert category in CrewCategories.to_dict()
