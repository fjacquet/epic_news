"""to_crew_inputs must surface the enriched brief as the downstream `context`."""

from epic_news.models.content_state import ContentState


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
