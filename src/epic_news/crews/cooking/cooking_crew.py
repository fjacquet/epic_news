import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.models.paprika_recipe import PaprikaRecipe
from epic_news.models.report import ReportHTMLOutput
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.utility_tools import get_reporting_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@CrewBase
class CookingCrew:
    """
    Cooking crew that creates comprehensive recipes optimized for Thermomix when appropriate.
    
    This crew specializes in generating detailed cooking recipes in multiple formats:
    - HTML format for web display with rich formatting and images
    - YAML format compatible with the Paprika recipe manager
    
    The crew leverages configuration-driven design with YAML files for agents and tasks,
    and implements asynchronous execution where appropriate for optimal performance.
    """

    # Configuration files for agents and tasks
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the CookingCrew.
        
        Following the context-driven design pattern, topic and preferences
        are now passed via CrewAI inputs instead of constructor parameters.
        This aligns with the project's design principles for context injection.
            
        Sets up the output directory and initializes the tools required for recipe creation.
        """
        # Use centralized path utility for consistent output directory handling

        # Initialize tools
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize all tools needed by the crew's agents.
        
        This centralizes tool initialization to follow the DRY principle and
        makes it easier to modify tool configurations in one place.
        """
        try:
            # # Initialize the Composio toolset
            # toolset = ComposioToolSet()

            # # Get search tools for recipe research
            # self.search_tools = toolset.get_tools(actions=[
            #     'COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH',
            #     # Uncomment if needed for additional search capabilities
            #     # 'COMPOSIO_SEARCH_SEARCH',
            # ])

            self.search_tools = get_search_tools()
            self.scrape_tools = get_scrape_tools()
            self.rag_tools = get_rag_tools()
            self.reporting_tools = get_reporting_tools()
            self.report_tools = get_report_tools()

            logger.info("Successfully initialized all tools for CookingCrew")
        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            # Provide fallback empty list to prevent crew from failing completely
            self.search_tools = []
            self.reporting_tools = []
            raise

    @agent
    def recipe_expert(self) -> Agent:
        """Create a recipe expert agent responsible for creating detailed recipes.
        
        This agent specializes in researching and creating comprehensive recipes,
        optimized for Thermomix when appropriate, with detailed instructions,
        ingredient lists, and cooking techniques.
        
        Returns:
            Agent: Configured recipe expert agent with search tools
        """
        return Agent(
            config=self.agents_config['recipe_expert'],
            tools=self.search_tools + self.scrape_tools + self.rag_tools + self.reporting_tools + self.report_tools,
            verbose=True,
            llm_timeout=300,  # 5 minutes timeout for complex recipe generation
            respect_context_window=True,
            reasoning=True,
            max_iterations=3  # Allow multiple iterations for recipe refinement
        )

    @task
    def html_recipe_task(self) -> Task:
        """Define the HTML recipe creation task.
        
        This task generates a comprehensive recipe in HTML format with proper
        French language content and emoji usage for enhanced readability.
        The task uses the ReportingTool to create a professional HTML report.
        
        Returns:
            Task: Configured HTML recipe task from YAML configuration with topic
        """
        task_config = dict(self.tasks_config['html_recipe_task'])

        # Topic and preferences will be available in the task context via CrewAI inputs
        # The task description template will be formatted at runtime with the actual inputs

        return Task(
            config=task_config,
            verbose=False,
            llm_timeout=300,  # 5 minutes timeout for recipe generation
            async_execution=True,
            output_pydantic=ReportHTMLOutput
        )

    @task
    def paprika_yaml_task(self) -> Task:
        """Define the Paprika YAML recipe creation task.
        
        This task generates a recipe in YAML format compatible with the Paprika recipe manager.
        The YAML format includes structured fields for ingredients, instructions, cooking time,
        servings, and other metadata required by the Paprika app.
        
        Returns:
            Task: Configured Paprika YAML recipe task from YAML configuration with topic
        """
        task_config = dict(self.tasks_config['paprika_yaml_task'])

        # Topic and preferences will be available in the task context via CrewAI inputs
        # The task description template will be formatted at runtime with the actual inputs

        return Task(
            config=task_config,
            output_pydantic=PaprikaRecipe,
            verbose=True,
            llm_timeout=300,  # 5 minutes timeout for recipe generation
            async_execution=False
        )


    @crew
    def crew(self) -> Crew:
        """Creates a streamlined cooking crew for comprehensive recipe creation.
        
        This method sets up the crew with the recipe expert agent and tasks for
        generating recipes in both HTML and Paprika YAML formats. Error handling
        is implemented to gracefully handle failures.
        
        Returns:
            Crew: Configured crew ready for execution
        """
        try:
            logger.info("Creating CookingCrew for recipe generation")

            return Crew(
                agents=self.agents,  # Automatically created by the @agent decorator
                tasks=self.tasks,    # Automatically created by the @task decorator
                verbose=False,
                process=Process.sequential,  # Tasks must execute in order
                manager_llm_timeout=300,     # 5 minutes timeout for manager LLM
                task_timeout=1800,           # 30 minutes timeout for each task
                max_rpm=10,                  # Rate limit API calls to avoid throttling
            )
        except Exception as e:
            logger.error(f"Error creating CookingCrew: {str(e)}")
            raise
