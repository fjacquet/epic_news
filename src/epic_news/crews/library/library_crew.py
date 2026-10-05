from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools


@CrewBase
class LibraryCrew:
    """Library expertise crew for finding books and generating book summaries."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering information."""
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            respect_context_window=True,
            tools=get_search_tools() + get_scrape_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Create a reporting analyst agent responsible for creating JSON reports."""
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            respect_context_window=True,
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
        )

    @task
    def research_task(self) -> Task:
        """Define the research task for gathering information about the topic."""
        return Task(
            config=self.tasks_config["research_task"],
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research."""
        return Task(
            config=self.tasks_config["reporting_task"],
            context=[self.research_task()],
            output_pydantic=BookSummaryReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
