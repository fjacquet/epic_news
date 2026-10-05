from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.tools.web_tools import get_news_tools


@CrewBase
class NewsDailyCrew:
    """NewsDaily crew for collecting and reporting daily news in French"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    def _new_researcher(self) -> Agent:
        """A fresh researcher for one region task.

        Region tasks run in parallel, so they must not share one Agent instance, and
        Agent.copy() would drop the LLM timeout (ADR-014).
        """
        return Agent(
            config=self.agents_config["news_researcher"],
            tools=get_news_tools(),  # get_search_tools() is the same PerplexitySearchTool
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @agent
    def news_researcher(self) -> Agent:
        # Kept as an @agent so tasks.yaml's `agent: news_researcher` still resolves;
        # region tasks override it with their own instance (explicit agent= wins).
        return self._new_researcher()

    @agent
    def content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config["content_curator"],
            tools=[],
            verbose=True,
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
        )

    @task
    def suisse_romande_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_romande_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def suisse_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def france_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["france_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def europe_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["europe_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def world_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["world_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def wars_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["wars_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def economy_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["economy_news_task"],
            agent=self._new_researcher(),
            async_execution=True,
        )

    @task
    def content_curation_task(self) -> Task:
        return Task(
            config=self.tasks_config["content_curation_task"],
            context=[
                self.suisse_romande_news_task(),
                self.suisse_news_task(),
                self.france_news_task(),
                self.europe_news_task(),
                self.world_news_task(),
                self.wars_news_task(),
                self.economy_news_task(),
            ],
        )

    @task
    def final_report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_generation_task"],
            context=[self.content_curation_task()],
            output_pydantic=NewsDailyReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the NewsDaily crew"""
        agents = list(self.agents)
        for task_ in self.tasks:
            if task_.agent is not None and all(task_.agent is not known for known in agents):
                agents.append(task_.agent)
        return Crew(
            agents=agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
