from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

load_dotenv()


@CrewBase
class LibraryCrew:
    """
    Library expertise crew for finding books and generating book summaries.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering information."""
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            respect_context_window=True,
            tools=get_search_tools() + get_scrape_tools() + get_report_tools(),
            llm="gpt-4.1-mini",
            reasoning=True,
            llm_timeout=300,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Create a reporting analyst agent responsible for creating HTML reports."""
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            respect_context_window=True,
            tools=get_search_tools() + get_scrape_tools() + get_report_tools(),
            reasoning=True,
            llm_timeout=300,
        )

    @task
    def research_task(self) -> Task:
        """Define the research task for gathering information about the topic."""
        return Task(
            config=self.tasks_config["research_task"],
            async_execution=False,
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research."""
        return Task(
            config=self.tasks_config["reporting_task"],
            verbose=True,
            async_execution=False,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow."""
        try:
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
            )
        except Exception as e:
            error_msg = f"Error creating LibraryCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
