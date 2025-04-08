from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv
import os

from epic_news.crews.news.checkpointing import CheckpointManager, task_callback

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()
search_tools = toolset.get_tools(actions=['COMPOSIO_SEARCH_TAVILY_SEARCH'],)


fact_checking_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_NEWS_SEARCH',
    'COMPOSIO_SEARCH_TAVILY_SEARCH',
    'FIRECRAWL_EXTRACT'
],)

# Set environment variables to increase timeouts
os.environ["LITELLM_TIMEOUT"] = "300"  # 5 minutes timeout
os.environ["OPENAI_TIMEOUT"] = "300"   # 5 minutes timeout

# Initialize checkpoint manager
checkpoint_manager = CheckpointManager(
    checkpoint_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../..", "checkpoints")
)

@CrewBase
class NewsCrew:
    """News monitoring crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Create necessary directories
        os.makedirs("output", exist_ok=True)

        
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
        
        # Check if we have a checkpoint for this task
        checkpoint = checkpoint_manager.load_checkpoint(task_id)
        if checkpoint:
            print(f" Resuming from checkpoint for {task_id}")
            # Create a task with the checkpoint data
            return Task(
                config=self.tasks_config[task_id],
                output_file='output/research_results.md',
                description=f"IMPORTANT: Resume from previous work. Previous output: {checkpoint['output']}",
                callback=task_callback
            )
        
        return Task(
            config=self.tasks_config[task_id],
            output_file='output/research_results.md',
            callback=task_callback
        )

    @task
    def analysis_task(self) -> Task:
        task_id = "analysis_task"
        
        # Check if we have a checkpoint for this task
        checkpoint = checkpoint_manager.load_checkpoint(task_id)
        if checkpoint:
            print(f" Resuming from checkpoint for {task_id}")
            # Create a task with the checkpoint data
            return Task(
                config=self.tasks_config[task_id],
                context=[self.research_task()],
                output_file='output/analysis_results.md',
                description=f"IMPORTANT: Resume from previous work. Previous output: {checkpoint['output']}",
                callback=task_callback
            )
        
        return Task(
            config=self.tasks_config[task_id],
            context=[self.research_task()],
            output_file='output/analysis_results.md',
            callback=task_callback
        )
    
    @task
    def verification_task(self) -> Task:
        task_id = "verification_task"
        
        # Check if we have a checkpoint for this task
        checkpoint = checkpoint_manager.load_checkpoint(task_id)
        if checkpoint:
            print(f" Resuming from checkpoint for {task_id}")
            # Create a task with the checkpoint data
            return Task(
                config=self.tasks_config[task_id],
                context=[self.research_task(), self.analysis_task()],
                output_file='output/verification_results.md',
                description=f"IMPORTANT: Resume from previous work. Previous output: {checkpoint['output']}",
                callback=task_callback
            )
        
        return Task(
            config=self.tasks_config[task_id],
            context=[self.research_task(), self.analysis_task()],
            output_file='output/verification_results.md',
            callback=task_callback
        )
    
    @task
    def editing_task(self) -> Task:
        task_id = "editing_task"
        
        # Check if we have a checkpoint for this task
        checkpoint = checkpoint_manager.load_checkpoint(task_id)
        if checkpoint:
            print(f" Resuming from checkpoint for {task_id}")
            # Create a task with the checkpoint data
            return Task(
                config=self.tasks_config[task_id],
                context=[self.research_task(), self.analysis_task(), self.verification_task()],
                output_file='output/news_report.md',  # Changed from editing_results.md to news_report.md
                description=f"IMPORTANT: Resume from previous work. Previous output: {checkpoint['output']}",
                callback=task_callback
            )
        
        return Task(
            config=self.tasks_config[task_id],
            context=[self.research_task(), self.analysis_task(), self.verification_task()],
            output_file='output/news_report.md',  # Changed from editing_results.md to news_report.md
            callback=task_callback
        )

    @crew
    def crew(self) -> Crew:
        """Creates the News monitoring crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            allow_delegation=True,
            memory=True,
            verbose=True,  
            process=Process.sequential,
            manager_llm="gpt-4o",
            max_rpm=5,  # Reduced rate limiting to avoid overwhelming the API
            manager_llm_timeout=600,  # 10 minutes timeout for manager LLM (increased from 5 minutes)
            task_timeout=3600,  # 60 minutes timeout for each task (increased from 30 minutes)
            max_retries=3  # Add retries for failed tasks
        )
