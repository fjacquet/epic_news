from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.company_profiler_report import CompanyProfileReport
from epic_news.tools.finance_tools import get_yahoo_finance_tools
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class CompanyProfilerCrew:
    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def company_researcher(self) -> Agent:
        """Creates the company researcher agent with tools for data gathering"""
        # Research tools only: rendering/PDF happen in the flow, never in this agent.
        all_tools = [HybridSearchTool(), get_scraper()] + get_yahoo_finance_tools()

        return Agent(
            config=self.agents_config["company_researcher"],
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def company_reporter(self) -> Agent:
        """Creates the company reporter agent with no tools for clean output generation"""
        return Agent(
            config=self.agents_config["company_reporter"],
            tools=[],  # No tools to prevent action traces in output
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def company_core_info(self) -> Task:
        """Collect foundational information about the company"""
        return Task(
            config=self.tasks_config["company_core_info"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_history(self) -> Task:
        """Research and document the company history"""
        return Task(
            config=self.tasks_config["company_history"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_financials(self) -> Task:
        """Analyze the company financial statements"""
        return Task(
            config=self.tasks_config["company_financials"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_market_position(self) -> Task:
        """Evaluate the company market position"""
        return Task(
            config=self.tasks_config["company_market_position"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_products_services(self) -> Task:
        """Document the company products and services"""
        return Task(
            config=self.tasks_config["company_products_services"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_management(self) -> Task:
        """Research and analyze the company management team"""
        return Task(
            config=self.tasks_config["company_management"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def company_legal_compliance(self) -> Task:
        """Research and document any legal or regulatory issues"""
        return Task(
            config=self.tasks_config["company_legal_compliance"],
            agent=self.company_researcher(),
            async_execution=False,
        )

    @task
    def format_report_task(self) -> Task:
        """Format the comprehensive company profile report"""
        return Task(
            config=self.tasks_config["format_report_task"],
            agent=self.company_reporter(),
            context=[
                self.company_core_info(),
                self.company_history(),
                self.company_financials(),
                self.company_market_position(),
                self.company_products_services(),
                self.company_management(),
                self.company_legal_compliance(),
            ],
            output_pydantic=CompanyProfileReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Company Profiler crew"""
        # Implement the Two-Agent Pattern:
        # 1. Research tasks are assigned to company_researcher (with tools)
        # 2. Final output task is assigned to company_reporter (without tools)
        # This prevents action traces from contaminating the output
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Sequential to avoid needing a manager
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
