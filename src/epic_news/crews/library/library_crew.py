import logging
import os
import pathlib

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

# KISS approach: No custom path utilities
from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.rag_tools import get_rag_tools
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
class LibraryCrew():
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
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self, topic=None):
        """Initialize the LibraryCrew and ensure output directory exists.
        
        Args:
            topic: The book or research topic to analyze (e.g., "The Art of War by Sun Tzu")
        """
        # KISS approach: Let CrewAI manage output paths
        # No custom output_dir needed - CrewAI will handle this
        
        # Store inputs
        self.topic = topic or 'The Art of War by Sun Tzu'
        
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
            self.rag_tools = get_rag_tools()
            self.html_to_pdf_tool = HtmlToPdfTool()
            self.file_read_tool = FileReadTool()
            self.report_tools = get_report_tools()
            
            # Create combined toolsets for different agent needs
            self.all_tools = self.search_tools + self.scrape_tools + self.rag_tools + \
                           [self.html_to_pdf_tool] + self.report_tools
                           
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
            config=self.agents_config['researcher'],
            verbose=True,
            respect_context_window=True,
            tools=self.all_tools,
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
            config=self.agents_config['reporting_analyst'],
            verbose=True,
            respect_context_window=True,
            tools=self.rag_tools + [self.html_to_pdf_tool, self.file_read_tool] + self.report_tools,  
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
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config['research_task'])
        task_config['description'] = task_config['description'].format(topic=self.topic)
        
        # KISS approach: Use simple relative paths
        output_file = "output/library/research_results.md"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        return Task(
            config=task_config,
            output_file=output_file,
            async_execution=True  # Make task asynchronous for better performance
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research.
        
        This task is assigned to the reporting analyst agent and produces an HTML file
        with a properly structured report using the standard report template with styling, 
        table of contents, and emojis.
        
        Returns:
            Task: Configured reporting task from YAML configuration
        """
        # Create task config with dynamic topic
        task_config = dict(self.tasks_config['reporting_task'])
        task_config['description'] = task_config['description'].format(topic=self.topic)
        
        # KISS approach: Use simple relative paths
        output_file = f"output/library/{self.topic.replace(' ', '_')}_library_report.html"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        return Task(
            config=task_config,
            output_file=output_file,
            # Final task in sequential process must be synchronous per CrewAI framework
        )
    @task
    def reporting_task_pdf(self) -> Task:
        """Define the reporting task for creating PDF reports based on research.
        
        This task is assigned to the reporting analyst agent and produces a PDF file
        with a properly structured report including styling, table of contents, and emojis.
        The tool used for this task requires absolute paths for input and output.
        
        Returns:
            Task: Configured reporting task from YAML configuration
        """
        # KISS approach: The tool handles saving the file to the final destination.
        input_html_path = pathlib.Path(f"output/library/{self.topic.replace(' ', '_')}_library_report.html")
        output_file_path = input_html_path.with_suffix('.pdf')
        
        # The tool needs absolute paths to function correctly.
        abs_input_html_path = input_html_path.resolve()
        abs_output_pdf_path = output_file_path.resolve()

        # Ensure output directory exists
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a copy of the config to modify
        task_config = dict(self.tasks_config['reporting_task_pdf'])
        
        # Add the absolute file paths directly to the task description for the agent.
        task_config['description'] = (
            task_config['description'] + 
            f"\nHTML_FILE_PATH: {abs_input_html_path}" +
            f"\nPDF_OUTPUT_PATH: {abs_output_pdf_path}"
        )
        
        return Task(
            config=task_config,
            output_file=str(output_file_path), # crewAI uses this to track the output
            # No callback needed; the tool now handles file placement.
            context=[self.reporting_task()],
            # PDF task is final and must be synchronous
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
                tasks=self.tasks,    # Automatically created by the @task decorator
                process=Process.sequential,  # Sequential process for clear task flow
                verbose=True,        # Enable verbose output for better debugging
                max_rpm=10,          # Rate limit to prevent API throttling
                memory=True,         # Enable memory to retain context between tasks
                cache=True,          # Enable caching for better performance
                llm_timeout=300,     # 5 minute timeout for LLM calls
                max_retries=2,       # Retry up to 2 times on failure
            )
        except Exception as e:
            # Fail fast with explicit error message
            error_msg = f"Error creating LibraryCrew: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
