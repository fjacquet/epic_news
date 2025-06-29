from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.tools.html_generator_tool import HtmlGeneratorTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class HtmlDesignerCrew:
    """HtmlDesigner crew - Generates professional HTML reports from JSON data"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        """Initialize HtmlDesignerCrew with proper CrewAI tools."""
        super().__init__()
        self._init_tools()

    def _init_tools(self):
        # Data analyzer has tools to read and analyze JSON data
        self.analysis_tools = [
            DirectoryReadTool(),
            FileReadTool(),
        ]

        # HTML designer has the proper CrewAI tool for HTML generation
        self.design_tools = [
            HtmlGeneratorTool(),
        ]

    # All HTML generation is now handled through proper CrewAI agents and tools
    # No bypassing methods allowed per CREWAI_ENGAGEMENT_RULES.md

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

        # CrewAI will handle output_file from task config or inputs

        return Task(
            config=task_config, agent=self.html_designer(), context=[self.data_analysis_task()], verbose=True
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HtmlDesigner crew with unified template system."""
        return Crew(
            agents=[self.data_analyzer(), self.html_designer()],
            tasks=[self.data_analysis_task(), self.html_generation_task()],
            process=Process.sequential,
            verbose=True,
        )
