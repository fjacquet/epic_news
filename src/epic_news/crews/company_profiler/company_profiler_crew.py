from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from epic_news.tools.finance_tools import get_yahoo_finance_tools
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
from epic_news.utils.directory_utils import ensure_output_directory

load_dotenv()


@CrewBase
class CompanyProfilerCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def company_researcher(self) -> Agent:
        """Creates the company researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        finance_tools = get_yahoo_finance_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + finance_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["company_researcher"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @agent
    def company_reporter(self) -> Agent:
        """Creates the company reporter agent with no tools for clean output generation"""
        return Agent(
            config=self.agents_config["company_reporter"],
            verbose=True,
            tools=[],  # No tools to prevent action traces in output
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @task
    def company_core_info(self) -> Task:
        """Collect foundational information about the company"""
        return Task(
            config=self.tasks_config["company_core_info"],
            async_execution=True,
        )

    @task
    def company_history(self) -> Task:
        """Research and document the company history"""
        return Task(
            config=self.tasks_config["company_history"],
            async_execution=True,
        )

    @task
    def company_financials(self) -> Task:
        """Analyze the company financial statements"""
        return Task(
            config=self.tasks_config["company_financials"],
            async_execution=True,
        )

    @task
    def company_market_position(self) -> Task:
        """Evaluate the company market position"""
        return Task(
            config=self.tasks_config["company_market_position"],
            async_execution=True,
        )

    @task
    def company_products_services(self) -> Task:
        """Document the company products and services"""
        return Task(
            config=self.tasks_config["company_products_services"],
            async_execution=True,
        )

    @task
    def company_management(self) -> Task:
        """Research and analyze the company management team"""
        return Task(
            config=self.tasks_config["company_management"],
            async_execution=True,
        )

    @task
    def company_legal_compliance(self) -> Task:
        """Research and document any legal or regulatory issues"""
        return Task(
            config=self.tasks_config["company_legal_compliance"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Company Profiler crew"""
        # Ensure output directory exists for final reports
        ensure_output_directory("output/company_profiler")
        ensure_output_directory("output/osint")

        # Implement the Two-Agent Pattern:
        # 1. Research tasks are assigned to company_researcher (with tools)
        # 2. Final output task is assigned to company_reporter (without tools)
        # This prevents action traces from contaminating the output
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,  # Hierarchical for parallel execution
            verbose=True,
        )
