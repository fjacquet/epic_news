from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools
from epic_news.utils.directory_utils import ensure_output_directory

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class CrossReferenceReportCrew:
    """CrossReferenceReportCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def osint_researcher(self) -> Agent:
        """Creates the OSINT researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = get_search_tools()
        scrape_tools = get_scrape_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        directory_read_tool = DirectoryReadTool("output/osint")
        file_read_tool = FileReadTool()

        all_tools = (
            search_tools
            + scrape_tools
            + [html_to_pdf_tool, directory_read_tool, file_read_tool]
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
            llm="gpt-4.1-mini",  # Use more powerful model for complex reporting
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
        )

    @task
    def intelligence_collection_coordination(self) -> Task:
        """Coordinate intelligence collection activities"""
        return Task(
            config=self.tasks_config["intelligence_collection_coordination"],
            async_execution=True,
        )

    @task
    def intelligence_analysis_integration(self) -> Task:
        """Integrate intelligence analysis from all specialized crews"""
        return Task(
            config=self.tasks_config["intelligence_analysis_integration"],
            async_execution=True,
        )

    @task
    def intelligence_product_development(self) -> Task:
        """Develop final intelligence products"""
        return Task(
            config=self.tasks_config["intelligence_product_development"],
            async_execution=True,
        )

    # @task
    # def investigation_quality_assurance(self) -> Task:
    #     """Conduct quality assurance review"""
    #     return Task(
    #         config=self.tasks_config["investigation_quality_assurance"],
    #         async_execution=True,
    #     )

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

    @crew
    def crew(self) -> Crew:
        """Creates the CrossReferenceReportCrew crew"""
        # Ensure output directory exists for final reports
        ensure_output_directory("output/osint")

        # Implement the Two-Agent Pattern: researcher gathers data, reporter creates clean output
        # Research tasks are executed first, then the final report is generated by the reporter
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,  # Sequential to avoid needing a manager
            verbose=True,
        )
