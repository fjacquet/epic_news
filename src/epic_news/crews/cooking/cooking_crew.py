from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()

search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
],
)

@CrewBase
class CookingCrew:
    """
    Cooking crew that creates comprehensive recipes optimized for Thermomix when appropriate
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def recipe_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['recipe_expert'],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )
    
    @task
    def comprehensive_recipe_task(self) -> Task:
        return Task(
            config=self.tasks_config['comprehensive_recipe_task'],
            output_file='output/cooking/recipe.html'
        )

    @crew
    def crew(self) -> Crew:
        """Creates a streamlined cooking crew for comprehensive recipe creation"""
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            memory=False,
            cache=False,
            process=Process.sequential,
            manager_llm_timeout=300,  # 5 minutes timeout for manager LLM
            task_timeout=1800, # 30 minutes timeout for each task
        )
