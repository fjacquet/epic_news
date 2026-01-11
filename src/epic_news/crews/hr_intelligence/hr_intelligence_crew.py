from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.hr_intelligence_report import HRIntelligenceReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.hybrid_search_tool import HybridSearchTool

# Import RAG tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class HRIntelligenceCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def hr_researcher(self) -> Agent:
        """Creates the HR researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [HybridSearchTool(), get_scraper(), PDFSearchTool()]
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["hr_researcher"],  # type: ignore[index]
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
        )

    @agent
    def hr_reporter(self) -> Agent:
        """Creates the HR reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["hr_reporter"],  # type: ignore[index]
            verbose=True,
            tools=[],  # No tools for reporter to ensure clean output
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
        )

    @task
    def leadership_team_assessment(self) -> Task:
        """Assess the company's leadership team"""
        return Task(
            config=self.tasks_config["leadership_team_assessment"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def employee_sentiment_analysis(self) -> Task:
        """Analyze employee reviews and sentiment"""
        return Task(
            config=self.tasks_config["employee_sentiment_analysis"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def organizational_culture_assessment(self) -> Task:
        """Assess the company's organizational culture"""
        return Task(
            config=self.tasks_config["organizational_culture_assessment"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def talent_acquisition_strategy(self) -> Task:
        """Analyze the company's talent acquisition strategy"""
        return Task(
            config=self.tasks_config["talent_acquisition_strategy"],  # type: ignore[arg-type, index]
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def format_hr_intelligence_report(self) -> Task:
        """Format the comprehensive HR intelligence report"""
        return Task(
            config=self.tasks_config["format_hr_intelligence_report"],  # type: ignore[arg-type, index]
            async_execution=False,
            context=[
                self.leadership_team_assessment(),  # type: ignore[call-arg]
                self.employee_sentiment_analysis(),  # type: ignore[call-arg]
                self.organizational_culture_assessment(),  # type: ignore[call-arg]
                self.talent_acquisition_strategy(),  # type: ignore[call-arg]
            ],
            output_pydantic=HRIntelligenceReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HR Intelligence Analysis crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),  # type: ignore[call-arg]
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
