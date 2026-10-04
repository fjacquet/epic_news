from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import HybridSearchTool
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.geospatial_analysis_report import GeospatialAnalysisReport

# Import tool factories
from epic_news.tools.location_tools import get_location_tools
from epic_news.tools.scraper_factory import get_scraper

load_dotenv()


@CrewBase
class GeospatialAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def geospatial_researcher(self) -> Agent:
        """Creates the geospatial researcher agent with tools for data gathering"""
        # Research tools only: rendering/PDF happen in the flow, never in this agent.
        all_tools = [HybridSearchTool(), get_scraper()] + get_location_tools()

        return Agent(
            config=self.agents_config["geospatial_researcher"],  # type: ignore[index]
            verbose=True,
            tools=all_tools,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            allow_delegation=False,
            respect_context_window=True,
            max_retry_limit=3,
        )

    @agent
    def geospatial_reporter(self) -> Agent:
        """Creates the geospatial reporter agent without tools for clean output generation"""
        return Agent(
            config=self.agents_config["geospatial_reporter"],  # type: ignore[index]
            verbose=True,
            tools=[],  # No tools for reporter to ensure clean output
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def physical_location_mapping(self) -> Task:
        """Map the company's physical locations"""
        return Task(
            config=self.tasks_config["physical_location_mapping"],  # type: ignore[arg-type, index]
            agent=self.geospatial_researcher(),  # type: ignore[call-arg]
            async_execution=False,
        )

    @task
    def geospatial_risk_assessment(self) -> Task:
        """Assess geospatial risks for the company's locations"""
        return Task(
            config=self.tasks_config["geospatial_risk_assessment"],  # type: ignore[arg-type, index]
            agent=self.geospatial_researcher(),  # type: ignore[call-arg]
            async_execution=False,
        )

    @task
    def supply_chain_mapping(self) -> Task:
        """Map the company's supply chain geospatially"""
        return Task(
            config=self.tasks_config["supply_chain_mapping"],  # type: ignore[arg-type, index]
            agent=self.geospatial_researcher(),  # type: ignore[call-arg]
            async_execution=False,
        )

    @task
    def geospatial_intelligence_for_mergers_acquisitions(self) -> Task:
        """Provide geospatial intelligence for mergers and acquisitions"""
        return Task(
            config=self.tasks_config["geospatial_intelligence_for_mergers_acquisitions"],  # type: ignore[arg-type, index]
            async_execution=False,
            context=[
                self.physical_location_mapping(),  # type: ignore[call-arg]
                self.geospatial_risk_assessment(),  # type: ignore[call-arg]
                self.supply_chain_mapping(),  # type: ignore[call-arg]
            ],
            output_pydantic=GeospatialAnalysisReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Geospatial Analysis crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
            max_rpm=LLMConfig.get_max_rpm(),
        )
