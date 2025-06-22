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
class HRIntelligenceCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


    @agent
    def hr_intelligence_analyst(self) -> Agent:
        """Creates the HR intelligence analyst agent"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        rag_tools = get_rag_tools()
        html_to_pdf_tool = HtmlToPdfTool()

        all_tools = search_tools + rag_tools + [html_to_pdf_tool] + get_report_tools()

        return Agent(
            config=self.agents_config["hr_intelligence_analyst"],
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
    def leadership_team_assessment(self) -> Task:
        """Assess the company's leadership team"""
        return Task(
            config=self.tasks_config["leadership_team_assessment"],
            async_execution=True,
        )

    @task
    def employee_sentiment_analysis(self) -> Task:
        """Analyze employee reviews and sentiment"""
        return Task(
            config=self.tasks_config["employee_sentiment_analysis"],
            async_execution=True,
        )

    @task
    def organizational_culture_assessment(self) -> Task:
        """Assess the company's organizational culture"""
        return Task(
            config=self.tasks_config["organizational_culture_assessment"],
            async_execution=True,
        )

    @task
    def talent_acquisition_strategy(self) -> Task:
        """Analyze the company's talent acquisition strategy"""
        return Task(
            config=self.tasks_config["talent_acquisition_strategy"],
            async_execution=True,
        )

    @task
    def format_hr_intelligence_report(self) -> Task:
        """Format the comprehensive HR intelligence report"""
        return Task(
            config=self.tasks_config["format_hr_intelligence_report"],
            async_execution=False,
            output_pydantic=ReportHTMLOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HR Intelligence Analysis crew"""
        # Ensure output directory exists for final reports
        os.makedirs("output/hr_intelligence", exist_ok=True)

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
