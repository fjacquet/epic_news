"""
SaintDaily crew for researching and reporting on the saint of the day in Switzerland.
This crew searches for information about today's saint using Wikipedia and other web tools,
then generates a comprehensive French HTML report.
"""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import WikipediaArticleTool, WikipediaProcessingTool, WikipediaSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.saint_daily_report import SaintData


@CrewBase
class SaintDailyCrew:
    """SaintDailyCrew that creates comprehensive saint of the day reports."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def saint_researcher(self) -> Agent:
        # Wikipedia tools for saint research
        wikipedia_tools = [
            WikipediaSearchTool(),
            WikipediaArticleTool(),
            WikipediaProcessingTool(),
        ]
        # Web search and scraping tools for additional research
        research_tools = wikipedia_tools

        return Agent(
            config=self.agents_config["saint_researcher"],
            tools=research_tools,
            verbose=True,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            respect_context_window=True,
        )

    @agent
    def saint_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["saint_reporter"],
            tools=[],  # NO TOOLS = No action traces
            verbose=True,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            respect_context_window=True,
        )

    @task
    def saint_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_research_task"],
            agent=self.saint_researcher(),
        )

    @task
    def saint_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_data_task"],
            agent=self.saint_reporter(),
            context=[self.saint_research_task()],
            output_pydantic=SaintData,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SaintDaily crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
