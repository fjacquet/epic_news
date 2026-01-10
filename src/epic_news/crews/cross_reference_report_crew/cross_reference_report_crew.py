from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool, PDFSearchTool

from epic_news.config.llm_config import LLMConfig
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
            config=self.agents_config["osint_researcher"],  # type: ignore[index]
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            allow_delegation=True,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=5,
        )

    @agent
    def osint_reporter(self) -> Agent:
        """Creates the OSINT reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["osint_reporter"],  # type: ignore[index]
            tools=[],  # No tools for reporter to ensure clean output
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
        )

    @task
    def intelligence_requirements_planning(self) -> Task:
        """Develop comprehensive intelligence requirements"""
        return Task(
            config=self.tasks_config["intelligence_requirements_planning"],  # type: ignore[index,arg-type]
            description="Develop comprehensive intelligence requirements",
            expected_output="A structured JSON object outlining intelligence requirements",
            async_execution=True,
        )

    @task
    def intelligence_collection_coordination(self) -> Task:
        """Coordinate intelligence collection activities"""
        return Task(
            config=self.tasks_config["intelligence_collection_coordination"],  # type: ignore[index,arg-type]
            description="Coordinate intelligence collection activities",
            expected_output="A comprehensive JSON object detailing collection coordination",
            async_execution=True,
        )

    @task
    def intelligence_analysis_integration(self) -> Task:
        """Integrate intelligence analysis from all specialized crews"""
        return Task(
            config=self.tasks_config["intelligence_analysis_integration"],  # type: ignore[index,arg-type]
            description="Integrate intelligence analysis from all specialized crews",
            expected_output="A comprehensive JSON object integrating intelligence analysis",
            async_execution=True,
        )

    @task
    def intelligence_product_development(self) -> Task:
        """Develop final intelligence products"""
        return Task(
            config=self.tasks_config["intelligence_product_development"],  # type: ignore[index,arg-type]
            description="Develop final intelligence products",
            expected_output="A comprehensive JSON object serving as final intelligence products",
            async_execution=True,
        )

    @task
    def global_reporting(self) -> Task:
        """Create a global report from all generated intelligence."""
        return Task(
            config=self.tasks_config["global_reporting"],  # type: ignore[index,arg-type]
            description="Create a comprehensive global report from all generated intelligence",
            expected_output="A comprehensive global intelligence report in JSON format",
            context=[
                self.intelligence_requirements_planning(),  # type: ignore[call-arg]
                self.intelligence_collection_coordination(),  # type: ignore[call-arg]
                self.intelligence_analysis_integration(),  # type: ignore[call-arg]
                self.intelligence_product_development(),  # type: ignore[call-arg]
            ],
            output_pydantic=CrossReferenceReport,
        )

    @task
    def html_report_generation(self) -> Task:
        """Generate an HTML report from the cross-reference report."""
        return Task(
            config=self.tasks_config["html_report_generation"],  # type: ignore[index,arg-type]
            description="Generate an HTML report from the cross-reference report",
            expected_output="A professional HTML report document",
            agent=self.osint_reporter(),  # type: ignore[call-arg]
            context=[self.global_reporting()],  # type: ignore[call-arg]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrossReferenceReportCrew crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
