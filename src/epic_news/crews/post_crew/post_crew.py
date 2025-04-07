from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet, App, Action
from dotenv import load_dotenv
import os
import datetime
import yaml
from pathlib import Path

load_dotenv()

# Initialize the ComposioToolSet for email sending
toolset = ComposioToolSet(app=App.GMAIL)
send_tools = toolset.get_tools(actions=['GMAIL_SEND_EMAIL'])

# Set environment variables to increase timeouts
os.environ["LITELLM_TIMEOUT"] = "300"  # 5 minutes timeout
os.environ["OPENAI_TIMEOUT"] = "300"   # 5 minutes timeout

@CrewBase
class PostCrew:
    """PostCrew crew for distributing content via email"""

    # YAML configuration files
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, topic, recipient_email):
        """Initialize the PostCrew with topic and recipient email."""
        self.topic = topic
        self.recipient_email = recipient_email
        self.current_year = datetime.datetime.now().year
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.inputs = {}  # Initialize inputs as an empty dictionary
        
        # Create necessary directories
        os.makedirs("output", exist_ok=True)


    @agent
    def distributor(self) -> Agent:
        """Creates the distributor agent"""
        return Agent(
            config=self.agents_config['distributor'],
            tools=send_tools,
            verbose=True
        )
    

    @task
    def distribution_task(self) -> Task:
        """Creates the distribution task with dynamic content"""
        # Create a context dictionary with all available variables
        context_dict = {
            'topic': self.topic,
            'recipient_email': self.recipient_email,
            'current_year': self.current_year,
            'current_date': self.current_date,
            'news': self.inputs.get('news', ''),
            'poem': self.inputs.get('poem', ''),
            'recipe': self.inputs.get('recipe', ''),
            'book_summary': self.inputs.get('book_summary', ''),
            'meeting_prep': self.inputs.get('meeting_prep', ''),
            'lead_score': self.inputs.get('lead_score', ''),
            'contact_info': self.inputs.get('contact_info', '')
        }
        
        # Get the task description from YAML but don't include tools section
        description = self.tasks_config['distribution_task']['description']
        expected_output = self.tasks_config['distribution_task']['expected_output']
        
        # Format the description with the context variables
        formatted_description = description.format(**context_dict)
        
        return Task(
            description=formatted_description,
            expected_output=expected_output,
            agent=self.distributor(),
            tools=send_tools
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PostCrew crew for email distribution"""
        # For simplicity, we'll only use the distributor agent and task when sending emails
        return Crew(
            agents=[self.distributor()],
            tasks=[self.distribution_task()],
            process=Process.sequential,
            verbose=True,
        )
        
    def kickoff(self, inputs=None):
        """Start the crew with the given inputs."""
        if inputs:
            self.inputs = inputs
            
        return self.crew().kickoff()
