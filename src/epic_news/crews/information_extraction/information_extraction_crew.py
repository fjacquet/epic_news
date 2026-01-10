from typing import Any, cast

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.extracted_info import ExtractedInfo


@CrewBase
class InformationExtractionCrew:
    """A crew responsible for extracting structured information from a user request."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def detailed_request_analyzer_agent(self) -> Agent:
        """Agent that analyzes the user request in detail."""
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["detailed_request_analyzer_agent"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @task
    def comprehensive_information_extraction_task(self) -> Task:
        """Task to extract information into a Pydantic model."""
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["comprehensive_information_extraction_task"],
            agent=self.detailed_request_analyzer_agent(),  # type: ignore[call-arg]
            output_pydantic=ExtractedInfo,
        )

    @crew
    def crew(self) -> Crew:
        """Creates and returns the InformationExtractionCrew."""
        return Crew(
            agents=cast(list[Agent], self.agents),  # type: ignore[arg-type, attr-defined]
            tasks=cast(list[Task], self.tasks),  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
