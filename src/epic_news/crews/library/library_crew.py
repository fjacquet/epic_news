import os
import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.models.report import ReportHTMLOutput

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
    
    # Output directory structure - use absolute path for consistency
    output_dir = os.path.abspath(os.path.join('output', 'library'))

    def __init__(self, topic=None):
        """Initialize the LibraryCrew and ensure output directory exists.
        
        Args:
            topic: The book or research topic to analyze (e.g., "The Art of War by Sun Tzu")
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
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
        
        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, 'research_results.md')
        
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
        
        # Define output file with absolute path
        output_file = os.path.join(self.output_dir, 'book_summary.html')
        
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
        
        Returns:
            Task: Configured reporting task from YAML configuration
        """
        # Use absolute paths for both input HTML and output PDF
        input_html = os.path.abspath(os.path.join(self.output_dir, 'book_summary.html'))
        output_file = os.path.abspath(os.path.join(self.output_dir, 'book_summary.pdf'))
        
        # Create a copy of the config to modify
        task_config = dict(self.tasks_config['reporting_task_pdf'])
        
        # Add the file paths directly to the task description
        task_config['description'] = task_config['description'] + f"\nHTML_FILE_PATH={input_html}\nPDF_OUTPUT_PATH={output_file}"
        
        return Task(
            config=task_config,
            output_file=output_file,
            # Context should reference the HTML task to ensure proper sequencing
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
