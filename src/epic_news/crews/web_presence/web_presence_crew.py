import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from epic_news.models.report import ReportHTMLOutput
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool

# Import RAG tools
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

load_dotenv()

@CrewBase
class WebPresenceCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def web_presence_investigator(self) -> Agent:
        """Creates the web presence investigator agent"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        rag_tools = get_rag_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + rag_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["web_presence_investigator"],
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

    @task
    def web_presence_audit(self) -> Task:
        """Conduct a comprehensive audit of the target's web presence"""
        return Task(
            config=self.tasks_config["web_presence_audit"],
            async_execution=True,
        )

    @task
    def social_media_footprint(self) -> Task:
        """Analyze the target's social media footprint across platforms"""
        return Task(
            config=self.tasks_config["social_media_footprint"],
            async_execution=True,
        )

    @task
    def domain_infrastructure_analysis(self) -> Task:
        """Analyze the target's domain infrastructure and technical footprint"""
        return Task(
            config=self.tasks_config["domain_infrastructure_analysis"],
            async_execution=True,
        )

    @task
    def data_leak_analysis(self) -> Task:
        """Analyze potential data leaks and breaches related to the target"""
        return Task(
            config=self.tasks_config["data_leak_analysis"],
            async_execution=True,
        )

    @task
    def competitive_web_presence_analysis(self) -> Task:
        """Analyze the web presence of competitors to identify best practices"""
        return Task(
            config=self.tasks_config["competitive_web_presence_analysis"],
            async_execution=True,
        )

    @task
    def consolidate_web_presence_report(self) -> Task:
        """Consolidate all web presence findings into a comprehensive report"""
        return Task(
            config=self.tasks_config["consolidate_web_presence_report"],
            async_execution=False,
            output_pydantic=ReportHTMLOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Web Presence Analysis crew"""
        # Ensure output directory exists for final reports
        os.makedirs("output/web_presence", exist_ok=True)

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
