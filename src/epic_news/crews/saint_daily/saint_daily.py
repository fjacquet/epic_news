"""
SaintDaily crew for researching and reporting on the saint of the day in Switzerland.
This crew searches for information about today's saint using Wikipedia and other web tools,
then generates a comprehensive French HTML report.
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool
from epic_news.tools.wikipedia_processing_tool import WikipediaProcessingTool
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool


@CrewBase
class SaintDailyCrew:
    """SaintDailyCrew that creates comprehensive saint of the day reports."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def saint_researcher(self) -> Agent:
        # Wikipedia tools for saint research
        wikipedia_tools = [
            WikipediaSearchTool(),
            WikipediaArticleTool(),
            WikipediaProcessingTool(),
        ]
        # Web search and scraping tools for additional research
        research_tools = wikipedia_tools

        return Agent(
            config=self.agents_config["saint_researcher"],  # type: ignore[index]
            tools=research_tools,
            verbose=True,
            respect_context_window=True,
        )

    @agent
    def saint_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["saint_reporter"],  # type: ignore[index]
            tools=[],  # NO TOOLS = No action traces
            verbose=True,
            respect_context_window=True,
        )

    @task
    def saint_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_research_task"],  # type: ignore[arg-type, index]
            agent=self.saint_researcher(),  # type: ignore[call-arg]
            verbose=True,
        )

    @task
    def saint_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_data_task"],  # type: ignore[arg-type, index]
            agent=self.saint_reporter(),  # type: ignore[call-arg]
            context=[self.saint_research_task()],  # type: ignore[call-arg]
            output_pydantic=SaintData,
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SaintDaily crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,  # type: ignore[call-arg]
        )
