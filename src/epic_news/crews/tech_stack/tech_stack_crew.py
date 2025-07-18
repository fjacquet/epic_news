from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.tools.github_tools import get_github_tools
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

load_dotenv()


@CrewBase
class TechStackCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def tech_researcher(self) -> Agent:
        """Creates the tech researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool(), PDFSearchTool()]
        tech_tools = get_github_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        all_tools = search_tools + tech_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["tech_researcher"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @agent
    def tech_reporter(self) -> Agent:
        """Creates the tech reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["tech_reporter"],
            verbose=True,
            tools=[],  # No tools for reporter to ensure clean output
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @task
    def tech_stack_identification(self) -> Task:
        """Identify the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_identification"],
            async_execution=True,
            verbose=True,
        )

    @task
    def tech_stack_analysis(self) -> Task:
        """Analyze the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def open_source_contributions(self) -> Task:
        """Analyze the company's open source contributions"""
        return Task(
            config=self.tasks_config["open_source_contributions"],
            async_execution=True,
            verbose=True,
        )

    @task
    def tech_talent_assessment(self) -> Task:
        """Assess the company's tech talent"""
        return Task(
            config=self.tasks_config["tech_talent_assessment"],
            async_execution=True,
            verbose=True,
        )

    @task
    def consolidate_tech_stack_report(self) -> Task:
        """Consolidate all findings into a comprehensive tech stack report"""
        return Task(
            config=self.tasks_config["consolidate_tech_stack_report"],
            async_execution=False,
            context=[
                self.tech_stack_identification(),
                self.tech_stack_analysis(),
                self.open_source_contributions(),
                self.tech_talent_assessment(),
            ],
            output_pydantic=TechStackReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Tech Stack Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
