from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

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
            respect_context_window=True,
            reasoning=True,
            verbose=True,
        )

    @agent
    def menu_reporter(self) -> Agent:
        """Agent responsible for creating clean JSON output of the menu."""
        return Agent(
            config=self.agents_config["menu_reporter"],
            tools=[],
            respect_context_window=True,
            reasoning=True,
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
            verbose=True,
        )
