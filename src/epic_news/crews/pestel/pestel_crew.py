"""PESTEL analysis crew.

Six-agent research pattern (one researcher per PESTEL dimension) plus a
dedicated reporter with no tools, to avoid action traces in the final output.
The six dimension tasks run in parallel (async); the report task waits for all of
them through its context.
The reporter consolidates all six dimensions into a single PestelReport.
"""

from __future__ import annotations

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig, get_mcp_tools_or_empty
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool
from epic_news.tools.recent_search_tool import RecentSearchTool


@CrewBase
class PestelCrew:
    """PESTEL analysis crew (6 dimension researchers + 1 reporter)."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    # Wikipedia MCP server: @CrewBase starts one shared adapter on the first
    # get_mcp_tools() call and stops it in an after-kickoff hook.
    mcp_server_params = MCPConfig.get_wikipedia_mcp()

    def _researcher(self, config_key: str) -> Agent:
        """Build a dimension researcher with the shared tool set."""
        return Agent(
            config=self.agents_config[config_key],
            tools=[
                RecentSearchTool(),
                HybridSearchTool(),
                CappedScrapeWebsiteTool(),
                *get_mcp_tools_or_empty(self),
            ],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def political_researcher(self) -> Agent:
        return self._researcher("political_researcher")

    @agent
    def economic_researcher(self) -> Agent:
        return self._researcher("economic_researcher")

    @agent
    def social_researcher(self) -> Agent:
        return self._researcher("social_researcher")

    @agent
    def technological_researcher(self) -> Agent:
        return self._researcher("technological_researcher")

    @agent
    def environmental_researcher(self) -> Agent:
        return self._researcher("environmental_researcher")

    @agent
    def legal_researcher(self) -> Agent:
        return self._researcher("legal_researcher")

    @agent
    def pestel_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["pestel_reporter"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def political_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["political_research_task"],
            async_execution=True,
        )

    @task
    def economic_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["economic_research_task"],
            async_execution=True,
        )

    @task
    def social_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["social_research_task"],
            async_execution=True,
        )

    @task
    def technological_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["technological_research_task"],
            async_execution=True,
        )

    @task
    def environmental_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["environmental_research_task"],
            async_execution=True,
        )

    @task
    def legal_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["legal_research_task"],
            async_execution=True,
        )

    @task
    def format_pestel_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["format_pestel_report_task"],
            agent=self.pestel_reporter(),
            context=[
                self.political_research_task(),
                self.economic_research_task(),
                self.social_research_task(),
                self.technological_research_task(),
                self.environmental_research_task(),
                self.legal_research_task(),
            ],
            output_pydantic=PestelReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
