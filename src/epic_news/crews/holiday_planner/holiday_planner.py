from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv
import os
load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()
search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_NEWS_SEARCH',
    'COMPOSIO_SEARCH_TAVILY_SEARCH',
    'COMPOSIO_SEARCH_SEARCH',
],)

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
    def budget_navigator(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_navigator"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def destination_expert(self) -> Agent:
        return Agent(
            config=self.agents_config["destination_expert"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def accommodation_ace(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_ace"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def enchantment_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["enchantment_architect"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def culinary_compass(self) -> Agent:
        return Agent(
            config=self.agents_config["culinary_compass"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def local_whisperer(self) -> Agent:
        return Agent(
            config=self.agents_config["local_whisperer"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def logistics_liaison(self) -> Agent:
        return Agent(
            config=self.agents_config["logistics_liaison"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def travel_logistics_planner(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_logistics_planner"],
            tools=search_tools,
            verbose=True,
        )

    @agent
    def itinerary_translator(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_translator"],
            tools=search_tools,
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def PlanTravel(self) -> Task:
        return Task(
            config=self.tasks_config["PlanTravel"],
            output_file="output/holiday/PlanTravel_en.md",
            verbose=True,
        )

    @task
    def ValidateLocation(self) -> Task:
        return Task(
            config=self.tasks_config["ValidateLocation"],
            output_file="output/holiday/ValidateLocation_en.md",    
            verbose=True,
        )

    @task
    def DefineBudget(self) -> Task:
        return Task(
            config=self.tasks_config["DefineBudget"],
            output_file="output/holiday/DefineBudget_en.md",
            verbose=True,
        )

    @task
    def ValidateLocation(self) -> Task:
        return Task(
            config=self.tasks_config["ValidateLocation"],
            output_file="output/holiday/ValidateLocation_en.md",
            verbose=True,
        )

    @task
    def FindAccommodation(self) -> Task:
        return Task(
            config=self.tasks_config["FindAccommodation"],
            output_file="output/holiday/FindAccommodation_en.md",
            verbose=True,
        )

    @task
    def CurateActivities(self) -> Task:
        return Task(
            config=self.tasks_config["CurateActivities"],
            output_file="output/holiday/CurateActivities_en.md",
            verbose=True,
        )

    @task
    def RecommendDining(self) -> Task:
        return Task(
            config=self.tasks_config["RecommendDining"],
            output_file="output/holiday/RecommendDining_en.md",
            verbose=True,
        )

    @task
    def LocalInsights(self) -> Task:
        return Task(
            config=self.tasks_config["LocalInsights"],
            output_file="output/holiday/{destination}_en.md",   
            verbose=True,
        )


    @task
    def FinalizeItinerary(self) -> Task:
        return Task(
            config=self.tasks_config["FinalizeItinerary"],
            output_file="output/holiday/FinalizeItinerary.md",   
            verbose=True,
        )


    @task
    def TranslateToFrench(self) -> Task:
        return Task(
            config=self.tasks_config["TranslateToFrench"],
            output_file="output/holiday/destination.md",        
            verbose=True,
        )

 
    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge


        return Crew(
            agents=self.agents, # Automatically created by the @task decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
        )
