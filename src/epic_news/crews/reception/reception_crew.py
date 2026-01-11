from typing import Any, cast

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.routing_result import RoutingResult

load_dotenv()


@CrewBase
class ReceptionCrew:
    """ReceptionCrew for routing requests to the appropriate specialized crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def router(self) -> Agent:
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["router"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            respect_context_window=True,
        )

    @task
    def routing_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["routing_task"],
            agent=self.router(),  # type: ignore[call-arg]
            output_pydantic=RoutingResult,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ReceptionCrew for routing requests"""
        return Crew(
            agents=cast(list[Agent], self.agents),  # type: ignore[arg-type, attr-defined]
            tasks=cast(list[Task], self.tasks),  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
