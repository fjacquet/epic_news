from tabnanny import verbose
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()
search_tools = toolset.get_tools(actions=[ 
    'FIRECRAWL_SEARCH',
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
    'COMPOSIO_SEARCH_NEWS_SEARCH',
    'COMPOSIO_SEARCH_TRENDS_SEARCH',
    'COMPOSIO_SEARCH_EVENT_SEARCH'],
    )


# Use only available tools for fact checking
fact_checking_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH'
],)


@CrewBase
class NewsCrew:
    """News monitoring crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=search_tools,
            # verbose=True,
            llm_timeout=300
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            tools=search_tools,
            # verbose=True,
            llm_timeout=300
        )
    
    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['fact_checker'],
            tools=fact_checking_tools,
            # verbose=True,
            llm_timeout=300
        )
    
    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],
            tools=search_tools,
            # verbose=True,
            llm_timeout=300
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        task_id = "research_task"
        
        return Task(
            config=self.tasks_config[task_id],
            output_file='output/research_results.md',
            verbose=True,
            llm_timeout=300
        )

    @task
    def analysis_task(self) -> Task:
        task_id = "analysis_task"
        return Task(
            config=self.tasks_config[task_id],
            # context=[self.research_task()],
            output_file='output/news/analysis_results.md',
            verbose=True,
            llm_timeout=300
        )
    
    @task
    def verification_task(self) -> Task:
        task_id = "verification_task"
        return Task(
            config=self.tasks_config[task_id],
            # context=[self.research_task(), self.analysis_task()],
            output_file='output/news/verification_results.md',
            verbose=True,
            llm_timeout=300
        )
    
    @task
    def editing_task(self) -> Task:
        task_id = "editing_task"
        
        return Task(
            config=self.tasks_config[task_id],
            # context=[self.research_task(), self.analysis_task(), self.verification_task()],
            output_file='output/news/report.html',  
            verbose=True,
            llm_timeout=300
        )

    @crew
    def crew(self) -> Crew:
        """Creates the News monitoring crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            allow_delegation=True,
            memory=False,
            cache=False,
            max_rpm=12,
            verbose=True,  
            respect_context_window=True,
            process=Process.hierarchical,
            manager_llm_timeout=600,  
            task_timeout=3600,  
            max_retries=3  
        )
