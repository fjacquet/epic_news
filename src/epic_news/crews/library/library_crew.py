from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools


@CrewBase
class LibraryCrew:
    """Library expertise crew for finding books and generating book summaries."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering information."""
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            verbose=True,
            respect_context_window=True,
            tools=get_search_tools() + get_scrape_tools() + get_report_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Create a reporting analyst agent responsible for creating JSON reports."""
        return Agent(
            config=self.agents_config["reporting_analyst"],  # type: ignore[index]
            verbose=True,
            respect_context_window=True,
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @task
    def research_task(self) -> Task:
        """Define the research task for gathering information about the topic."""
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[arg-type, index, call-arg]
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research."""
        return Task(
            config=self.tasks_config["reporting_task"],  # type: ignore[arg-type, index]
            context=[self.research_task()],  # type: ignore[call-arg]
            output_pydantic=BookSummaryReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow."""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),  # type: ignore[call-arg]
            verbose=True,
        )
