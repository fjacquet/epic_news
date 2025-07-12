from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.tool_logging import configure_tool_logging

# Mute all tools
configure_tool_logging(mute_tools=True, log_level="ERROR")

# Load environment variables
load_dotenv()


@CrewBase
class CookingCrew:
    """
    Cooking crew that creates comprehensive recipes.

    This crew specializes in generating detailed cooking recipes with structured data output
    in YAML files compatible with Paprika recipe manager for easy import.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def cook(self) -> Agent:
        """
        Cook agent that produces a PaprikaRecipe model.
        It uses the default LLM for cost efficiency and no external tools.
        """
        return Agent(
            config=self.agents_config["cook"],
            verbose=True,
            llm_timeout=120,
            respect_context_window=True,
            reasoning=False,
        )

    @agent
    def paprika_renderer(self) -> Agent:
        """Paprika renderer agent that serialises recipe to YAML."""
        return Agent(
            config=self.agents_config["paprika_renderer"],
            verbose=True,
            respect_context_window=True,
            reasoning=False,
        )

    @task
    def cook_task(self) -> Task:
        """Generate the `PaprikaRecipe`."""
        return Task(
            config=self.tasks_config["cook_task"],
            output_pydantic=PaprikaRecipe,
        )

    @task
    def paprika_yaml_task(self) -> Task:
        """
        Generate a recipe in YAML format compatible with the Paprika recipe manager.
        """
        return Task(
            config=self.tasks_config["paprika_yaml_task"],
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        """Creates a streamlined cooking crew for comprehensive recipe creation."""
        try:
            logger.info("Creating CookingCrew for recipe generation")
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
            )
        except Exception as e:
            logger.error(f"Error creating CookingCrew: {str(e)}")
            raise
