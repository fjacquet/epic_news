from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool, SerperDevTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.legal_analysis_report import LegalAnalysisReport
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool

# Import RAG tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class LegalAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def legal_researcher(self) -> Agent:
        """Creates the legal researcher agent with tools for data gathering"""
        # Get all tools
        search_tools = [SerperDevTool(), get_scraper(), PDFSearchTool()]
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["legal_researcher"],
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            allow_delegation=False,
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=5,
        )

    @agent
    def legal_reporter(self) -> Agent:
        """Creates the legal reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["legal_reporter"],
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
    def legal_compliance_assessment(self) -> Task:
        """Assess the company's legal compliance status"""
        return Task(
            config=self.tasks_config["legal_compliance_assessment"],
            async_execution=True,
            verbose=True,
        )

    @task
    def intellectual_property_analysis(self) -> Task:
        """Analyze the company's intellectual property portfolio"""
        return Task(
            config=self.tasks_config["intellectual_property_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def regulatory_risk_assessment(self) -> Task:
        """Assess the company's regulatory risks"""
        return Task(
            config=self.tasks_config["regulatory_risk_assessment"],
            async_execution=True,
            verbose=True,
        )

    @task
    def litigation_history_analysis(self) -> Task:
        """Analyze the company's litigation history"""
        return Task(
            config=self.tasks_config["litigation_history_analysis"],
            async_execution=True,
            verbose=True,
        )

    @task
    def mergers_and_acquisitions_due_diligence(self) -> Task:
        """Conduct legal due diligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["mergers_and_acquisitions_due_diligence"],
            async_execution=False,
            context=[
                self.legal_compliance_assessment(),
                self.intellectual_property_analysis(),
                self.regulatory_risk_assessment(),
                self.litigation_history_analysis(),
            ],
            output_pydantic=LegalAnalysisReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Legal Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
