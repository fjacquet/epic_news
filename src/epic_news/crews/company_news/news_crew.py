import logging
import os
import pathlib

from composio_crewai import ComposioToolSet
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.tools.report_tools import get_report_tools

# fact_checking_tools module doesn't exist, using alternative approach
from epic_news.tools.web_tools import get_scrape_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the toolset
toolset = ComposioToolSet()

# Use only available tools for search
search_tools = toolset.get_tools(
    actions=[
        "FIRECRAWL_SEARCH",
        "COMPOSIO_SEARCH_SEARCH",
        "COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH",
        "COMPOSIO_SEARCH_NEWS_SEARCH",
        "COMPOSIO_SEARCH_TRENDS_SEARCH",
        "COMPOSIO_SEARCH_EVENT_SEARCH",
    ],
)


# Use only available tools for fact checking
fact_checking_tools = toolset.get_tools(
    actions=["COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH"],
)


@CrewBase
class CompanyNewsCrew:
    """
    Company news monitoring, analysis, fact-checking and editor crew.

    This crew follows the epic_news design principles of being configuration-driven,
    simple, and elegant. It leverages YAML configuration files for agents and tasks,
    maintaining a clear separation between code and configuration.

    The crew uses a hierarchical process with multiple agents working in coordination:
    - Researcher: Gathers news and information about the specified topic
    - Analyst: Analyzes research data for insights, trends, and significance
    - Fact Checker: Verifies all claims and statements for accuracy
    - Editor: Creates the final formatted HTML report using templates
    """

    # Configuration file paths relative to the crew directory
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Output directory structure - use absolute path for consistency
    _crew_path = pathlib.Path(__file__).parent
    project_root = (
        _crew_path.parent.parent.parent.parent.parent
    )  # Go up 5 levels: news -> crews -> epic_news -> src -> project_root
    output_dir = str(project_root / "output" / "news")

    def __init__(self):
        """
        Initialize the CompanyNewsCrew and ensure output directory exists.

        Creates the output directory for news reports if it doesn't exist and
        initializes all necessary tools for the crew's agents.

        Raises:
            Exception: If there's an error during initialization.
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize tools
        self._initialize_tools()

    def _initialize_tools(self):
        """
        Initialize all tools needed by the crew's agents.

        This centralizes tool initialization to follow the DRY principle and
        makes it easier to modify tool configurations in one place.
        """
        try:
            # Initialize Composio toolset
            toolset = ComposioToolSet()

            # Initialize standard tool sets
            self.search_tools = toolset.get_tools(
                actions=[
                    "FIRECRAWL_SEARCH",
                    "COMPOSIO_SEARCH_SEARCH",
                    "COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH",
                    "COMPOSIO_SEARCH_NEWS_SEARCH",
                    "COMPOSIO_SEARCH_TRENDS_SEARCH",
                    "COMPOSIO_SEARCH_EVENT_SEARCH",
                ]
            )

            # Use specific search tools for fact checking
            self.fact_checking_tools = toolset.get_tools(actions=["COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH"])

            self.scrape_tools = get_scrape_tools()
            self.rag_tools = get_rag_tools()
            self.report_tools = get_report_tools()

            # Create combined toolsets for different agent needs
            self.all_tools = self.search_tools + self.scrape_tools + self.rag_tools + self.report_tools

            logger.info("Successfully initialized all tools for CompanyNewsCrew")

        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            # Provide fallback empty lists to prevent crew from failing completely
            self.search_tools = []
            self.fact_checking_tools = []
            self.scrape_tools = []
            self.report_tools = []
            self.all_tools = []
            raise RuntimeError(f"Error initializing tools: {str(e)}") from e

    # Agent definitions follow - each agent is specialized for a specific role
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
    def fact_checker(self) -> Agent:
        """Create a fact checker agent responsible for verifying claims and sources.

        Returns:
            Agent: Configured fact checker agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["fact_checker"],
            tools=self.fact_checking_tools,
            verbose=True,
            llm_timeout=300,
            reasoning=True,
            respect_context_window=True,
        )

    @agent
    def editor(self) -> Agent:
        """Create an editor agent responsible for creating the final HTML report.

        This agent uses report tools to create standardized, professional HTML reports
        using the appropriate templates.

        Returns:
            Agent: Configured editor agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["editor"],
            tools=self.report_tools,
            verbose=True,
            llm_timeout=300,
            reasoning=True,
            respect_context_window=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        """Define the research task for gathering news information about the topic.

        This task is assigned to the researcher agent and produces a markdown file
        with research findings on the news topic.

        Returns:
            Task: Configured research task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["research_task"])

        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, "research_results.md")

        return Task(
            config=task_config,
            output_file=output_file,
            verbose=True,
            async_execution=True,  # Parallel execution for better performance
            llm_timeout=300,
        )

    @task
    def analysis_task(self) -> Task:
        """Define the analysis task for analyzing gathered news information.

        This task is assigned to the analyst agent and produces a markdown file
        with analysis of trends, impacts, and significance.

        Returns:
            Task: Configured analysis task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["analysis_task"])

        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, "analysis_results.md")

        return Task(
            config=task_config,
            context=[self.research_task()],  # This task depends on research
            output_file=output_file,
            verbose=True,
            llm_timeout=300,
        )

    @task
    def verification_task(self) -> Task:
        """Define the verification task for fact checking the research and analysis.

        This task is assigned to the fact checker agent and produces a markdown file
        with verification of claims and sources.

        Returns:
            Task: Configured verification task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["verification_task"])

        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, "verification_results.md")

        return Task(
            config=task_config,
            context=[self.research_task(), self.analysis_task()],  # This task depends on both previous tasks
            output_file=output_file,
            verbose=True,
            llm_timeout=300,
        )

    @task
    def editing_task(self) -> Task:
        """Define the editing task for creating the final HTML news report.

        This task is assigned to the editor agent and produces a professionally formatted
        HTML report using standardized templates.

        Returns:
            Task: Configured editing task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config["editing_task"])

        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, "news_report.html")

        return Task(
            config=task_config,
            context=[
                self.research_task(),
                self.analysis_task(),
                self.verification_task(),
            ],  # This task depends on all previous tasks
            output_file=output_file,
            verbose=True,
            llm_timeout=300,
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
                process=Process.hierarchical,  # Hierarchical process for parallel execution
                verbose=True,  # Enable verbose output for better debugging
                max_rpm=10,  # Rate limit to prevent API throttling
                memory=True,  # Enable memory to retain context between tasks
                cache=True,  # Enable caching for better performance
                llm_timeout=300,  # 5 minute timeout for LLM calls
                max_retries=2,  # Retry up to 2 times on failure
                manager_llm="gpt-4.1-nano",
            )
        except Exception as e:
            # Fail fast with explicit error message
            error_msg = f"Error creating CompanyNewsCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
