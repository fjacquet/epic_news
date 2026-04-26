"""PESTEL analysis crew.

Six-agent research pattern (one researcher per PESTEL dimension) plus a
dedicated reporter with no tools, to avoid action traces in the final output.
The reporter consolidates all six dimensions into a single PestelReport.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import MCPServerAdapter, ScrapeWebsiteTool

from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.tools.hybrid_search_tool import HybridSearchTool


@CrewBase
class PestelCrew:
    """PESTEL analysis crew (6 dimension researchers + 1 reporter)."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    _wikipedia_mcp: MCPServerAdapter | None = None

    @property
    def wikipedia_tools(self):
        """Lazy initialization of Wikipedia MCP tools."""
        adapter = self._wikipedia_mcp
        if adapter is None:
            adapter = MCPServerAdapter(MCPConfig.get_wikipedia_mcp())
            self._wikipedia_mcp = adapter
        return adapter.tools

    def close(self) -> None:
        """Stop the Wikipedia MCP server process to release resources.

        MCPServerAdapter.__init__ spawns the MCP server process; without an
        explicit stop() it persists until garbage collection. Callers should
        invoke close() in a finally block after crew.kickoff() completes.
        """
        adapter = self._wikipedia_mcp
        if adapter is not None:
            try:
                adapter.stop()
            finally:
                self._wikipedia_mcp = None

    def _researcher(self, config_key: str) -> Agent:
        """Build a dimension researcher with the shared tool set."""
        return Agent(
            config=self.agents_config[config_key],  # type: ignore[index]
            tools=[
                HybridSearchTool(),
                ScrapeWebsiteTool(),
                *self.wikipedia_tools,
            ],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("long"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
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
            config=self.agents_config["pestel_reporter"],  # type: ignore[index]
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("long"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
        )

    @task
    def political_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["political_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def economic_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["economic_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def social_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["social_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def technological_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["technological_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def environmental_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["environmental_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def legal_research_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["legal_research_task"],  # type: ignore[index, arg-type]
            async_execution=True,
        )

    @task
    def format_pestel_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["format_pestel_report_task"],  # type: ignore[index, arg-type]
            agent=self.pestel_reporter(),  # type: ignore[call-arg]
            context=[
                self.political_research_task(),  # type: ignore[call-arg]
                self.economic_research_task(),  # type: ignore[call-arg]
                self.social_research_task(),  # type: ignore[call-arg]
                self.technological_research_task(),  # type: ignore[call-arg]
                self.environmental_research_task(),  # type: ignore[call-arg]
                self.legal_research_task(),  # type: ignore[call-arg]
            ],
            output_pydantic=PestelReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(  # type: ignore[call-arg]
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
