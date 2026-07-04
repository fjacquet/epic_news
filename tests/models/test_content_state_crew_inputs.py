"""Characterization tests pinning to_crew_inputs() before refactoring."""

from epic_news.models.content_state import ContentState
from epic_news.models.extracted_info import ExtractedInfo


def _state() -> ContentState:
    return ContentState(
        user_request="Plan a trip",
        extracted_info=ExtractedInfo(
            main_subject_or_activity="Trip to Rome",
            target_company="ACME Corp",
            destination_location="Rome",
            origin_location="Geneva",
            event_or_trip_duration="3 days",
            traveler_details="2 adults",
            user_preferences_and_constraints="vegetarian",
        ),
    )


def test_extracted_info_field_mapping():
    inputs = _state().to_crew_inputs()
    assert inputs["topic"] == "Trip to Rome"
    assert inputs["company"] == "ACME Corp"
    assert inputs["destination"] == "Rome"
    assert inputs["origin"] == "Geneva"
    assert inputs["duration"] == "3 days"
    assert inputs["family"] == "2 adults"
    assert inputs["user_preferences_and_constraints"] == "vegetarian"


def test_required_placeholders_always_present():
    inputs = ContentState(user_request="x").to_crew_inputs()
    for key in ("user_preferences_and_constraints", "context", "original_message", "target_audience"):
        assert key in inputs, f"missing required placeholder: {key}"


def test_none_values_are_stripped():
    inputs = ContentState(user_request="x").to_crew_inputs()
    assert all(v is not None for v in inputs.values())


def test_computed_fields_present():
    inputs = ContentState(user_request="x").to_crew_inputs()
    assert "current_date" in inputs
    assert "season" in inputs
    assert "topic_slug" in inputs
    assert "menu_slug" in inputs


def test_target_falls_back_from_company_to_topic():
    with_company = _state().to_crew_inputs()
    assert with_company["target"] == "ACME Corp"

    topic_only = ContentState(
        user_request="x",
        extracted_info=ExtractedInfo(main_subject_or_activity="Solar panels"),
    ).to_crew_inputs()
    assert topic_only["target"] == "Solar panels"


def test_no_stdout_noise(capsys):
    """to_crew_inputs must not print() — it runs on every crew kickoff."""
    _state().to_crew_inputs()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_participants_and_product_field_mapping():
    """Covers the remaining field_mapping entries that have real ExtractedInfo sources.

    field_mapping also lists "meeting_context" -> "context", "meeting_objective" ->
    "objective", and "prior_interactions" -> "prior_interactions", but ExtractedInfo
    has no fields named meeting_context, meeting_objective, or prior_interactions
    (it only defines "context" and "objective" directly, which are not the mapping's
    source keys). Those three field_mapping entries are dead: the `source_key in
    extracted_data` check can never be true, so they are not exercised here.
    """
    inputs = ContentState(
        user_request="Prep the meeting",
        extracted_info=ExtractedInfo(
            participants=["Ana <ana@example.com> - CEO"],
            our_product="PowerFlex",
        ),
    ).to_crew_inputs()
    assert inputs["participants"] == ["Ana <ana@example.com> - CEO"]
    assert inputs["our_product"] == "PowerFlex"
