from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool

from epic_news.config.llm_config import LLMConfig


@CrewBase
class RssWeeklyCrew:
    """RssWeekly crew for translating the weekly RSS digest.

    Uses the two-agent pattern recommended in the design principles:
    1. content_reader_agent: Uses tools to read and extract content
    2. translator_agent: No tools, just translates and formats the final output

    This pattern prevents action traces from appearing in the final output.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def content_reader_agent(self) -> Agent:
        """Agent responsible for reading the content from files.
        This agent uses tools but its output won't be the final result."""
        return Agent(
            config=self.agents_config["content_reader_agent"],
            tools=[FileReadTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def translator_agent(self) -> Agent:
        """Agent responsible for translating content and producing clean JSON output.
        This agent has NO tools to ensure clean output without action traces."""
        return Agent(
            config=self.agents_config["translator_agent"],
            tools=[],  # NO TOOLS = No action traces in output
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            allow_delegation=False,
        )

    @task
    def content_reading_task(self) -> Task:
        """Task for reading the content from the input file."""
        return Task(
            config=self.tasks_config["content_reading_task"],
            agent=self.content_reader_agent(),
        )

    @task
    def translation_task(self) -> Task:
        """Task for translating the content into French and formatting as clean JSON."""
        return Task(
            config=self.tasks_config["translation_task"],
            agent=self.translator_agent(),
            context=[self.content_reading_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the RssWeekly translation crew with sequential processing."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
