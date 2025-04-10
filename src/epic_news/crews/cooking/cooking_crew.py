from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()

search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_TAVILY_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
],
)
@CrewBase
class CookingCrew:
    """Cooking expertise crew for finding recipes, ingredients, and preparation steps"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def recipe_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['recipe_finder'],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )
    
    @agent
    def ingredient_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['ingredient_specialist'],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )
    
    @agent
    def preparation_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['preparation_expert'],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )
    
    @task
    def recipe_finding_task(self) -> Task:
        return Task(
            config=self.tasks_config['recipe_finding_task'],
            output_file='output/cooking/recipe_finding.md'
        )
    
    @task
    def ingredient_listing_task(self) -> Task:
        return Task(
            config=self.tasks_config['ingredient_listing_task'],
            context=[self.recipe_finding_task()],
            output_file='output/cooking/ingredient_listing.md'
        )
    
    @task
    def preparation_steps_task(self) -> Task:
        return Task(
            config=self.tasks_config['preparation_steps_task'],
            context=[self.recipe_finding_task(), self.ingredient_listing_task()],
            output_file='output/cooking/preparation_steps.md'
        )
    
    @task
    def complete_recipe_task(self) -> Task:
        return Task(
            config=self.tasks_config['complete_recipe_task'],
            context=[
                self.recipe_finding_task(), 
                self.ingredient_listing_task(), 
                self.preparation_steps_task()
            ],
            output_file='output/cooking/recipe.html'
        )


    @crew
    def crew(self) -> Crew:
        """Creates a laser-focused cooking crew for finding recipes, ingredients, and preparation steps"""
        
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            verbose=True,
            memory=True,
            cache=True,
            process=Process.sequential,
            manager_llm_timeout=300,  # 5 minutes timeout for manager LLM
            task_timeout=1800, # 30 minutes timeout for each task
        )
