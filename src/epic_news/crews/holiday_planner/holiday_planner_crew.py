from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.models.crews.holiday_planner_report import HolidayPlannerReport
from epic_news.tools.exchange_rate_tool import ExchangeRateTool
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools, get_youtube_tools

load_dotenv()


@CrewBase
class HolidayPlannerCrew:
    """HolidayPlanner crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_researcher"],
            tools=get_search_tools() + get_youtube_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm="gpt-4.1-mini",
            verbose=False,
            reasoning=True,
            allow_delegation=True,
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_specialist"],
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm="gpt-4.1-mini",
            verbose=False,
            reasoning=True,
            allow_delegation=True,
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_architect"],
            tools=get_search_tools() + get_scrape_tools() + get_youtube_tools() + [ExchangeRateTool()],
            llm="gpt-4.1-mini",
            verbose=False,
            reasoning=True,
            allow_delegation=True,
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_manager"],
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            llm="gpt-4.1-mini",
            verbose=False,
            allow_delegation=False,
        )

    @agent
    def content_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config["content_formatter"],
            tools=get_search_tools() + get_scrape_tools() + [ExchangeRateTool()],
            verbose=False,
            allow_delegation=False,
        )

    @task
    def research_destination(self) -> Task:
        return Task(config=self.tasks_config["research_destination"], async_execution=True)

    @task
    def recommend_accommodation_and_dining(self) -> Task:
        return Task(config=self.tasks_config["recommend_accommodation_and_dining"], async_execution=True)

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config["plan_itinerary"],
            async_execution=False,
        )

    @task
    def analyze_and_optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_and_optimize_budget"],
            async_execution=False,
        )

    @task
    def format_and_translate_guide(self) -> Task:
        return Task(
            config=self.tasks_config["format_and_translate_guide"],
            async_execution=False,
            output_pydantic=HolidayPlannerReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
            max_retry_limit=5,
            max_rpm=30,
        )
