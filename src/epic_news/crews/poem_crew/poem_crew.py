from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class PoemCrew:
    """Poem Crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    def __init__(self):
        """Initialize the PoemCrew"""
        self.topic = None
        self.sentence_count = 5
        self.output_file = "output/poem/poem.html"

    # If you would lik to add tools to your crew, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def poem_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["poem_writer"],
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def write_poem(self) -> Task:
        print(f"Writing poem about: {self.topic}")
        # Create a task with the configuration from YAML
        task = Task(
            config=self.tasks_config["write_poem"],
            output_file=self.output_file
        )
        
        # Replace the placeholders in the description and expected_output
        if self.topic:
            task.description = task.description.replace("{topic}", self.topic)
            task.expected_output = task.expected_output.replace("{topic}", self.topic)
        
        if self.sentence_count:
            task.description = task.description.replace("{sentence_count}", str(self.sentence_count))
            task.expected_output = task.expected_output.replace("{sentence_count}", str(self.sentence_count))
            
        return task

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
        
    def kickoff(self, inputs=None):
        """Start the crew with the given inputs"""
        if inputs:
            # Update instance variables with inputs
            if "topic" in inputs:
                self.topic = inputs["topic"]
            if "sentence_count" in inputs:
                self.sentence_count = inputs["sentence_count"]
            if "output_file" in inputs:
                self.output_file = inputs["output_file"]

        # Run the crew
        result = self.crew().kickoff()
        return result
