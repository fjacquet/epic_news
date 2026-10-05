from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.tools.github_tools import get_github_tools
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class TechStackCrew:
    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def tech_researcher(self) -> Agent:
        """Creates the tech researcher agent with tools for data gathering"""
        # Research tools only: rendering/PDF happen in the flow, never in this agent.
        all_tools = [HybridSearchTool(), get_scraper()] + get_github_tools()

        return Agent(
            config=self.agents_config["tech_researcher"],
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def tech_reporter(self) -> Agent:
        """Creates the tech reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["tech_reporter"],
            tools=[],  # No tools for reporter to ensure clean output
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def tech_stack_identification(self) -> Task:
        """Identify the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_identification"],
            agent=self.tech_researcher(),
            async_execution=False,
        )

    @task
    def tech_stack_analysis(self) -> Task:
        """Analyze the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_analysis"],
            agent=self.tech_researcher(),
            async_execution=False,
        )

    @task
    def open_source_contributions(self) -> Task:
        """Analyze the company's open source contributions"""
        return Task(
            config=self.tasks_config["open_source_contributions"],
            agent=self.tech_researcher(),
            async_execution=False,
        )

    @task
    def tech_talent_assessment(self) -> Task:
        """Assess the company's tech talent"""
        return Task(
            config=self.tasks_config["tech_talent_assessment"],
            agent=self.tech_researcher(),
            async_execution=False,
        )

    @task
    def consolidate_tech_stack_report(self) -> Task:
        """Consolidate all findings into a comprehensive tech stack report"""
        return Task(
            config=self.tasks_config["consolidate_tech_stack_report"],
            async_execution=False,
            context=[
                self.tech_stack_identification(),
                self.tech_stack_analysis(),
                self.open_source_contributions(),
                self.tech_talent_assessment(),
            ],
            output_pydantic=TechStackReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Tech Stack Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
