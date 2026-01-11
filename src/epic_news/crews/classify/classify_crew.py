from typing import Any, cast

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.classification_result import ClassificationResult

load_dotenv()


@CrewBase
class ClassifyCrew:
    """
    Simple classification crew that analyzes user content and classifies it
    into the appropriate category from a predefined list.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def classifier(self) -> Agent:
        return Agent(
            config=cast(dict[str, Any], self.agents_config)["classifier"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
        )

    @task
    def classification_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=cast(dict[str, Any], self.tasks_config)["classification_task"],
            agent=self.classifier(),  # type: ignore[call-arg]
            output_pydantic=ClassificationResult,
        )

    @crew
    def crew(self) -> Crew:
        """Creates a simple classification crew"""
        return Crew(
            agents=cast(list[Agent], self.agents),  # type: ignore[arg-type, attr-defined]
            tasks=cast(list[Task], self.tasks),  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )

    def parse_result(self, result, categories=None):
        """
        Extract the selected category from the classification result.

        Args:
            result (CrewOutput or ClassificationResult or str): The result from the classification task
            categories (dict, optional): Dictionary of valid categories

        Returns:
            str: The selected category (selected_crew)
        """
        # If result is already a ClassificationResult, extract selected_crew
        if isinstance(result, ClassificationResult):
            category = result.selected_crew
        elif hasattr(result, "pydantic") and isinstance(result.pydantic, ClassificationResult):
            # CrewAI output with pydantic attribute
            category = result.pydantic.selected_crew
        else:
            # Fall back to string parsing for backwards compatibility
            result_text = str(result)
            if not result_text:
                return "UNKNOWN"
            # Get the first line which should be the category
            category = result_text.strip().split("\n")[0].strip()

        # If categories provided, validate the result
        if categories and category:
            # Case-insensitive match against available categories
            for key in categories:
                if key.upper() == category.upper():
                    return key

        # Return the found category or default to UNKNOWN
        return category if category else "UNKNOWN"
