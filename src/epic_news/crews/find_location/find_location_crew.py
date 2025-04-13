from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()

search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
],)


@CrewBase
class FindLocationCrew():
    """Location Finder crew that helps analyze user requirements and find suitable locations"""

    # Configuration files
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def location_requirements_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['location_requirements_analyst'],
            tools=search_tools,
            verbose=True
        )

    @agent
    def location_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['location_researcher'],
            tools=search_tools,
            verbose=True
        )

    @agent
    def location_recommendations_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['location_recommendations_specialist'],
            tools=search_tools,
            verbose=True
        )

    @task
    def requirements_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['requirements_analysis_task']
        )

    @task
    def location_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['location_research_task'],
            depends_on=[self.requirements_analysis_task]
        )

    @task
    def location_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['location_recommendation_task'],
            depends_on=[self.location_research_task]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LocationFinder crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
