from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()

# Get search tools for finding company and contact information
search_tools = toolset.get_tools(actions=[
    'COMPOSIO_SEARCH_SEARCH',
    'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
    'COMPOSIO_SEARCH_FINANCE_SEARCH',
    'COMPOSIO_SEARCH_NEWS_SEARCH',
])


@CrewBase
class ContactFinderCrew():
    """ContactFinder crew for finding sales contacts at target companies"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def org_structure_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["org_structure_analyst"],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def sales_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist"],
            tools=search_tools,
            verbose=True,
            llm_timeout=300
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_company_task"],
            agent=self.company_researcher(),
            output_file="output/contact_finder/company_research.md",
        )

    @task
    def analyze_org_structure_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_org_structure_task"],
            agent=self.org_structure_analyst(),
            output_file="output/contact_finder/organization_structure.md",
        )

    @task
    def find_key_contacts_task(self) -> Task:
        return Task(
            config=self.tasks_config["find_key_contacts_task"],
            agent=self.contact_finder(),
            output_file="output/contact_finder/key_contacts.md",
        )

    @task
    def develop_approach_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["develop_approach_strategy_task"],
            agent=self.sales_strategist(),
            output_file="output/contact_finder/approach_strategy.html",
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ContactFinder crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,
            manager_llm_timeout=300,  # 5 minutes timeout for manager LLM
            task_timeout=1800,  # 30 minutes timeout for each task
            manager_llm="gpt-4o",
        )
