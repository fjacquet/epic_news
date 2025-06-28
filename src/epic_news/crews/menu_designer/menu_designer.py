import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.models.html_output import ReportHTMLOutput
from epic_news.models.menu_output import WeeklyMenuPlan
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

    def __init__(self) -> None:
        """Initialize the tools and paths for the crew's agents."""
        self.planning_tools = get_search_tools() + [FileReadTool(), DirectoryReadTool()]

        # Output directory for menu files
        self.output_dir = "output/menu_designer"

    @agent
    def menu_planner(self) -> Agent:
        """Agent responsible for planning the menu structure."""
        # Get config and add any missing required fields
        config = self.agents_config["menu_planner"]

        # Add backstory if missing (required field in newer CrewAI versions)
        if "backstory" not in config:
            config["backstory"] = (
                "Vous êtes un chef expérimenté et diététicien, spécialisé dans la planification de menus hebdomadaires équilibrés et adaptés aux contraintes spécifiques. Vous avez une expertise approfondie en nutrition et en cuisine française et internationale."
            )

        return Agent(
            config=config,
            tools=self.planning_tools,
            respect_context_window=True,
            reasoning=False,
            # llm="gpt-4.1-nano",  # Use more powerful model for menu planning
            verbose=True,
        )

    @agent
    def html_formatter(self) -> Agent:
        """Agent responsible for creating HTML version of the menu."""
        # Get config and add any missing required fields
        config = self.agents_config["html_formatter"]

        # The html_formatter already has a backstory in agents.yaml
        # but adding a check for consistency in case YAML changes
        if "backstory" not in config:
            config["backstory"] = (
                "Vous êtes un designer et développeur front-end talentueux, spécialisé dans la création d'interfaces web élégantes pour l'industrie culinaire et gastronomique."
            )

        return Agent(
            config=config,
            # tools=self.planning_tools,
            respect_context_window=True,
            reasoning=False,
            # llm="gpt-4.1-mini",  # Use more powerful model for HTML creation
            verbose=True,
        )

    @task
    def menu_planning_task(self) -> Task:
        """Task to plan the menu structure, assigned to the menu_planner agent."""
        return Task(
            config=self.tasks_config["menu_planning_task"],
            agent=self.menu_planner(),
            verbose=True,
            output_pydantic=WeeklyMenuPlan,  # Use Pydantic model for structured output
            output_file=os.path.join(self.output_dir, "{menu_slug}.json"),
        )

    @task
    def menu_html_task(self) -> Task:
        """Task to create an HTML version of the menu, assigned to the html_formatter agent."""
        return Task(
            config=self.tasks_config["menu_html_task"],
            agent=self.html_formatter(),
            verbose=True,
            output_pydantic=ReportHTMLOutput,  # Use HTML output model
            output_file=os.path.join(self.output_dir, "{menu_slug}.html"),
        )

    @crew
    def crew(self) -> Crew:
        """Create a menu designer crew with sequential tasks."""
        # Set up the standard crew without any custom wrapper
        return Crew(
            agents=[self.menu_planner(), self.html_formatter()],
            tasks=[self.menu_planning_task(), self.menu_html_task()],
            manager_llm="gpt-4.1-mini",
            process=Process.sequential,
            verbose=True,
        )
