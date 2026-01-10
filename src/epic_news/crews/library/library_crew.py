from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

load_dotenv()


@CrewBase
class LibraryCrew:
    """
    Library expertise crew for finding books and generating book summaries.
    """

    def __init__(self):
        # Resolve the absolute path to the configuration files
        base_dir = Path(__file__).parent
        self.agents_config = str(base_dir / "config/agents.yaml")
        self.tasks_config = str(base_dir / "config/tasks.yaml")

    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering information."""
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            respect_context_window=True,
            tools=get_search_tools() + get_scrape_tools() + get_report_tools(),
            llm=LLMConfig.get_openrouter_llm(),
            reasoning=True,
            max_reasoning_attempts=3,
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Create a reporting analyst agent responsible for creating JSON reports."""
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            respect_context_window=True,
            tools=[],  # No tools for final reporting agent to ensure clean JSON output
            llm=LLMConfig.get_openrouter_llm(),
            reasoning=True,
            max_reasoning_attempts=3,
            llm_timeout=LLMConfig.get_timeout("default"),
            system_template="""You are a JSON formatting expert. Your ONLY job is to produce valid,
            syntactically correct JSON that conforms exactly to the specified Pydantic model.

            CRITICAL RULES:
            - Output ONLY JSON, no explanations or additional text
            - Ensure all strings are properly quoted with double quotes
            - Ensure all arrays use square brackets []
            - Ensure all objects use curly braces {}
            - Use proper comma separation between all fields and array elements
            - Validate JSON syntax before outputting

            You never include markdown code blocks, explanations, or any text outside the JSON structure.""",
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
            agent=self.reporting_analyst(),
            context=[self.research_task()],
            output_pydantic=BookSummaryReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow."""
        try:
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                llm_timeout=LLMConfig.get_timeout("default"),
                max_iter=LLMConfig.get_max_iter(),
                max_rpm=LLMConfig.get_max_rpm(),
                verbose=True,
            )
        except Exception as e:
            error_msg = f"Error creating LibraryCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
