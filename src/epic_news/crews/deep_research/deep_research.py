from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    BraveSearchTool,
    CodeInterpreterTool,
    FileReadTool,
    ScrapeWebsiteTool,
    SerperDevTool,
)

from epic_news.models.crews.deep_research_report import DeepResearchReport
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool


@CrewBase
class DeepResearchCrew:
    """DeepResearch crew for comprehensive internet research with 6-agent architecture"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    code_interpreter = CodeInterpreterTool(default_image_tag="fjacquet/code-interpreter:latest")

    # Research Strategist - Planning and methodology
    @agent
    def research_strategist(self) -> Agent:
        """Research strategist agent for planning and methodology."""
        return Agent(
            config=self.agents_config["research_strategist"],
            tools=[],  # Strategic planning, no external tools needed
            verbose=True,
        )

    # Information Collector - Web research and data collection
    @agent
    def information_collector(self) -> Agent:
        """Information collector agent with web search and scraping tools."""
        return Agent(
            config=self.agents_config["information_collector"],
            tools=[
                BraveSearchTool(),
                SerperDevTool(n_results=25, search_type="search"),
                SerperDevTool(n_results=25, search_type="news"),
                # ScrapeNinjaTool(),
                ScrapeWebsiteTool(),
                FileReadTool(),  # Backup scraping tool
            ],
            llm="gpt-5-mini",
            verbose=True,
            reasoning=True,
        )

    # Wikipedia Specialist - Encyclopedic research
    @agent
    def wikipedia_specialist(self) -> Agent:
        """Wikipedia specialist agent for encyclopedic research."""
        return Agent(
            config=self.agents_config["wikipedia_specialist"],
            tools=[
                WikipediaSearchTool(),
                WikipediaArticleTool(),
            ],
            verbose=True,
            respect_context_window=True,
        )

    # Data Analyst - Analysis and synthesis with Code Interpreter
    @agent
    def data_analyst(self) -> Agent:
        """Data analyst agent for synthesis and quantitative analysis with Code Interpreter."""
        return Agent(
            config=self.agents_config["data_analyst"],
            tools=[self.code_interpreter, FileReadTool()],
            llm="gpt-5-mini",
            verbose=True,
            allow_code_execution=True,  # Enable Code Interpreter for real quantitative analysis
        )

    # Report Writer - Technical writing
    @agent
    def report_writer(self) -> Agent:
        """Report writer agent for technical report creation."""
        return Agent(
            config=self.agents_config["report_writer"],
            tools=[],  # Report writing, no external tools needed
            llm="gpt-5-mini",
            verbose=True,
        )

    # # Quality Assurance - QA and editorial review
    # @agent
    # def quality_assurance(self) -> Agent:
    #     """Quality assurance agent for editorial review and fact-checking."""
    #     return Agent(
    #         config=self.agents_config["quality_assurance"],
    #         tools=[],  # QA and editing, no external tools needed
    #         llm="gpt-5-mini",
    #         verbose=True,
    #     )

    # Task 1: Research Planning
    @task
    def reformulate_task(self) -> Task:
        """Reformulate task."""
        return Task(
            config=self.tasks_config["reformulate_task"],
            verbose=True,
        )

    @task
    def research_planning_task(self) -> Task:
        """Research planning and methodology task."""
        return Task(
            config=self.tasks_config["research_planning_task"],
            verbose=True,
        )

    # Task 2: Information Collection
    @task
    def information_collection_task(self) -> Task:
        """Information collection task."""
        return Task(
            config=self.tasks_config["information_collection_task"],
            verbose=True,
            context=[
                self.research_planning_task(),
            ],
        )

    # Task 3: Wikipedia Research
    @task
    def wikipedia_research_task(self) -> Task:
        """Wikipedia research task."""
        return Task(
            config=self.tasks_config["wikipedia_research_task"],
            verbose=True,
            context=[
                self.research_planning_task(),
                self.information_collection_task(),
            ],
        )

    # Task 4: Data Analysis
    @task
    def data_analysis_task(self) -> Task:
        """Data analysis and synthesis task."""
        return Task(
            config=self.tasks_config["data_analysis_task"],
            verbose=True,
            context=[
                self.research_planning_task(),
                self.information_collection_task(),
                self.wikipedia_research_task(),
            ],
        )

    # Task 5: Report Writing
    @task
    def report_writing_task(self) -> Task:
        """Report writing task."""
        return Task(
            config=self.tasks_config["report_writing_task"],
            verbose=True,
            context=[
                self.research_planning_task(),
                self.information_collection_task(),
                self.wikipedia_research_task(),
                self.data_analysis_task(),
            ],
            output_pydantic=DeepResearchReport,
        )

    # # Task 6: Quality Assurance (Final)
    # @task
    # def quality_assurance_task(self) -> Task:
    #     """Quality assurance and final validation task."""
    #     # Import at the method level to avoid circular imports
    #     from epic_news.models.crews.deep_research_report import DeepResearchReport

    #     return Task(
    #         config=self.tasks_config["quality_assurance_task"],
    #         verbose=True,
    #         context=[
    #             self.research_planning_task(),
    #             self.information_collection_task(),
    #             self.wikipedia_research_task(),
    #             self.data_analysis_task(),
    #             self.report_writing_task(),
    #         ],
    #         output_pydantic=DeepResearchReport,
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the DeepResearch crew with 6-agent sequential process."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,  # Automatically created from the tasks above
            process=Process.sequential,
            # manager_llm="gpt-4.1-nano",
            verbose=True,
            # planning=True,
        )
