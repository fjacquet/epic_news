from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.tools.web_tools import get_search_tools


@CrewBase
class MenuDesignerCrew:
    """
    MenuDesigner crew for generating the weekly French menu structure.

    This crew is responsible only for planning the menu. The detailed recipe
    generation and file output is handled by a different process.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def menu_researcher(self) -> Agent:
        """Agent responsible for researching and planning the menu structure."""
        return Agent(
            config=self.agents_config["menu_researcher"],
            tools=get_search_tools() + [FileReadTool(), DirectoryReadTool()],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
            verbose=True,
        )

    @agent
    def menu_reporter(self) -> Agent:
        """Agent responsible for creating clean JSON output of the menu."""
        return Agent(
            config=self.agents_config["menu_reporter"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            respect_context_window=True,
            reasoning=True,
            max_reasoning_attempts=3,
            verbose=True,
        )

    @task
    def menu_planning_task(self) -> Task:
        """Task to plan the menu structure, assigned to the menu_researcher agent."""
        return Task(
            config=self.tasks_config["menu_planning_task"],
            verbose=True,
            output_pydantic=WeeklyMenuPlan,
            output_file="output/menu_designer/menu_research_{menu_slug}.json",
        )

    @task
    def menu_json_task(self) -> Task:
        """Task to create a clean JSON version of the menu, assigned to the menu_reporter agent."""
        return Task(
            config=self.tasks_config["menu_json_task"],
            context=[self.menu_planning_task()],
            verbose=True,
            output_file="output/menu_designer/{menu_slug}.json",
        )

    @crew
    def crew(self) -> Crew:
        """Create a menu designer crew with hierarchical process."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            llm_timeout=LLMConfig.get_timeout("default"),
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
