import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool

# Import RAG tools
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

load_dotenv()

@CrewBase
class GeospatialAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    
    @agent
    def geospatial_analyst(self) -> Agent:
        """Creates the geospatial analyst agent"""
        # Get all tools
        search_tools = [SerperDevTool(), ScrapeNinjaTool()]
        rag_tools = get_rag_tools()
        html_to_pdf_tool = HtmlToPdfTool()
        
        all_tools = search_tools + rag_tools + [html_to_pdf_tool]
        
        return Agent(
            config=self.agents_config["geospatial_analyst"],
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
    def physical_location_mapping(self) -> Task:
        """Map the company's physical locations"""
        return Task(
            config=self.tasks_config["physical_location_mapping"],
            async_execution=True,
        )

    @task
    def geospatial_risk_assessment(self) -> Task:
        """Assess geospatial risks for the company's locations"""
        return Task(
            config=self.tasks_config["geospatial_risk_assessment"],
            async_execution=True,
        )

    @task
    def supply_chain_mapping(self) -> Task:
        """Map the company's supply chain geospatially"""
        return Task(
            config=self.tasks_config["supply_chain_mapping"],
            async_execution=True,
        )

    @task
    def geospatial_intelligence_for_mergers_acquisitions(self) -> Task:
        """Provide geospatial intelligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["geospatial_intelligence_for_mergers_acquisitions"],
            async_execution=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Geospatial Analysis crew"""
        # Ensure output directory exists for final reports
        os.makedirs("output/geospatial_analysis", exist_ok=True)
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
