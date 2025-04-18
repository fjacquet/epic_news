from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
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
class OsintCrew():
    """Osint crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            tools=search_tools,
        )

    @agent
    def chief_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["chief_coordinator"],
            verbose=True,
            tools=search_tools,
        )

    @agent
    def company_profile_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["company_profile_analyst"],
            verbose=True,
            tools=search_tools,
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],
            verbose=True,
            tools=search_tools,
        )

    @agent
    def job_tech_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["job_tech_analyst"],
            verbose=True,
            tools=search_tools,
        )

    @agent
    def industry_innovation_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["industry_innovation_analyst"],
            verbose=True,
            tools=search_tools,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def company_profile_task(self) -> Task:
        return Task(
            config=self.tasks_config["company_profile_task"],
            output_file="output/osint/company_profile.md",
        )

    @task
    def financial_task(self) -> Task:
        return Task(
            config=self.tasks_config["financial_task"],
            output_file="output/osint/financial_report.md",
        )

    @task
    def job_tech_task(self) -> Task:
        return Task(
            config=self.tasks_config["job_tech_task"],
            output_file="output/osint/job_tech_report.md"
        )

    @task
    def industry_innovation_task(self) -> Task:
        return Task(
            config=self.tasks_config["industry_innovation_task"],
            output_file="output/osint/industry_innovation_report.md",
        )

    @task
    def chief_coordinator_task(self) -> Task:
        return Task(
            config=self.tasks_config["chief_coordinator_task"],
            output_file="output/osint/final.md"
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Osint crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
