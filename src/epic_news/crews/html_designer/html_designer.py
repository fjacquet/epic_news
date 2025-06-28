import os
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.utils.html.path import determine_output_path
from epic_news.utils.html.template_manager import TemplateManager

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class HtmlDesignerCrew:
    """HtmlDesigner crew - Generates professional HTML reports from JSON data"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        """Initialize HtmlDesignerCrew with unified template system."""
        super().__init__()
        self.selected_crew = None
        self.output_file_path = None
        self.template_manager = TemplateManager()
        self._init_tools()

    def _init_tools(self):
        # Data analyzer has tools to read and analyze JSON data
        self.analysis_tools = [
            DirectoryReadTool(),
            FileReadTool(),
        ]

        # HTML designer has NO TOOLS (critical pattern) to generate clean HTML output
        # Template rendering is handled programmatically via TemplateManager
        self.design_tools = []

    # Les méthodes _extract_recipe_title_from_state et _generate_cooking_output_path
    # ont été externalisées dans le module path_utils.py

    def kickoff_with_template(self, inputs: dict[str, Any]) -> str:
        """Execute crew and return rendered HTML using unified template system."""
        # Extract state data from inputs
        state_data = inputs.get("state_data", {})

        # Render the unified report directly
        return self.render_unified_report(state_data)

    def set_crew_context(self, selected_crew: str, state_data: dict[str, Any] = None) -> None:
        """Set the crew context and determine output file path."""
        self.selected_crew = selected_crew
        self.output_file_path = determine_output_path(selected_crew, state_data)

        # Log template system usage
        print(f" HtmlDesignerCrew configured for {selected_crew} with unified template system")
        print(f" Output path: {self.output_file_path}")
        print(" Dark mode and responsive design enabled via universal template")

    @agent
    def data_analyzer(self) -> Agent:
        """Agent responsible for analyzing JSON data from other crews"""
        return Agent(
            config=self.agents_config["data_analyzer"],
            tools=self.analysis_tools,
            verbose=True,
        )

    @agent
    def html_designer(self) -> Agent:
        """Agent responsible for generating clean HTML output using TemplateManager"""
        return Agent(
            config=self.agents_config["html_designer"],
            tools=self.design_tools,
            verbose=True,
        )

    @task
    def data_analysis_task(self) -> Task:
        """Task to analyze and structure JSON data from other crews"""
        return Task(
            config=self.tasks_config["data_analysis_task"],
            verbose=True,
        )

    @task
    def html_generation_task(self) -> Task:
        """HTML generation task using unified template system."""
        task_config = self.tasks_config["html_generation_task"].copy()

        # Use the dynamically determined output file path
        if self.output_file_path:
            task_config["output_file"] = self.output_file_path

        return Task(
            config=task_config, agent=self.html_designer(), context=[self.data_analysis_task()], verbose=True
        )

    def render_unified_report(self, state_data: dict[str, Any]) -> str:
        """Render a unified HTML report using the template system."""
        selected_crew = state_data.get("selected_crew", "UNKNOWN")

        # Déterminer le chemin de sortie basé sur state_data
        self.output_file_path = determine_output_path(selected_crew, state_data)

        # Extract relevant content data based on crew type
        content_data = self._extract_content_data(state_data, selected_crew)

        # Use template manager to render the report
        html_content = self.template_manager.render_report(selected_crew, content_data)

        # Ensure output directory exists
        output_dir = os.path.dirname(self.output_file_path)
        os.makedirs(output_dir, exist_ok=True)

        # Write the HTML content to the output file
        with open(self.output_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ HTML report generated at: {self.output_file_path}")

        return html_content

    def _extract_content_data(self, state_data: dict[str, Any], selected_crew: str) -> dict[str, Any]:
        """Extract and structure content data based on crew type using factory pattern."""
        from epic_news.utils.content_extractors import ContentExtractorFactory

        return ContentExtractorFactory.extract_content(state_data, selected_crew)

    @crew
    def crew(self) -> Crew:
        """Creates the HtmlDesigner crew with unified template system."""
        return Crew(
            agents=[self.data_analyzer(), self.html_designer()],
            tasks=[self.data_analysis_task(), self.html_generation_task()],
            process=Process.sequential,
            verbose=True,
        )
