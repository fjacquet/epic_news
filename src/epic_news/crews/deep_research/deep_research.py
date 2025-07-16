from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

from epic_news.models.crews.deep_research_report import DeepResearchReport

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool


@CrewBase
class DeepResearchCrew:
    """DeepResearch crew for comprehensive internet research"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    @agent
    def primary_researcher(self) -> Agent:
        """Primary researcher agent with web search and scraping tools."""
        return Agent(
            config=self.agents_config["primary_researcher"],
            tools=[
                SerperDevTool(n_results=25, search_type="search"),
                SerperDevTool(n_results=15, search_type="news"),
                ScrapeNinjaTool(),
                ScrapeWebsiteTool(),  # Backup scraping tool
            ],
            llm="gpt-4.1",
            verbose=True,
            reasoning=True,
        )

    @agent
    def wikipedia_specialist(self) -> Agent:
        """Wikipedia specialist agent for encyclopedic research."""
        return Agent(
            config=self.agents_config["wikipedia_specialist"],
            tools=[
                WikipediaSearchTool(),
                WikipediaArticleTool(),
            ],
            llm="gpt-4.1-mini",
            verbose=True,
            reasoning=True,
        )

    @agent
    def content_analyst(self) -> Agent:
        """Content analyst agent for synthesis and validation."""
        return Agent(
            config=self.agents_config["content_analyst"],
            tools=[
                SerperDevTool(n_results=30, search_type="search"),  # For validation
            ],
            llm="gpt-4.1-mini",
            verbose=True,
            reasoning=True,
        )

    @agent
    def report_generator(self) -> Agent:
        """Report generator agent for final HTML report creation."""
        return Agent(
            config=self.agents_config["report_generator"],
            llm="gpt-4.1-mini",
            verbose=True,
        )

    @task
    def primary_research_task(self) -> Task:
        """Primary web research task."""
        return Task(
            config=self.tasks_config["primary_research_task"],
            verbose=True,
        )

    @task
    def wikipedia_research_task(self) -> Task:
        """Wikipedia research task."""
        return Task(
            config=self.tasks_config["wikipedia_research_task"],
            verbose=True,
        )

    @task
    def content_analysis_task(self) -> Task:
        """Content analysis and synthesis task."""
        return Task(
            config=self.tasks_config["content_analysis_task"],
            verbose=True,
            context=[
                self.primary_research_task(),
                self.wikipedia_research_task(),
            ],
        )

    @task
    def final_report_generation_task(self) -> Task:
        """Final report generation task with Pydantic output."""
        return Task(
            config=self.tasks_config["final_report_generation_task"],
            verbose=True,
            context=[
                self.primary_research_task(),
                self.wikipedia_research_task(),
                self.content_analysis_task(),
            ],
            output_pydantic=DeepResearchReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DeepResearch crew with 4-agent workflow."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
