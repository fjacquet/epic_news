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
    'REDDIT_SEARCH_ACROSS_SUBREDDITS',
    'HACKERNEWS_GET_FRONTPAGE',
    'FIRECRAWL_CRAWL_URLS',

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
            allow_delegation=False,  
            respect_context_window=True,
        )

    # @agent
    def chief_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config["chief_coordinator"],
            verbose=True,
            # tools=search_tools,
            allow_delegation=True,  
            # respect_context_window=True,
        )

    @agent
    def company_profile_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["company_profile_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False, 
            respect_context_window=True, 
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def job_tech_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["job_tech_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def industry_innovation_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["industry_innovation_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def competitor_mapping_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["competitor_mapping_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def social_media_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["social_media_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def regulatory_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["regulatory_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
        )

    @agent
    def cyber_threat_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["cyber_threat_analyst"],
            verbose=True,
            tools=search_tools,
            allow_delegation=False,  
            respect_context_window=True,
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
    def industry_innovation_task(self) -> Task:
        return Task(
            config=self.tasks_config["industry_innovation_task"],
            output_file="output/osint/industry_innovation_report.md",
        )

    # @task
    # def chief_coordinator_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["chief_coordinator_task"],
    #         output_file="output/osint/final.html",
    #     )

    @task
    def competitor_mapping_task(self) -> Task:
        return Task(
            config=self.tasks_config["competitor_mapping_task"],
            output_file="output/osint/competitor_mapping_report.md",
        )

    @task
    def social_media_sentiment_task(self) -> Task:
        return Task(
            config=self.tasks_config["social_media_sentiment_task"],
            output_file="output/osint/social_media_report.md",
        )

    @task
    def regulatory_overview_task(self) -> Task:
        return Task(
            config=self.tasks_config["regulatory_overview_task"],
            output_file="output/osint/regulatory_report.md",
        )

    @task
    def cyber_threat_snapshot_task(self) -> Task:
        return Task(
            config=self.tasks_config["cyber_threat_snapshot_task"],
            output_file="output/osint/cyber_threat_report.md",
        )
    @task
    def reporter_task(self) -> Task:
        return Task(
            config=self.tasks_config["reporter_task"],
            output_file="output/osint/final.html",
            context=[
                self.company_profile_task(),
                self.financial_task(),
                self.industry_innovation_task(), 
                self.competitor_mapping_task(), 
                self.social_media_sentiment_task(),
                self.regulatory_overview_task(),
                self.cyber_threat_snapshot_task(),
                ]
        )

    # @task
    # def chief_coordinator_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["chief_coordinator_task"],
    #         output_file="output/osint/final.html",
    #         context=[
    #             self.company_profile_task(),
    #             self.financial_task(),
    #             self.industry_innovation_task(), 
    #             self.competitor_mapping_task(), 
    #             self.social_media_sentiment_task(),
    #             self.regulatory_overview_task(),
    #             self.cyber_threat_snapshot_task(),
    #             ]
    #     )

  

    @crew
    def crew(self) -> Crew:
        """Creates the Osint crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            # process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True,        
            manager_agent=self.chief_coordinator(),
            llm_timeout=300,
            process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
