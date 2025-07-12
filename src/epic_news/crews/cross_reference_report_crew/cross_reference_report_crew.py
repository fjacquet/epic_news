from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool, PDFSearchTool

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools


@CrewBase
class CrossReferenceReportCrew:
    """CrossReferenceReportCrew crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def osint_researcher(self) -> Agent:
        """Creates the OSINT researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = get_search_tools()
        scrape_tools = get_scrape_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        directory_read_tool = DirectoryReadTool("output/osint")
        file_read_tool = FileReadTool()
        pdf_search_tool = PDFSearchTool()

        all_tools = (
            search_tools
            + scrape_tools
            + [html_to_pdf_tool, directory_read_tool, file_read_tool, pdf_search_tool]
            + get_report_tools()
        )

        return Agent(
            config=self.agents_config["osint_researcher"],
            verbose=True,
            tools=all_tools,
            llm="gpt-4.1-mini",  # Use more powerful model for complex cross-referencing
            allow_delegation=True,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=5,
        )

    @agent
    def osint_reporter(self) -> Agent:
        """Creates the OSINT reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["osint_reporter"],
            verbose=True,
            tools=[],  # No tools for reporter to ensure clean output
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @task
    def intelligence_requirements_planning(self) -> Task:
        """Develop comprehensive intelligence requirements"""
        return Task(
            config=self.tasks_config["intelligence_requirements_planning"],
            async_execution=True,
            verbose=True,
        )

    @task
    def intelligence_collection_coordination(self) -> Task:
        """Coordinate intelligence collection activities"""
        return Task(
            config=self.tasks_config["intelligence_collection_coordination"],
            async_execution=True,
            verbose=True,
        )

    @task
    def intelligence_analysis_integration(self) -> Task:
        """Integrate intelligence analysis from all specialized crews"""
        return Task(
            config=self.tasks_config["intelligence_analysis_integration"],
            async_execution=True,
            verbose=True,
        )

    @task
    def intelligence_product_development(self) -> Task:
        """Develop final intelligence products"""
        return Task(
            config=self.tasks_config["intelligence_product_development"],
            async_execution=True,
            verbose=True,
        )

    @task
    def global_reporting(self) -> Task:
        """Create a global report from all generated intelligence."""
        return Task(
            config=self.tasks_config["global_reporting"],
            async_execution=False,
            context=[
                self.intelligence_requirements_planning(),
                self.intelligence_collection_coordination(),
                self.intelligence_analysis_integration(),
                self.intelligence_product_development(),
            ],
            output_pydantic=CrossReferenceReport,
        )

    @task
    def html_report_generation(self) -> Task:
        """Generate an HTML report from the cross-reference report."""
        return Task(
            config=self.tasks_config["html_report_generation"],
            agent=self.osint_reporter(),
            context=[self.global_reporting()],
            async_execution=False,
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
