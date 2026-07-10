"""The crew's output_pydantic contract must survive a small model's omissions.

A production deep-research run (~9 minutes) failed at the final step with:

    3 validation errors for DeepResearchReport
    methodology      Field required
    sources_count    Field required
    confidence_level Field required

The LLM had omitted three fields the model marked strictly required, and the task
instructions themselves didn't list two of them as mandatory (and required a phantom
`conclusions` field this model has never had). `sources_count` is worse: it's a
computed integer no model should be asked to produce.

These tests pin the resilient contract: the three fields default instead of hard-
failing, and `sources_count` is derived from the sections, not trusted.
"""

import pytest
from pydantic import ValidationError

from epic_news.models.crews.deep_research_report import DeepResearchReport

_SECTION = {
    "section_title": "S1",
    "content": "body",
    "sources": [
        {"title": "a", "url": "https://a", "source_type": "web", "summary": "s", "relevance_score": 8},
        {"title": "b", "url": "https://b", "source_type": "web", "summary": "s", "relevance_score": 7},
    ],
}


def _minimal(**overrides) -> dict:
    base = {
        "title": "T",
        "topic": "Topic",
        "executive_summary": "Summary",
        "research_sections": [dict(_SECTION), {"section_title": "S2", "content": "b", "sources": []}],
    }
    base.update(overrides)
    return base


def test_the_exact_production_omission_validates():
    """methodology / sources_count / confidence_level all absent -> must not raise."""
    report = DeepResearchReport.model_validate(_minimal())

    assert report.methodology == ""
    assert report.confidence_level == "Medium"


def test_sources_count_is_computed_not_trusted():
    """Counting is deterministic; the LLM's value is ignored when sections have sources."""
    report = DeepResearchReport.model_validate(_minimal(sources_count=999))

    assert report.sources_count == 2, "must reflect the 2 real sources, not the LLM's 999"


def test_explicit_count_kept_when_no_section_carries_sources():
    """A hand-built report with sourceless sections keeps its stated count."""
    report = DeepResearchReport.model_validate(
        _minimal(research_sections=[{"section_title": "S", "content": "c", "sources": []}], sources_count=15)
    )

    assert report.sources_count == 15


def test_absent_count_defaults_to_zero():
    report = DeepResearchReport.model_validate(
        _minimal(research_sections=[{"section_title": "S", "content": "c", "sources": []}])
    )

    assert report.sources_count == 0


def test_provided_values_are_respected():
    report = DeepResearchReport.model_validate(_minimal(methodology="IMRaD", confidence_level="High"))

    assert report.methodology == "IMRaD"
    assert report.confidence_level == "High"


def test_genuinely_required_fields_still_hard_fail():
    """Resilience is scoped: the report is meaningless without a title/topic/summary."""
    for missing in ("title", "topic", "executive_summary"):
        payload = _minimal()
        payload.pop(missing)
        with pytest.raises(ValidationError):
            DeepResearchReport.model_validate(payload)


def test_phantom_fields_from_the_old_instructions_are_ignored():
    """The old task example emitted conclusions/credibility_score/extraction_date."""
    report = DeepResearchReport.model_validate(
        _minimal(conclusions="general", research_sections=[{**_SECTION, "conclusions": "sec"}])
    )

    assert not hasattr(report, "conclusions")
    assert report.sources_count == 2
