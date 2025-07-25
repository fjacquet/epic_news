from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# from epic_news.tools.validation_tools import get_validation_tools
from epic_news.tools.web_tools import get_news_tools, get_search_tools


@CrewBase
class NewsDailyCrew:
    """NewsDaily crew for collecting and reporting daily news in French"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def news_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["news_researcher"],
            tools=get_news_tools() + get_search_tools(),
            verbose=True,
        )

    @agent
    def content_curator(self) -> Agent:
        return Agent(
            config=self.agents_config["content_curator"],
            tools=[],
            verbose=True,
            reasoning=True,
            llm="gpt-4.1",
        )

    @task
    def suisse_romande_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_romande_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def suisse_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["suisse_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def france_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["france_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def europe_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["europe_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def world_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["world_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def wars_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["wars_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def economy_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["economy_news_task"],
            async_execution=True,
            verbose=True,
        )

    @task
    def content_curation_task(self) -> Task:
        return Task(
            config=self.tasks_config["content_curation_task"],
            verbose=True,
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
            verbose=True,
            context=[self.content_curation_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the NewsDaily crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
