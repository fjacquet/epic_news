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
    'COMPOSIO_SEARCH_TAVILY_SEARCH',
])

# Set environment variables to increase timeouts
os.environ["LITELLM_TIMEOUT"] = "300"  # 5 minutes timeout
os.environ["OPENAI_TIMEOUT"] = "300"   # 5 minutes timeout

@CrewBase
class ContactFinderCrew():
    """ContactFinder crew for finding sales contacts at target companies"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the ContactFinder crew"""
        # Create necessary directories
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/contact_finder", exist_ok=True)
        
        # Default values
        self.company = "iFage | Fondation pour la formation des adultes"
        self.our_product = "PowerStore"
        self.sendto = "fred.jacquet@gmail.com"

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            tools=search_tools,
            allow_delegation=False,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def org_structure_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["org_structure_analyst"],
            tools=search_tools,
            allow_delegation=False,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],
            tools=search_tools,
            allow_delegation=False,
            verbose=True,
            llm_timeout=300
        )

    @agent
    def sales_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist"],
            tools=search_tools,
            allow_delegation=False,
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
            # max_rpm=10,  # Rate limiting to avoid overwhelming the API
            manager_llm_timeout=300,  # 5 minutes timeout for manager LLM
            task_timeout=1800,  # 30 minutes timeout for each task
            manager_llm="gpt-4o",
        )
    
    def find_contacts(self):
        """Generate contact information and return the formatted result for email distribution"""
        # Set default values if not provided
        company = getattr(self, 'company', "iFage | Fondation pour la formation des adultes")
        our_product = getattr(self, 'our_product', "PowerStore")
        
        # Get the output file path
        output_file = 'output/contact_finder/key_contacts.md'
        
        # Run the crew with inputs
        self.crew().kickoff(inputs={
            "company": company,
            "our_product": our_product
        })
        
        # Return the path to the output file
        return output_file
    
    def kickoff(self, inputs=None):
        """Start the crew with the given inputs."""
        if inputs:
            if 'company' in inputs:
                self.company = inputs['company']
            if 'our_product' in inputs:
                self.our_product = inputs['our_product']
            if 'sendto' in inputs:
                self.sendto = inputs['sendto']
        
        # Generate the contact information and return the result
        output_file = self.find_contacts()
        
        # Read the generated contact information from the file
        with open(output_file, "r") as f:
            contact_content = f.read()
            
        return contact_content
