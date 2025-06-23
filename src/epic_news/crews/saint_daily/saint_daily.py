"""
SaintDaily crew for researching and reporting on the saint of the day in Switzerland.
This crew searches for information about today's saint using Wikipedia and other web tools,
then generates a comprehensive French report using the ReportingTool.
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.tools.utility_tools import get_reporting_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool
from epic_news.tools.wikipedia_processing_tool import WikipediaProcessingTool
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool


@CrewBase
class SaintDailyCrew:
    """SaintDaily crew for researching the saint of the day in Switzerland"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        self._init_tools()

    def _init_tools(self):
        """Initialize tools for the crew's agents."""
        # Wikipedia tools for saint research
        self.wikipedia_tools = [
            WikipediaSearchTool(),
            WikipediaArticleTool(),
            WikipediaProcessingTool(),
        ]

        # Web search and scraping tools for additional research
        self.research_tools = get_search_tools() + get_scrape_tools() + self.wikipedia_tools

        # Reporting tools for HTML generation
        self.reporting_tools = get_reporting_tools()

    @agent
    def saint_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["saint_researcher"],
            tools=self.research_tools,
            verbose=True,
        )

    @agent
    def reporting_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_specialist"],
            tools=self.reporting_tools,
            verbose=True,
        )

    @task
    def saint_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_research_task"],
            verbose=True,
        )

    @task
    def saint_report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["saint_report_generation_task"],
            verbose=True,
            context=[self.saint_research_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SaintDaily crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
