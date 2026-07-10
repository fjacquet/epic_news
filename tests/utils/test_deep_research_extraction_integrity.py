"""Regression tests for the deep_research extraction path.

A real 19-minute research run once produced a report containing only placeholder text
("https://example.com/source"). Two defects combined:

1. ``DeepResearchExtractor.extract()`` returns ``{"deep_research_model": ...}``, but the
   caller assigned that dict straight to a ``DeepResearchReport`` variable.
2. Two distinct classes were both named ``DeepResearchReport``, so the ``isinstance``
   guard in the extractor could never match the model the caller passed back in.

The second extraction pass therefore fell through to the placeholder branch and the
degraded report was rendered and emailed as a success. These tests pin both defects.
"""

import json

import pytest
from loguru import logger

from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.utils.extractors.deep_research import DeepResearchExtractor
from epic_news.utils.extractors.factory import ContentExtractorFactory

PLACEHOLDER_MARKERS = (
    "example.com/source",
    "Contenu détaillé de la recherche approfondie",
)


@pytest.fixture
def crew_report_json() -> str:
    """JSON in the shape the deep_research crew actually writes to report.json."""
    return json.dumps(
        {
            "title": "Etat CrewAI 2026",
            "topic": "crewai",
            "executive_summary": "Un vrai résumé exécutif.",
            "key_findings": ["Une découverte réelle"],
            "methodology": "Recherche documentaire",
            "research_sections": [
                {
                    "section_title": "Une section réelle",
                    "content": "Contenu réel issu de la recherche.",
                    "sources": [
                        {
                            "title": "Source réelle",
                            "url": "https://real.example.org/article",
                            "source_type": "web",
                            "summary": "Résumé réel de la source.",
                            "relevance_score": 9,
                        }
                    ],
                }
            ],
            "sources_count": 1,
            "report_date": "2026-07-10",
            "confidence_level": "High",
        }
    )


def _dump(model: DeepResearchReport) -> str:
    return json.dumps(model.model_dump(), default=str)


def test_extract_returns_dict_not_model(crew_report_json: str):
    """extract() returns a wrapper dict; callers must unwrap 'deep_research_model'."""
    result = DeepResearchExtractor().extract({"raw_output": crew_report_json})

    assert isinstance(result, dict)
    assert not isinstance(result, DeepResearchReport)
    assert isinstance(result["deep_research_model"], DeepResearchReport)


def test_extract_preserves_real_content(crew_report_json: str):
    """The crew's real findings survive the first extraction pass."""
    model = DeepResearchExtractor().extract({"raw_output": crew_report_json})["deep_research_model"]

    assert model.title == "Etat CrewAI 2026"
    assert "real.example.org" in _dump(model)
    for marker in PLACEHOLDER_MARKERS:
        assert marker not in _dump(model)


def test_second_pass_roundtrips_model_without_placeholder_fallback(crew_report_json: str):
    """The factory's second pass must recognise the model, not rebuild placeholders.

    This is the exact call main.generate_deep_research makes after unwrapping. If the
    isinstance guard fails, the extractor silently substitutes placeholder text.
    """
    model = DeepResearchExtractor().extract({"raw_output": crew_report_json})["deep_research_model"]

    state_data = {
        "deep_research_report": model,
        "final_report": "CrewOutput(raw='not json')",
        "user_request": "etat crewai",
        "current_date": "2026-07-10",
    }
    extracted = ContentExtractorFactory.extract_content(state_data, "DEEPRESEARCH")
    round_tripped = extracted["deep_research_model"]

    assert round_tripped is model, "second pass rebuilt the report instead of reusing it"
    assert "real.example.org" in _dump(round_tripped)
    for marker in PLACEHOLDER_MARKERS:
        assert marker not in _dump(round_tripped)


def test_state_model_class_matches_extractor_class():
    """main.py, content_state and the extractor must share one DeepResearchReport class."""
    from epic_news.models.content_state import ContentState

    field = ContentState.model_fields["deep_research_report"]
    assert DeepResearchReport in getattr(field.annotation, "__args__", (field.annotation,))


def test_placeholder_fallback_is_logged_as_error():
    """An unparseable report must scream, not whisper -- it once shipped as a success.

    Loguru does not propagate to pytest's caplog, so capture via a dedicated sink.
    """
    records: list[tuple[str, str]] = []
    sink_id = logger.add(lambda msg: records.append((msg.record["level"].name, msg.record["message"])))
    try:
        result = DeepResearchExtractor().extract({"raw_output": "this is definitely not json"})
    finally:
        logger.remove(sink_id)

    # The fallback still returns a usable model, but it must be flagged at ERROR.
    assert isinstance(result["deep_research_model"], DeepResearchReport)
    error_messages = [msg for level, msg in records if level == "ERROR"]
    assert error_messages, f"placeholder fallback logged no ERROR; got {records}"
    assert any("PLACEHOLDER" in msg.upper() for msg in error_messages)
