import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from epic_news.tools.github_tools import get_github_tools
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool

# Import RAG tools
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
from epic_news.tools.report_tools import get_report_tools
from epic_news.models.report import ReportHTMLOutput

load_dotenv()

@CrewBase
class TechStackCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def tech_stack_analyst(self) -> Agent:
        """Creates the tech stack analyst agent"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        tech_tools = get_github_tools()
        rag_tools = get_rag_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        all_tools = search_tools + tech_tools + rag_tools + [html_to_pdf_tool] + get_report_tools()
        
        return Agent(
            config=self.agents_config["tech_stack_analyst"],
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
    def tech_stack_identification(self) -> Task:
        """Identify the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_identification"],
            async_execution=True,
        )

    @task
    def tech_stack_analysis(self) -> Task:
        """Analyze the company's tech stack"""
        return Task(
            config=self.tasks_config["tech_stack_analysis"],
            async_execution=True,
        )

    @task
    def open_source_contributions(self) -> Task:
        """Analyze the company's open source contributions"""
        return Task(
            config=self.tasks_config["open_source_contributions"],
            async_execution=True,
        )

    @task
    def tech_talent_assessment(self) -> Task:
        """Assess the company's tech talent"""
        return Task(
            config=self.tasks_config["tech_talent_assessment"],
            async_execution=True,
        )

    @task
    def consolidate_tech_stack_report(self) -> Task:
        """Consolidate all findings into a comprehensive tech stack report"""
        return Task(
            config=self.tasks_config["consolidate_tech_stack_report"],
            async_execution=False,
            output_pydantic=ReportHTMLOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Tech Stack Analysis crew"""
        # Ensure output directory exists for final reports
        os.makedirs("output/tech_stack", exist_ok=True)
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
