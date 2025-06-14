from crewai.project import CrewBase, agent, crew, task
from crewai import Agent, Crew, Process, Task

from composio_crewai import ComposioToolSet
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset with specialized tool groups
toolset = ComposioToolSet()
travel_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_GOOGLE_MAPS_SEARCH',
    'COMPOSIO_SEARCH_SEARCH',
    'YOUTUBE_SEARCH_YOU_TUBE'
])

accommodation_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_SHOPPING_SEARCH',
    'COMPOSIO_SEARCH_TRENDS_SEARCH'
])

content_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_NEWS_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH'
])

@CrewBase
class HolidayPlannerCrew():
    """HolidayPlanner crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_researcher"],
            tools=travel_tools,
            verbose=True,
            max_iter=15,
            allow_delegation=True
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_specialist"],
            tools=accommodation_tools,
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_architect"],
            tools=travel_tools + accommodation_tools,  # Combines both tool sets
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_manager"],
            tools=accommodation_tools,  # Focus on shopping/trends for deals
            verbose=True,
            allow_delegation=True,
        )

    @agent
    def content_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config["content_formatter"],
            tools=content_tools,
            verbose=True,
            allow_delegation=True,
        )

    @task
    def research_destination(self) -> Task:
        return Task(
            config=self.tasks_config['research_destination'],
        )

    @task
    def recommend_accommodation_and_dining(self) -> Task:
        return Task(
            config=self.tasks_config['recommend_accommodation_and_dining'],
        )

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config['plan_itinerary'],
        )

    @task
    def analyze_and_optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_and_optimize_budget'],
        )

    @task
    def format_and_translate_guide(self) -> Task:
        return Task(
            config=self.tasks_config['format_and_translate_guide'],
            output_file='output/travel_guides/itinerary.html'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        # Use a minimal LLM configuration that relies on environmental defaults
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.hierarchical,
            manager_llm="openai/gpt-4o",
            memory=True,
            cache=True,
            max_retry_limit=5,
            max_rpm=30,  # Rate limiting to avoid API issues
        )
