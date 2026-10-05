from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig, get_mcp_tools_or_empty
from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool


@CrewBase
class DeepResearchCrew:
    """DeepResearch crew for comprehensive internet research with 4-agent architecture.

    Agents:
    1. research_strategist: Planning and methodology
    2. information_collector: Web + Wikipedia research (merged from 2 agents)
    3. data_analyst: Analysis and synthesis with Code Interpreter
    4. report_writer: Technical report creation
    """

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    # Wikipedia MCP server: @CrewBase starts it lazily on the first get_mcp_tools()
    # call and stops it in an after-kickoff hook.
    mcp_server_params = MCPConfig.get_wikipedia_mcp()

    # Research Strategist - Planning and methodology
    @agent
    def research_strategist(self) -> Agent:
        """Research strategist agent for planning and methodology."""
        return Agent(
            config=self.agents_config["research_strategist"],
            tools=[],  # Strategic planning, no external tools needed
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    # Information Collector - Web and encyclopedic research
    @agent
    def information_collector(self) -> Agent:
        """Information collector agent with web search, scraping AND Wikipedia MCP tools."""
        return Agent(
            config=self.agents_config["information_collector"],
            tools=[
                # Hybrid search (Perplexity → Brave → Serper cascading fallback)
                HybridSearchTool(),
                CappedScrapeWebsiteTool(),
                # Wikipedia MCP tools (encyclopedic research)
                *get_mcp_tools_or_empty(self),  # Adds search and fetch tools from Wikipedia MCP
            ],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    # Data Analyst - Critical analysis and synthesis of the collected corpus
    @agent
    def data_analyst(self) -> Agent:
        """Data analyst agent for critical synthesis of the collected sources.

        Deliberately tool-less: the corpus arrives via task context. Given a FileReadTool
        it invents plausible filenames and tries to read a corpus nobody ever wrote.
        """
        return Agent(
            config=self.agents_config["data_analyst"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    # Report Writer - Technical writing
    @agent
    def report_writer(self) -> Agent:
        """Report writer agent for technical report creation."""
        return Agent(
            config=self.agents_config["report_writer"],
            tools=[],  # Report writing, no external tools needed
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    # Task 1: Research Planning
    @task
    def reformulate_task(self) -> Task:
        """Reformulate task."""
        return Task(
            config=self.tasks_config["reformulate_task"],
        )

    @task
    def research_planning_task(self) -> Task:
        """Research planning and methodology task."""
        return Task(
            config=self.tasks_config["research_planning_task"],
        )

    # Task 2: Information Collection
    @task
    def information_collection_task(self) -> Task:
        """Information collection task."""
        return Task(
            config=self.tasks_config["information_collection_task"],
            context=[
                self.research_planning_task(),
            ],
        )

    # Task 3: Data Analysis (formerly Task 4)
    @task
    def data_analysis_task(self) -> Task:
        """Data analysis and synthesis task."""
        return Task(
            config=self.tasks_config["data_analysis_task"],
            context=[
                self.research_planning_task(),
                self.information_collection_task(),
            ],
        )

    # Task 4: Report Writing (formerly Task 5)
    @task
    def report_writing_task(self) -> Task:
        """Report writing task."""
        return Task(
            config=self.tasks_config["report_writing_task"],
            context=[
                self.research_planning_task(),
                self.information_collection_task(),
                self.data_analysis_task(),
            ],
            output_pydantic=DeepResearchReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DeepResearch crew with 6-agent sequential process."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,  # Automatically created from the tasks above
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
