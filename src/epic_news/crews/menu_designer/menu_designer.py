import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.models.menu_output import WeeklyMenuPlan
from epic_news.tools.web_tools import get_search_tools
from epic_news.utils.file_utils import ensure_output_directory


@CrewBase
class MenuDesignerCrew:
    """
    MenuDesigner crew for generating the weekly French menu structure.

    This crew is responsible only for planning the menu. The detailed recipe
    generation and file output is handled by a different process.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        """Initialize the tools and paths for the crew's agents."""
        self.planning_tools = get_search_tools() + [FileReadTool(), DirectoryReadTool()]

        # Output directory for menu files
        self.output_dir = "output/menu_designer"

        # Ensure output directory exists
        ensure_output_directory(self.output_dir)

    @agent
    def menu_researcher(self) -> Agent:
        """Agent responsible for researching and planning the menu structure."""
        # Get config and add any missing required fields
        config = self.agents_config["menu_researcher"]

        return Agent(
            config=config,
            tools=self.planning_tools,  # Researcher has tools for data gathering
            respect_context_window=True,
            reasoning=True,
            verbose=True,
        )

    @agent
    def menu_reporter(self) -> Agent:
        """Agent responsible for creating clean JSON output of the menu."""
        # Get config from the YAML file
        config = self.agents_config["menu_reporter"]

        return Agent(
            config=config,
            tools=[],  # Reporter has no tools to ensure clean output
            respect_context_window=True,
            reasoning=True,
            verbose=True,
        )

    @task
    def menu_planning_task(self) -> Task:
        """Task to plan the menu structure, assigned to the menu_researcher agent."""
        return Task(
            config=self.tasks_config["menu_planning_task"],
            agent=self.menu_researcher(),
            verbose=True,
            output_pydantic=WeeklyMenuPlan,  # Use Pydantic model for structured output
            output_file=os.path.join(self.output_dir, "menu_research_{menu_slug}.json"),
        )

    @task
    def menu_json_task(self) -> Task:
        """Task to create a clean JSON version of the menu, assigned to the menu_reporter agent."""
        return Task(
            config=self.tasks_config["menu_json_task"],
            agent=self.menu_reporter(),
            verbose=True,
            output_file=os.path.join(self.output_dir, "{menu_slug}.json"),
        )

    @crew
    def crew(self) -> Crew:
        """Create a menu designer crew with hierarchical process."""
        # Implement the Two-Agent Pattern: researcher gathers data, reporter creates clean output
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_llm="gpt-4.1-mini",
            process=Process.hierarchical,  # Use hierarchical process for better orchestration
            verbose=True,
        )
