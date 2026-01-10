from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.poem_report import PoemJSONOutput


@CrewBase
class PoemCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def poem_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["poem_writer"],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            respect_context_window=True,
            verbose=True,
            system_template="""You are a JSON formatting expert poet. Your output MUST be valid JSON.

            CRITICAL JSON FORMATTING RULES:
            - ALL string values must have special characters properly escaped
            - Use \\" for quotes inside strings
            - Use \\\\ for backslashes
            - French apostrophes MUST be escaped: "l'amour" → "l\\'amour"
            - Common patterns to escape:
              * "C'est" → "C\\'est"
              * "d'une" → "d\\'une"
              * "l'humilité" → "l\\'humilité"
              * Any ' inside strings → \\'

            Output ONLY valid JSON with properly escaped strings. No markdown, no explanations.""",
        )

    @task
    def write_poem(self) -> Task:
        return Task(
            config=self.tasks_config["write_poem"],
            agent=self.poem_writer(),
            output_pydantic=PoemJSONOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
