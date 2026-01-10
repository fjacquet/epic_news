from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.web_presence_report import WebPresenceReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class WebPresenceCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def web_researcher(self) -> Agent:
        """Creates the web researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), get_scraper(), PDFSearchTool()]
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["web_researcher"],
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=5,
            max_retry_limit=3,
        )

    @agent
    def web_reporter(self) -> Agent:
        """Creates the web reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["web_reporter"],
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
            verbose=True,
        )

    @task
    def domain_infrastructure_analysis(self) -> Task:
        """Analyze the target's domain infrastructure and technical footprint"""
        return Task(
            config=self.tasks_config["domain_infrastructure_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def data_leak_analysis(self) -> Task:
        """Analyze potential data leaks and breaches related to the target"""
        return Task(
            config=self.tasks_config["data_leak_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def competitive_web_presence_analysis(self) -> Task:
        """Analyze the web presence of competitors to identify best practices"""
        return Task(
            config=self.tasks_config["competitive_web_presence_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def consolidate_web_presence_report(self) -> Task:
        """Consolidate all web presence findings into a comprehensive report"""
        return Task(
            config=self.tasks_config["consolidate_web_presence_report"],
            async_execution=False,
            context=[
                self.web_presence_audit(),
                self.social_media_footprint(),
                self.domain_infrastructure_analysis(),
                self.data_leak_analysis(),
                self.competitive_web_presence_analysis(),
            ],
            output_pydantic=WebPresenceReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Web Presence Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            reasoning=True,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
        )
