from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool


@CrewBase
class SalesProspectingCrew:
    """Sales Prospecting crew for finding sales contacts at target companies"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            tools=[HybridSearchTool(), CappedScrapeWebsiteTool()],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            respect_context_window=True,
        )

    @agent
    def org_structure_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["org_structure_analyst"],
            tools=[HybridSearchTool(), CappedScrapeWebsiteTool()],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            respect_context_window=True,
        )

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],
            tools=[HybridSearchTool(), CappedScrapeWebsiteTool()],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            respect_context_window=True,
        )

    @agent
    def sales_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            respect_context_window=True,
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_company_task"],
            async_execution=False,
        )

    @task
    def analyze_org_structure_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_org_structure_task"],
            async_execution=False,
        )

    @task
    def find_key_contacts_task(self) -> Task:
        return Task(
            config=self.tasks_config["find_key_contacts_task"],
            async_execution=False,
        )

    @task
    def generate_sales_metrics_task(self) -> Task:
        return Task(
            config=self.tasks_config["develop_approach_strategy_task"],
            context=[
                self.research_company_task(),
                self.analyze_org_structure_task(),
                self.find_key_contacts_task(),
            ],
            output_pydantic=SalesProspectingReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Sales Prospecting crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=10,  # Keeping existing custom value (lower than default 20)
        )
