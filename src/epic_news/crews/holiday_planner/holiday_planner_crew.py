from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from composio_crewai import ComposioToolSet, App, Action
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()
search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_NEWS_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_SHOPPING_SEARCH',
    'COMPOSIO_SEARCH_GOOGLE_MAPS_SEARCH',
    'COMPOSIO_SEARCH_TRENDS_SEARCH',
    'YOUTUBE_SEARCH_YOU_TUBE',
],)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class HolidayPlannerCrew():
    """HolidayPlanner crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_researcher'],
            tools=search_tools,
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['accommodation_specialist'],
            tools=search_tools,
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_architect'],
            tools=search_tools,
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['budget_manager'],
            tools=search_tools,
        )

    @agent
    def content_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['content_formatter'],

        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_destination(self) -> Task:
        return Task(
            config=self.tasks_config['research_destination'],
        )

    @task
    def plan_accommodation_and_dining(self) -> Task:
        return Task(
            config=self.tasks_config['plan_accommodation_and_dining'],
        )

    @task
    def create_detailed_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config['create_detailed_itinerary'],
        )

    @task
    def optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_budget'],
        )

    @task
    def format_and_translate(self) -> Task:
        return Task(
            config=self.tasks_config['format_and_translate'],
            output_file='output/travel_guides/itinerary.html'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            memory=True,
            cache=True,
            verbose=True,
        )
