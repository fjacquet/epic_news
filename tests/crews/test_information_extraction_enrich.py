"""InformationExtractionCrew runs an enrich task before extraction, and the
extraction task consumes the enriched brief as context."""

from epic_news.crews.information_extraction.information_extraction_crew import (
    InformationExtractionCrew,
)
from epic_news.models.extracted_info import ExtractedInfo


def test_crew_has_two_agents_and_two_tasks():
    crew = InformationExtractionCrew().crew()
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2


def test_enrich_runs_first_and_extraction_consumes_it():
    crew = InformationExtractionCrew().crew()
    enrich_task, extract_task = crew.tasks[0], crew.tasks[1]

    # Enrich task emits plain text (the brief), not the structured model.
    assert enrich_task.output_pydantic is None
    # Extraction task still produces ExtractedInfo, and now reads the enrich task.
    assert extract_task.output_pydantic is ExtractedInfo
    assert extract_task.context, "extraction task must consume the enrich task as context"
    assert enrich_task in extract_task.context


def test_faithfulness_guard_is_present_in_config():
    """The 'never invent' constraint is the core safety property — lock it in so a
    future edit can't quietly drop it. Real LLM faithfulness is checked manually
    (see the plan's end-to-end verification), not in CI."""
    ie = InformationExtractionCrew()
    agent_backstory = ie.prompt_enricher_agent().backstory.lower()
    task_desc = ie.enrich_request_task().description.lower()
    assert "never invent" in agent_backstory
    assert "do not" in task_desc and "invent" in task_desc
