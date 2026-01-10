from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig

load_dotenv()


@CrewBase
class ReceptionCrew:
    """ReceptionCrew for routing requests to the appropriate specialized crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def router(self) -> Agent:
        return Agent(
            config=self.agents_config["router"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            respect_context_window=True,
        )

    @task
    def routing_task(self) -> Task:
        return Task(
            config=self.tasks_config["routing_task"],
            agent=self.router(),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ReceptionCrew for routing requests"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
