from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
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
    """Cooking crew: one agent produces a PaprikaRecipe; YAML/JSON exports are written in Python (utils.recipe_export)."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def cook(self) -> Agent:
        """
        Cook agent that produces a PaprikaRecipe model.
        It uses the default LLM for cost efficiency and no external tools.
        """
        return Agent(
            config=self.agents_config["cook"],
            llm=LLMConfig.get_openrouter_llm(task_type="quick"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            respect_context_window=True,
        )

    @task
    def cook_task(self) -> Task:
        """Generate the `PaprikaRecipe`."""
        return Task(
            config=self.tasks_config["cook_task"],
            agent=self.cook(),
            output_pydantic=PaprikaRecipe,
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
                max_rpm=LLMConfig.get_max_rpm(),
            )
        except Exception as e:
            logger.error(f"Error creating CookingCrew: {str(e)}")
            raise
