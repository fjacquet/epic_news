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
            config=self.agents_config["detailed_request_analyzer_agent"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @task
    def comprehensive_information_extraction_task(self) -> Task:
        """Task to extract information into a Pydantic model."""
        return Task(
            config=self.tasks_config["comprehensive_information_extraction_task"],
            output_pydantic=ExtractedInfo,
        )

    @crew
    def crew(self) -> Crew:
        """Creates and returns the InformationExtractionCrew."""
        return Crew(
            agents=self.agents,  # Uses the @agent decorated properties
            tasks=self.tasks,  # Uses the @task decorated properties
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
