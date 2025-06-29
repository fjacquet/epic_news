import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

# KISS approach: No custom path utilities
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Note: Composio tools integration is commented out for future implementation
# from composio_crewai import ComposioToolSet, App, Action
# toolset = ComposioToolSet()
# search_tools = toolset.get_tools(actions=[
#     'COMPOSIO_SEARCH_SEARCH',
#     'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
#     'COMPOSIO_SEARCH_SHOPPING_SEARCH',
# ],
# )

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class LibraryCrew:
    """Library expertise crew for finding books and generating book summaries.

    This crew follows the epic_news design principles of being configuration-driven,
    simple, and elegant. It leverages YAML configuration files for agents and tasks,
    maintaining a clear separation between code and configuration.

    The crew consists of two agents:
    - Researcher: Finds relevant information about the specified topic
    - Reporting Analyst: Creates detailed HTML reports based on research findings

    The workflow is sequential, with research being conducted first, followed by
    report generation in HTML format with proper structure and styling.
    """

    # Configuration file paths relative to the crew directory
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the LibraryCrew and ensure output directory exists."""

        # KISS approach: Let CrewAI manage output paths
        # No custom output_dir needed - CrewAI will handle this

        # Initialize tools
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all tools needed by the crew's agents.

        This centralizes tool initialization to follow the DRY principle and
        makes it easier to modify tool configurations in one place.
        """
        try:
            # Initialize standard tool sets
            self.search_tools = get_search_tools()
            self.scrape_tools = get_scrape_tools()
            self.file_read_tool = FileReadTool()
            self.report_tools = get_report_tools()

            # Create combined toolsets for different agent needs
            self.all_tools = self.search_tools + self.scrape_tools + self.report_tools

            logger.info("Successfully initialized all tools for LibraryCrew")

        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            # Provide fallback empty lists to prevent crew from failing completely
            self.search_tools = []
            self.scrape_tools = []
            self.rag_tools = []
            self.report_tools = []
            self.all_tools = []
            raise

    @agent
    def researcher(self) -> Agent:
        """Create a researcher agent responsible for gathering information.

        Returns:
            Agent: Configured researcher agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["researcher"],
            verbose=True,
            respect_context_window=True,
            tools=self.all_tools,
            llm="gpt-4.1-mini",  # Use more powerful model for research
            reasoning=True,
            llm_timeout=300,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Create a reporting analyst agent responsible for creating HTML reports.

        Returns:
            Agent: Configured reporting analyst agent from YAML configuration
        """
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            respect_context_window=True,
            tools=self.all_tools,
            llm="gpt-4.1-mini",  # Use more powerful model for report generation
            reasoning=True,
            llm_timeout=300,
        )

    @task
    def research_task(self) -> Task:
        """Define the research task for gathering information about the topic.

        This task is assigned to the researcher agent and produces a markdown file
        with research findings.

        Returns:
            Task: Configured research task from YAML configuration
        """
        return Task(
            config=self.tasks_config["research_task"],
            async_execution=False,  # Make task asynchronous for better performance
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research.

        This task is assigned to the reporting analyst agent and produces an HTML file
        with a properly structured report using the universal report template with
        consistent styling, dark mode support, and proper structure.

        Returns:
            Task: Configured reporting task from YAML configuration
        """

        return Task(
            config=self.tasks_config["reporting_task"],
            verbose=True,
            async_execution=True,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow.

        The crew executes tasks in sequence: research first, then reporting, then PDF generation.

        Returns:
            Crew: Configured Library crew with agents and tasks
        """
        try:
            # Configure the crew with sequential process and appropriate settings
            return Crew(
                agents=self.agents,  # Automatically created by the @agent decorator
                tasks=self.tasks,  # Automatically created by the @task decorator
                process=Process.sequential,  # Sequential process for clear task flow
                verbose=True,  # Enable verbose output for better debuggingå
            )
        except Exception as e:
            # Fail fast with explicit error message
            error_msg = f"Error creating LibraryCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
