from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import json

@CrewBase
class ReceptionCrew:
    """ReceptionCrew for routing requests to the appropriate specialized crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def router(self) -> Agent:
        return Agent(
            config=self.agents_config['router'],
            verbose=True
        )

    @task
    def routing_task(self) -> Task:
        return Task(
            config=self.tasks_config['routing_task'],
            agent=self.router(),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ReceptionCrew for routing requests"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
