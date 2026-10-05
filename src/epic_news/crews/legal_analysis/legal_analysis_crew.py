from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.legal_analysis_report import LegalAnalysisReport
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class LegalAnalysisCrew:
    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def legal_researcher(self) -> Agent:
        """Creates the legal researcher agent with tools for data gathering"""
        # Research tools only: rendering/PDF happen in the flow, never in this agent.
        all_tools = [HybridSearchTool(), get_scraper()]

        return Agent(
            config=self.agents_config["legal_researcher"],
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def legal_reporter(self) -> Agent:
        """Creates the legal reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["legal_reporter"],
            tools=[],  # No tools for reporter to ensure clean output
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def legal_compliance_assessment(self) -> Task:
        """Assess the company's legal compliance status"""
        return Task(
            config=self.tasks_config["legal_compliance_assessment"],
            agent=self.legal_researcher(),
            async_execution=False,
        )

    @task
    def intellectual_property_analysis(self) -> Task:
        """Analyze the company's intellectual property portfolio"""
        return Task(
            config=self.tasks_config["intellectual_property_analysis"],
            agent=self.legal_researcher(),
            async_execution=False,
        )

    @task
    def regulatory_risk_assessment(self) -> Task:
        """Assess the company's regulatory risks"""
        return Task(
            config=self.tasks_config["regulatory_risk_assessment"],
            agent=self.legal_researcher(),
            async_execution=False,
        )

    @task
    def litigation_history_analysis(self) -> Task:
        """Analyze the company's litigation history"""
        return Task(
            config=self.tasks_config["litigation_history_analysis"],
            agent=self.legal_researcher(),
            async_execution=False,
        )

    @task
    def mergers_and_acquisitions_due_diligence(self) -> Task:
        """Conduct legal due diligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["mergers_and_acquisitions_due_diligence"],
            async_execution=False,
            context=[
                self.legal_compliance_assessment(),
                self.intellectual_property_analysis(),
                self.regulatory_risk_assessment(),
                self.litigation_history_analysis(),
            ],
            output_pydantic=LegalAnalysisReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Legal Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
