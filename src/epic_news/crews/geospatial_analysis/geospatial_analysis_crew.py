from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.models.crews.geospatial_analysis_report import GeospatialAnalysisReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool

# Import tool factories
from epic_news.tools.location_tools import get_location_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

load_dotenv()


@CrewBase
class GeospatialAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def geospatial_researcher(self) -> Agent:
        """Creates the geospatial researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool(), PDFSearchTool()]
        location_tools = get_location_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + location_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["geospatial_researcher"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=5,
            max_iter=5,
            max_retry_limit=3,
            max_rpm=10,
        )

    @agent
    def geospatial_reporter(self) -> Agent:
        """Creates the geospatial reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["geospatial_reporter"],
            verbose=True,
            tools=[],  # No tools for reporter to ensure clean output
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @task
    def physical_location_mapping(self) -> Task:
        """Map the company's physical locations"""
        return Task(
            config=self.tasks_config["physical_location_mapping"],
            async_execution=True,
            verbose=True,
        )

    @task
    def geospatial_risk_assessment(self) -> Task:
        """Assess geospatial risks for the company's locations"""
        return Task(
            config=self.tasks_config["geospatial_risk_assessment"],
            async_execution=True,
            verbose=True,
        )

    @task
    def supply_chain_mapping(self) -> Task:
        """Map the company's supply chain geospatially"""
        return Task(
            config=self.tasks_config["supply_chain_mapping"],
            async_execution=True,
            verbose=True,
        )

    @task
    def geospatial_intelligence_for_mergers_acquisitions(self) -> Task:
        """Provide geospatial intelligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["geospatial_intelligence_for_mergers_acquisitions"],
            async_execution=False,
            context=[
                self.physical_location_mapping(),
                self.geospatial_risk_assessment(),
                self.supply_chain_mapping(),
            ],
            output_pydantic=GeospatialAnalysisReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Geospatial Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
