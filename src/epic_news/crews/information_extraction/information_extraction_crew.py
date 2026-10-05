from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.extracted_info import ExtractedInfo


@CrewBase
class InformationExtractionCrew:
    """A crew responsible for extracting structured information from a user request."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def prompt_enricher_agent(self) -> Agent:
        """Agent that rewrites the raw request into a clean, faithful brief."""
        return Agent(
            config=self.agents_config["prompt_enricher_agent"],
            llm=LLMConfig.get_openrouter_llm(task_type="quick"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @agent
    def detailed_request_analyzer_agent(self) -> Agent:
        """Agent that analyzes the user request in detail."""
        return Agent(
            config=self.agents_config["detailed_request_analyzer_agent"],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @task
    def enrich_request_task(self) -> Task:
        """Task that produces the enriched brief (runs first)."""
        return Task(
            config=self.tasks_config["enrich_request_task"],
            agent=self.prompt_enricher_agent(),
        )

    @task
    def comprehensive_information_extraction_task(self) -> Task:
        """Task to extract information into a Pydantic model from the enriched brief."""
        return Task(
            config=self.tasks_config["comprehensive_information_extraction_task"],
            agent=self.detailed_request_analyzer_agent(),
            context=[self.enrich_request_task()],
            output_pydantic=ExtractedInfo,
        )

    @crew
    def crew(self) -> Crew:
        """Creates and returns the InformationExtractionCrew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
