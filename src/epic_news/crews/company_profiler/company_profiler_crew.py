from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.company_profiler_report import CompanyProfileReport
from epic_news.tools.finance_tools import get_yahoo_finance_tools
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class CompanyProfilerCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def company_researcher(self) -> Agent:
        """Creates the company researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), get_scraper(), PDFSearchTool()]
        finance_tools = get_yahoo_finance_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + finance_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["company_researcher"],  # type: ignore
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
        )

    @agent
    def company_reporter(self) -> Agent:
        """Creates the company reporter agent with no tools for clean output generation"""
        return Agent(
            config=self.agents_config["company_reporter"],  # type: ignore
            tools=[],  # No tools to prevent action traces in output
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
        )

    @task
    def company_core_info(self) -> Task:
        """Collect foundational information about the company"""
        return Task(
            config=self.tasks_config["company_core_info"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_history(self) -> Task:
        """Research and document the company history"""
        return Task(
            config=self.tasks_config["company_history"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_financials(self) -> Task:
        """Analyze the company financial statements"""
        return Task(
            config=self.tasks_config["company_financials"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_market_position(self) -> Task:
        """Evaluate the company market position"""
        return Task(
            config=self.tasks_config["company_market_position"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_products_services(self) -> Task:
        """Document the company products and services"""
        return Task(
            config=self.tasks_config["company_products_services"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_management(self) -> Task:
        """Research and analyze the company management team"""
        return Task(
            config=self.tasks_config["company_management"],  # type: ignore
            async_execution=True,
        )

    @task
    def company_legal_compliance(self) -> Task:
        """Research and document any legal or regulatory issues"""
        return Task(
            config=self.tasks_config["company_legal_compliance"],  # type: ignore
            async_execution=True,
        )

    @task
    def format_report_task(self) -> Task:
        """Format the comprehensive company profile report"""
        return Task(
            config=self.tasks_config["format_report_task"],  # type: ignore
            agent=self.company_reporter(),  # type: ignore
            context=[
                self.company_core_info(),  # type: ignore
                self.company_history(),  # type: ignore
                self.company_financials(),  # type: ignore
                self.company_market_position(),  # type: ignore
                self.company_products_services(),  # type: ignore
                self.company_management(),  # type: ignore
                self.company_legal_compliance(),  # type: ignore
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
            agents=self.agents,  # type: ignore
            tasks=self.tasks,  # type: ignore
            process=Process.sequential,  # Sequential to avoid needing a manager
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
