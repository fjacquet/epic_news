from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool, ScrapeWebsiteTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.tools.data_centric_tools import get_data_centric_tools
from epic_news.tools.report_tools import get_report_tools

load_dotenv()


@CrewBase
class SalesProspectingCrew:
    """Sales Prospecting crew for finding sales contacts at target companies"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],  # type: ignore[index]
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
                DirectoryReadTool("output/sales_prospecting"),
            ]
            + get_report_tools()
            + get_data_centric_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            max_reasoning_attempts=5,
            respect_context_window=True,
        )

    @agent
    def org_structure_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["org_structure_analyst"],  # type: ignore[index]
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
                DirectoryReadTool("output/sales_prospecting"),
            ]
            + get_report_tools()
            + get_data_centric_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            max_reasoning_attempts=5,
            respect_context_window=True,
        )

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],  # type: ignore[index]
            tools=[
                SerperDevTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),
                DirectoryReadTool("output/sales_prospecting"),
            ]
            + get_report_tools()
            + get_data_centric_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            max_reasoning_attempts=5,
            respect_context_window=True,
        )

    @agent
    def sales_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist"],  # type: ignore[index]
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=5,
            respect_context_window=True,
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_company_task"],  # type: ignore[index,arg-type]
            description="Research the target company",
            expected_output="Comprehensive company research findings",
            async_execution=True,
        )

    @task
    def analyze_org_structure_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_org_structure_task"],  # type: ignore[index,arg-type]
            description="Analyze the organizational structure",
            expected_output="Detailed organizational structure analysis",
            async_execution=True,
        )

    @task
    def find_key_contacts_task(self) -> Task:
        return Task(
            config=self.tasks_config["find_key_contacts_task"],  # type: ignore[index,arg-type]
            description="Find key contacts at the target company",
            expected_output="List of key contacts with details",
            async_execution=True,
        )

    @task
    def generate_sales_metrics_task(self) -> Task:
        return Task(
            config=self.tasks_config["develop_approach_strategy_task"],  # type: ignore[index,arg-type]
            description="Generate sales strategy and metrics",
            expected_output="Comprehensive sales prospecting report",
            context=[
                self.research_company_task(),  # type: ignore[call-arg]
                self.analyze_org_structure_task(),  # type: ignore[call-arg]
                self.find_key_contacts_task(),  # type: ignore[call-arg]
            ],
            output_pydantic=SalesProspectingReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Sales Prospecting crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
            max_rpm=10,  # Keeping existing custom value (lower than default 20)
        )
