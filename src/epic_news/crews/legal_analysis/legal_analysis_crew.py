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
class LegalAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def legal_analyst(self) -> Agent:
        """Creates the legal analyst agent"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        rag_tools = get_rag_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + rag_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["legal_analyst"],
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
    def legal_compliance_assessment(self) -> Task:
        """Assess the company's legal compliance status"""
        return Task(
            config=self.tasks_config["legal_compliance_assessment"],
            async_execution=True,
        )

    @task
    def intellectual_property_analysis(self) -> Task:
        """Analyze the company's intellectual property portfolio"""
        return Task(
            config=self.tasks_config["intellectual_property_analysis"],
            async_execution=True,
        )

    @task
    def regulatory_risk_assessment(self) -> Task:
        """Assess the company's regulatory risks"""
        return Task(
            config=self.tasks_config["regulatory_risk_assessment"],
            async_execution=True,
        )

    @task
    def litigation_history_analysis(self) -> Task:
        """Analyze the company's litigation history"""
        return Task(
            config=self.tasks_config["litigation_history_analysis"],
            async_execution=True,
        )

    @task
    def mergers_and_acquisitions_due_diligence(self) -> Task:
        """Conduct legal due diligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["mergers_and_acquisitions_due_diligence"],
            async_execution=False,
            output_pydantic=ReportHTMLOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Legal Analysis crew"""
        # Ensure output directory exists for final reports
        os.makedirs("output/legal_analysis", exist_ok=True)

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
