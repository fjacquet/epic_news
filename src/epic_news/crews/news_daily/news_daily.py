from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.news_daily_report import NewsDailyReport

# from epic_news.tools.validation_tools import get_validation_tools
from epic_news.tools.web_tools import get_news_tools, get_search_tools


@CrewBase
class NewsDailyCrew:
    """NewsDaily crew for collecting and reporting daily news in French"""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]

    @agent
    def news_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["news_researcher"],
            tools=get_news_tools() + get_search_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @agent
    def content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config["content_curator"],
            tools=[],
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=3,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @task
    def suisse_romande_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_romande_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def suisse_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def france_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["france_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def europe_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["europe_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def world_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["world_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def wars_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["wars_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def economy_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["economy_news_task"],
            async_execution=True,
            verbose=True,  # type: ignore[call-arg]
        )

    @task
    def content_curation_task(self) -> Task:
        return Task(
            config=self.tasks_config["content_curation_task"],
            verbose=True,  # type: ignore[call-arg]
            context=[
                self.suisse_romande_news_task(),  # type: ignore[call-arg]
                self.suisse_news_task(),  # type: ignore[call-arg]
                self.france_news_task(),  # type: ignore[call-arg]
                self.europe_news_task(),  # type: ignore[call-arg]
                self.world_news_task(),  # type: ignore[call-arg]
                self.wars_news_task(),  # type: ignore[call-arg]
                self.economy_news_task(),  # type: ignore[call-arg]
            ],
        )

    @task
    def final_report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_generation_task"],
            verbose=True,  # type: ignore[call-arg]
            context=[self.content_curation_task()],  # type: ignore[call-arg]
            output_pydantic=NewsDailyReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the NewsDaily crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
