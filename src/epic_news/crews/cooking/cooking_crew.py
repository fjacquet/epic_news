from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.models.paprika_recipe import PaprikaRecipe
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools
from epic_news.utils.tool_logging import apply_tool_silence, configure_tool_logging

# Mute all tools
configure_tool_logging(mute_tools=True, log_level="ERROR")

# Or just reduce verbosity
configure_tool_logging(mute_tools=False, log_level="WARNING")



# Load environment variables
load_dotenv()

# Apply tool silencing to mute tool output while keeping agent/task verbosity
apply_tool_silence()


# EnhancedCrew has been removed in favor of pure CrewAI implementation
# Topic slug generation is now handled in ContentState.to_crew_inputs


@CrewBase
class CookingCrew:
    """CookingCrew now follows a streamlined two-stage pipeline:

    1. Cook agent ⇒ generates a `PaprikaRecipe` dataclass (no heavy tools, default LLM)
    2. Paprika renderer ⇒ serialises the model to YAML for Paprika import

    HTML rendering is now centralized in HtmlDesignerCrew for consistency across all crews.
    This keeps each task focused, minimises tool usage, and speeds up the run while
    respecting the epic_news design principles (CrewAI-first, configuration-driven,
    context-driven, KISS).
    """

    """
    Cooking crew that creates comprehensive recipes optimized for Thermomix when appropriate.

    This crew specializes in generating detailed cooking recipes with structured data output:
    - JSON data for HtmlDesignerCrew to generate professional HTML reports
    - YAML files compatible with Paprika recipe manager for easy import

    The crew follows the epic_news design principles:
    - Configuration-driven approach using YAML files
    - Structured data output for centralized HTML generation via HtmlDesignerCrew
    - Dual output format support (JSON + YAML)
    - Error handling and logging
    - French language content with emoji enhancement
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the cooking crew with required tools."""
        self._init_tools()

    def _init_tools(self):
        """Initialize tools for the crew's agents."""
        self.search_tools = get_search_tools()
        self.scrape_tools = get_scrape_tools()

    @agent
    def cook(self) -> Agent:
        """Cook agent – produces a PaprikaRecipe model strictly.

        Uses the default LLM for cost efficiency and **no external tools** to keep
        the prompt small and fast.
        """
        return Agent(
            config=self.agents_config["cook"],  # new YAML entry expected
            verbose=True,
            llm_timeout=120,
            respect_context_window=True,
            reasoning=False,
        )

    @agent
    def paprika_renderer(self) -> Agent:
        """Paprika renderer agent – serialises recipe to YAML."""
        return Agent(
            config=self.agents_config["paprika_renderer"],
            verbose=True,
            respect_context_window=True,
            reasoning=False,
        )

    @agent
    def json_exporter(self) -> Agent:
        """JSON export specialist agent."""
        return Agent(
            config=self.agents_config["json_exporter"],
            verbose=True,
        )

    @task
    def cook_task(self) -> Task:
        """First task: generate the `PaprikaRecipe`."""
        task_config = dict(self.tasks_config["cook_task"])  # new YAML
        return Task(
            config=task_config,
            output_pydantic=PaprikaRecipe,
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
        task_config = dict(self.tasks_config["paprika_yaml_task"])

        # Topic and preferences will be available in the task context via CrewAI inputs
        # The task description template will be formatted at runtime with the actual inputs

        return Task(
            config=task_config,
            verbose=True,
        )

    @task
    def recipe_state_task(self) -> Task:
        """Third task: store PaprikaRecipe in CrewAI state for HtmlDesignerCrew."""
        task_config = dict(self.tasks_config["recipe_state_task"])
        return Task(
            config=task_config,
            verbose=True,
            output_pydantic=PaprikaRecipe,
        )

    @crew
    def crew(self) -> Crew:
        """Creates a streamlined cooking crew for comprehensive recipe creation.

        This method sets up the crew with the recipe expert agent and tasks for
        generating recipes in both HTML and Paprika YAML formats. Error handling
        is implemented to gracefully handle failures.

        Returns:
            Crew: Configured pure CrewAI crew ready for execution
        """
        try:
            logger.info("Creating CookingCrew for recipe generation")

            # Create and return a pure CrewAI crew
            # topic_slug is now handled in ContentState.to_crew_inputs
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
            )

        except Exception as e:
            logger.error(f"Error creating CookingCrew: {str(e)}")
            raise
