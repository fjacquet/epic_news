from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.config.llm_config import LLMConfig
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

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]

    @agent
    def cook(self) -> Agent:
        """
        Cook agent that produces a PaprikaRecipe model.
        It uses the default LLM for cost efficiency and no external tools.
        """
        return Agent(
            config=self.agents_config["cook"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("quick"),
            verbose=True,
            respect_context_window=True,
            reasoning=False,
        )

    @agent
    def paprika_renderer(self) -> Agent:
        """Paprika renderer agent that serialises recipe to YAML."""
        return Agent(
            config=self.agents_config["paprika_renderer"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("quick"),
            verbose=True,
            respect_context_window=True,
            reasoning=False,
        )

    @agent
    def json_exporter(self) -> Agent:
        """Agent that exports the PaprikaRecipe to JSON for downstream crews."""
        return Agent(
            config=self.agents_config["json_exporter"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("quick"),
            verbose=True,
            respect_context_window=True,
            reasoning=False,
        )

    @task
    def cook_task(self) -> Task:
        """Generate the `PaprikaRecipe`."""
        return Task(
            config=self.tasks_config["cook_task"],  # type: ignore[call-arg]
            agent=self.cook(),  # type: ignore[call-arg]
            output_pydantic=PaprikaRecipe,
        )

    @task
    def paprika_yaml_task(self) -> Task:
        """
        Generate a recipe in YAML format compatible with the Paprika recipe manager.
        """
        return Task(
            config=self.tasks_config["paprika_yaml_task"],  # type: ignore[call-arg]
            agent=self.paprika_renderer(),  # type: ignore[call-arg]
            context=[self.cook_task()],  # type: ignore
            verbose=True,
        )

    @task
    def recipe_state_task(self) -> Task:
        """Persist recipe state to JSON for HTML rendering pipeline."""
        return Task(
            config=self.tasks_config["recipe_state_task"],  # type: ignore[call-arg]
            agent=self.json_exporter(),  # type: ignore[call-arg]
            context=[self.cook_task()],  # type: ignore
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        """Creates a streamlined cooking crew for comprehensive recipe creation."""
        try:
            logger.info("Creating CookingCrew for recipe generation")
            return Crew(
                agents=self.agents,  # type: ignore[attr-defined]
                tasks=self.tasks,  # type: ignore[attr-defined]
                process=Process.sequential,
                verbose=True,
                max_iter=LLMConfig.get_max_iter(),  # type: ignore[call-arg]
                max_rpm=LLMConfig.get_max_rpm(),
            )
        except Exception as e:
            logger.error(f"Error creating CookingCrew: {str(e)}")
            raise
