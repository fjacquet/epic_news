"""The single DeepResearchReport accepts old key names but never invents content (S3)."""

import pytest
from pydantic import ValidationError

from epic_news.models.crews.deep_research import DeepResearchReport

_SOURCE = {"title": "a", "url": "https://a", "source_type": "web", "summary": "s", "relevance_score": 8}


def test_section_title_key_is_accepted():
    report = DeepResearchReport.model_validate(
        {
            "title": "T",
            "topic": "Topic",
            "executive_summary": "Summary",
            "research_sections": [{"title": "Heading", "content": "body"}],
        }
    )
    assert report.research_sections[0].section_title == "Heading"


def test_summary_key_is_accepted_and_topic_falls_back_to_title():
    report = DeepResearchReport.model_validate({"title": "T", "summary": "Sum"})
    assert report.executive_summary == "Sum"
    assert report.topic == "T"


def test_nothing_is_invented():
    report = DeepResearchReport.model_validate(
        {"title": "T", "topic": "Topic", "executive_summary": "S", "research_sections": []}
    )
    assert report.key_findings == []
    assert report.research_sections == []
    assert report.report_date is None
    assert report.unique_sources == []


def test_unique_sources_dedupes_by_url_then_title():
    no_url = {**_SOURCE, "title": "offline", "url": None}
    report = DeepResearchReport.model_validate(
        {
            "title": "T",
            "topic": "Topic",
            "executive_summary": "S",
            "research_sections": [
                {"section_title": "A", "content": "x", "sources": [_SOURCE, no_url]},
                {"section_title": "B", "content": "y", "sources": [{**_SOURCE, "title": "a again"}, no_url]},
            ],
        }
    )
    assert [(s.title, s.url) for s in report.unique_sources] == [("a", "https://a"), ("offline", None)]
    assert report.sources_count == 4  # citations, unchanged contract


def test_non_object_input_is_rejected_not_rewritten():
    with pytest.raises(ValidationError):
        DeepResearchReport.model_validate(["not", "an", "object"])
