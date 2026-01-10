from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.models.crews.company_news_report import CompanyNewsReport
from epic_news.utils.observability import get_observability_tools, trace_task

# Load environment variables
load_dotenv()

# Initialize observability tools at the module level
observability_tools = get_observability_tools(crew_name="company_news_crew")
tracer = observability_tools["tracer"]
dashboard = observability_tools["dashboard"]
hallucination_guard = observability_tools["hallucination_guard"]


@CrewBase
class CompanyNewsCrew:
    """
    Company news monitoring, analysis, and editor crew.

    This crew follows the epic_news design principles of being configuration-driven,
    simple, and elegant. It leverages YAML configuration files for agents and tasks,
    maintaining a clear separation between code and configuration.

    The crew uses a hierarchical process with multiple agents working in coordination:
    - Researcher: Gathers news and information about the specified topic
    - Analyst: Analyzes research data for insights, trends, and significance
    - Editor: Creates the final formatted HTML report using templates
    """

    # Configuration file paths relative to the crew directory
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """
        Initialize the CompanyNewsCrew.

        GOLD STANDARD: This class does not manage output directories or tools. All tool assignment is handled by CrewAI config/factories.
        Output file is passed via context parameter `output_file`.
        """

        from epic_news.config.composio_config import ComposioConfig

        # Initialize Composio with new 1.0 API
        # NOTE: Composio 1.0 has NO "SEARCH" toolkit. Search comes from social platforms.
        composio = ComposioConfig()

        # Get search tools from Reddit, Twitter, and HackerNews (5 tools total)
        # These replace the deprecated COMPOSIO_SEARCH_* actions that no longer exist
        self.search_tools = composio.get_search_tools()

        # Pass observability tools to instance
        self.tracer = tracer
        self.dashboard = dashboard
        self.hallucination_guard = hallucination_guard

    # in the news analysis and reporting process
    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering news information.

        Returns:
            Agent: Configured researcher agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.search_tools,
            verbose=True,
            llm_timeout=300,
            reasoning=True,
            respect_context_window=True,
        )

    @agent
    def analyst(self) -> Agent:
        """Create an analyst agent responsible for analyzing news and identifying trends.

        Returns:
            Agent: Configured analyst agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["analyst"],
            tools=self.search_tools,
            verbose=True,
            llm_timeout=300,
            reasoning=True,
            respect_context_window=True,
        )

    @agent
    def editor(self) -> Agent:
        """Create an editor agent responsible for creating the final HTML report.

        GOLD STANDARD: This agent has NO tools. It receives its output file path from the CrewAI context parameter `output_file`.
        All output file handling must be done via CrewAI config/context, NOT in Python.
        """
        return Agent(
            config=self.agents_config["editor"],
            tools=[],  # Gold standard: no tools for reporting agent
            verbose=True,
            llm_timeout=300,
            reasoning=True,
            respect_context_window=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    @trace_task(tracer)
    def research_task(self) -> Task:
        """Define the research task for gathering news information about the topic.

        This task is assigned to the researcher agent and produces a markdown file
        with research findings on the news topic.

        Returns:
            Task: Configured research task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["research_task"])
        return Task(
            config=task_config,
            verbose=True,
            async_execution=False,  # Parallel execution for better performance
            llm_timeout=300,
        )

    @task
    @trace_task(tracer)
    def analysis_task(self) -> Task:
        """Define the analysis task for analyzing gathered news information.

        This task is assigned to the analyst agent and produces a markdown file
        with analysis of trends, impacts, and significance.

        Returns:
            Task: Configured analysis task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["analysis_task"])
        return Task(
            config=task_config,
            context=[self.research_task()],  # This task depends on research
            verbose=True,
            llm_timeout=300,
        )

    @task
    @trace_task(tracer)
    def editing_task(self) -> Task:
        """Define the editing task for creating the final HTML news report.

        This task is assigned to the editor agent and produces a professionally formatted
        HTML report using standardized templates.

        Returns:
            Task: Configured editing task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["editing_task"])

        return Task(
            config=task_config,
            context=[
                self.research_task(),
                self.analysis_task(),
            ],  # This task depends on all previous tasks
            verbose=True,
            llm_timeout=300,
            output_pydantic=CompanyNewsReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Company news monitoring crew with hierarchical workflow.

        The crew uses a hierarchical process that allows for parallel execution
        of research, analysis, and verification tasks, followed by a final editing
        phase that consolidates the results into a professional HTML report.

        Returns:
            Crew: Configured Company news crew with agents and tasks
        """
        try:
            # Configure the crew with hierarchical process and appropriate settings
            return Crew(
                agents=self.agents,  # Automatically created by the @agent decorator
                tasks=self.tasks,  # Automatically created by the @task decorator
                process=Process.sequential,  # Hierarchical process for parallel execution
                verbose=True,  # Enable verbose output for better debugging
                llm_timeout=300,  # 5 minute timeout for LLM calls
                max_retries=2,  # Retry up to 2 times on failure
            )
        except Exception as e:
            # Fail fast with explicit error message
            error_msg = f"Error creating CompanyNewsCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
