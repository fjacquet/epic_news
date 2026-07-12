"""to_crew_inputs must surface the enriched brief as the downstream `context`, and
must never leak a degenerate (looped/oversized) extraction field to a crew."""

from epic_news.models.content_state import MAX_FREETEXT_CHARS, ContentState
from epic_news.models.extracted_info import ExtractedInfo

# A real GLM-5.2 extraction looped this field; simulate the degeneracy.
DEGENERATE_BLOB = "Road trip by car; hotels booked; family of 3. " * 2000  # ~90 KB


def test_enriched_brief_becomes_context():
    state = ContentState()
    state.user_request = "raw messy request"
    state.enriched_brief = "Clean family road-trip brief with all four cities"
    inputs = state.to_crew_inputs()
    assert inputs["context"] == "Clean family road-trip brief with all four cities"


def test_no_enriched_brief_keeps_default_context():
    state = ContentState()
    state.user_request = "raw messy request"
    inputs = state.to_crew_inputs()
    # Unchanged behaviour: context stays the empty-string placeholder when nothing set it.
    assert inputs.get("context", "") == ""


def test_degenerate_preferences_replaced_by_enriched_brief():
    state = ContentState()
    state.user_request = "raw"
    state.enriched_brief = "Clean brief: family road trip, 4 stops"
    state.extracted_info = ExtractedInfo(
        main_subject_or_activity="trip", user_preferences_and_constraints=DEGENERATE_BLOB
    )
    inputs = state.to_crew_inputs()
    # The looped blob never reaches a crew: preferences fields become the clean brief.
    for key in ("user_preferences_and_constraints", "constraints", "preferences"):
        assert inputs[key] == "Clean brief: family road trip, 4 stops"
        assert len(inputs[key]) <= MAX_FREETEXT_CHARS


def test_freetext_hard_capped_when_no_enriched_brief():
    state = ContentState()
    state.user_request = "raw"
    state.extracted_info = ExtractedInfo(
        main_subject_or_activity="trip", user_preferences_and_constraints=DEGENERATE_BLOB
    )
    inputs = state.to_crew_inputs()
    # No brief to prefer, but the cap still bounds every derived free-text field.
    for key in ("user_preferences_and_constraints", "constraints", "preferences"):
        assert len(inputs[key]) <= MAX_FREETEXT_CHARS
