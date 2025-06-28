from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.models.poem_models import PoemJSONOutput


@CrewBase
class PoemCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def poem_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["poem_writer"],
            respect_context_window=True,
            verbose=True,
        )

    @task
    def write_poem(self) -> Task:
        return Task(
            config=self.tasks_config["write_poem"],
            agent=self.poem_writer(),
            output_pydantic=PoemJSONOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
