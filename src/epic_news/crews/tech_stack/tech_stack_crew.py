from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.tools.github_tools import get_github_tools
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.hybrid_search_tool import HybridSearchTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class TechStackCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def tech_researcher(self) -> Agent:
        """Creates the tech researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [HybridSearchTool(), get_scraper(), PDFSearchTool()]
        tech_tools = get_github_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        all_tools = search_tools + tech_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["tech_researcher"],  # type: ignore[index]
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
    def tech_reporter(self) -> Agent:
        """Creates the tech reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["tech_reporter"],  # type: ignore[index]
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
    def tech_stack_identification(self) -> Task:
        """Identify the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_identification"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def tech_stack_analysis(self) -> Task:
        """Analyze the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_analysis"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def open_source_contributions(self) -> Task:
        """Analyze the company's open source contributions"""
        return Task(
            config=self.tasks_config["open_source_contributions"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def tech_talent_assessment(self) -> Task:
        """Assess the company's tech talent"""
        return Task(
            config=self.tasks_config["tech_talent_assessment"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def consolidate_tech_stack_report(self) -> Task:
        """Consolidate all findings into a comprehensive tech stack report"""
        return Task(
            config=self.tasks_config["consolidate_tech_stack_report"],  # type: ignore[arg-type, index]
            async_execution=False,
            context=[
                self.tech_stack_identification(),  # type: ignore[call-arg]
                self.tech_stack_analysis(),  # type: ignore[call-arg]
                self.open_source_contributions(),  # type: ignore[call-arg]
                self.tech_talent_assessment(),  # type: ignore[call-arg]
            ],
            output_pydantic=TechStackReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Tech Stack Analysis crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),  # type: ignore[call-arg]
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
