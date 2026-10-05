from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools


@CrewBase
class CrossReferenceReportCrew:
    """CrossReferenceReportCrew crew"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def osint_researcher(self) -> Agent:
        """Creates the OSINT researcher agent with tools for data gathering"""
        # Research tools only. None of this agent's tasks read local files (the
        # output/osint aggregation task, global_reporting, runs on osint_reporter), so
        # it holds no file reader next to its web tools.
        all_tools = get_search_tools() + get_scrape_tools()

        return Agent(
            config=self.agents_config["osint_researcher"],
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            allow_delegation=True,
            respect_context_window=True,
        )

    @agent
    def osint_reporter(self) -> Agent:
        """Creates the OSINT reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["osint_reporter"],
            tools=[],  # No tools for reporter to ensure clean output
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def intelligence_requirements_planning(self) -> Task:
        """Develop comprehensive intelligence requirements"""
        return Task(
            config=self.tasks_config["intelligence_requirements_planning"],
            agent=self.osint_researcher(),
            async_execution=False,
        )

    @task
    def intelligence_collection_coordination(self) -> Task:
        """Coordinate intelligence collection activities"""
        return Task(
            config=self.tasks_config["intelligence_collection_coordination"],
            agent=self.osint_researcher(),
            async_execution=False,
        )

    @task
    def intelligence_analysis_integration(self) -> Task:
        """Integrate intelligence analysis from all specialized crews"""
        return Task(
            config=self.tasks_config["intelligence_analysis_integration"],
            agent=self.osint_researcher(),
            async_execution=False,
        )

    @task
    def intelligence_product_development(self) -> Task:
        """Develop final intelligence products"""
        return Task(
            config=self.tasks_config["intelligence_product_development"],
            agent=self.osint_researcher(),
            async_execution=False,
        )

    @task
    def global_reporting(self) -> Task:
        """Create a global report from all generated intelligence."""
        return Task(
            config=self.tasks_config["global_reporting"],
            context=[
                self.intelligence_requirements_planning(),
                self.intelligence_collection_coordination(),
                self.intelligence_analysis_integration(),
                self.intelligence_product_development(),
            ],
            output_pydantic=CrossReferenceReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrossReferenceReportCrew crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
