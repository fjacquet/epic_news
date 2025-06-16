import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

from epic_news.tools.html_to_pdf_tool import HtmlToPdfTool
from epic_news.tools.rag_tools import get_rag_tools

# from composio_crewai import ComposioToolSet, App, Action
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

load_dotenv()

# # Initialize the toolset
# toolset = ComposioToolSet()

# search_tools = toolset.get_tools(actions=[
#     'COMPOSIO_SEARCH_SEARCH',
#     'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
#     'COMPOSIO_SEARCH_SHOPPING_SEARCH',
# ],
# )

search_tools = get_search_tools()
scrape_tools = get_scrape_tools()
rag_tools = get_rag_tools()
html_to_pdf_tool = HtmlToPdfTool()
file_read_tool = FileReadTool()
all_tools = search_tools + scrape_tools + rag_tools + [html_to_pdf_tool]

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
    
    # Output directory structure
    output_dir = 'output/library'

    def __init__(self):
        """Initialize the LibraryCrew and ensure output directory exists."""
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

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
            tools=all_tools,
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
            tools=rag_tools+[html_to_pdf_tool]+[file_read_tool],  
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
        output_file = os.path.join(self.output_dir, 'research_results.md')
        return Task(
            config=self.tasks_config['research_task'],
            output_file=output_file,
            async_execution=True  # Make task asynchronous for better performance
        )

    @task
    def reporting_task(self) -> Task:
        """Define the reporting task for creating HTML reports based on research.
        
        This task is assigned to the reporting analyst agent and produces an HTML file
        with a properly structured report including styling, table of contents, and emojis.
        
        Returns:
            Task: Configured reporting task from YAML configuration
        """
        output_file = os.path.join(self.output_dir, 'book_summary.html')
        return Task(
            config=self.tasks_config['reporting_task'],
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
            # Don't use context parameter as it requires specific structure
            # Final task in sequential process must be synchronous per CrewAI framework
        )
    @crew
    def crew(self) -> Crew:
        """Creates the Library crew with sequential workflow.
        
        The crew executes tasks in sequence: research first, then reporting.
        
        Returns:
            Crew: Configured Library crew with agents and tasks
        """
        try:
            return Crew(
                agents=self.agents,  # Automatically created by the @agent decorator
                tasks=self.tasks,    # Automatically created by the @task decorator
                process=Process.sequential,
                verbose=True,
            )
        except Exception as e:
            # Fail fast with explicit error message
            error_msg = f"Error creating LibraryCrew: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg) from e
