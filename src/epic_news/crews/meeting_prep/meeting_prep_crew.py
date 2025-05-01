from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()
search_tools = toolset.get_tools(actions=['COMPOSIO_SEARCH_TAVILY_SEARCH'],)


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators




@CrewBase
class MeetingPrepCrew():
    """MeetingPrep crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        """Initialize the MeetingPrepCrew with default values."""
        self.topic = ""
        self.sendto = ""
        self.company = ""
        self.participants = []  # Changed to list to match original template
        self.context = ""
        self.objective = ""
        self.prior_interactions = ""
        


    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def lead_researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_researcher_agent"],
            tools=search_tools, 
            allow_delegation=False,
            verbose=True,
            respect_context_window=True
        )

    @agent
    def product_specialist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["product_specialist_agent"],
            tools=search_tools, 
            allow_delegation=False,
            verbose=True,
            respect_context_window=True
        )

    @agent
    def sales_strategist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist_agent"],
            tools=search_tools, 
            verbose=True,
            respect_context_window=True
        )

    @agent
    def briefing_coordinator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["briefing_coordinator_agent"],
            tools=[],
            verbose=True,
            respect_context_window=True
        )


    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.lead_researcher_agent(),
        )

    @task
    def product_alignment_task(self) -> Task:
        return Task(
            config=self.tasks_config["product_alignment_task"],
            agent=self.product_specialist_agent(),
        )

    @task
    def sales_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["sales_strategy_task"],
            agent=self.sales_strategist_agent(),
        )

    @task
    def meeting_preparation_task(self) -> Task:
        return Task(
            config=self.tasks_config["meeting_preparation_task"],
            agent=self.briefing_coordinator_agent(),
            output_file="output/meeting/meeting_preparation.html"
        )
        
    @crew
    def crew(self) -> Crew:
        """Creates the MeetingPrep crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            llm_timeout=300,
            
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
    