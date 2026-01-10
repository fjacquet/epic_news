from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.tools.finance_tools import get_yahoo_finance_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools

load_dotenv()


@CrewBase
class MeetingPrepCrew:
    """
    MeetingPrep crew for preparing comprehensive meeting briefings.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def lead_researcher_agent(self) -> Agent:
        """
        Create a lead researcher agent responsible for gathering information.
        """
        return Agent(
            config=self.agents_config["lead_researcher_agent"],
            tools=get_search_tools() + get_scrape_tools() + get_yahoo_finance_tools(),
            allow_delegation=False,
            reasoning=True,
            verbose=True,
            respect_context_window=True,
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @agent
    def product_specialist_agent(self) -> Agent:
        """
        Create a product specialist agent for product-related analysis.
        """
        return Agent(
            config=self.agents_config["product_specialist_agent"],
            tools=get_search_tools() + get_scrape_tools() + get_yahoo_finance_tools(),
            allow_delegation=False,
            verbose=True,
            respect_context_window=True,
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @agent
    def sales_strategist_agent(self) -> Agent:
        """
        Create a sales strategist agent for developing sales approaches.
        """
        return Agent(
            config=self.agents_config["sales_strategist_agent"],
            tools=get_search_tools() + get_scrape_tools() + get_yahoo_finance_tools(),
            reasoning=True,
            verbose=True,
            respect_context_window=True,
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @agent
    def briefing_coordinator_agent(self) -> Agent:
        """
        Create a briefing coordinator agent to compile the final briefing.
        """
        return Agent(
            config=self.agents_config["briefing_coordinator_agent"],
            tools=get_report_tools(),
            verbose=True,
            respect_context_window=True,
            llm_timeout=LLMConfig.get_timeout("default"),
        )

    @task
    def research_task(self) -> Task:
        """
        Define the research task for gathering meeting-related information.
        """
        return Task(
            config=self.tasks_config["research_task"],
            agent=self.lead_researcher_agent(),
            async_execution=True,
        )

    @task
    def product_alignment_task(self) -> Task:
        """
        Define the product alignment task for analyzing product fit.
        """
        return Task(
            config=self.tasks_config["product_alignment_task"],
            async_execution=True,
        )

    @task
    def sales_strategy_task(self) -> Task:
        """
        Define the sales strategy task for developing sales approaches.
        """
        return Task(
            config=self.tasks_config["sales_strategy_task"],
            async_execution=True,
        )

    @task
    def meeting_preparation_task(self) -> Task:
        """
        Define the meeting preparation task for creating the final briefing.
        """
        return Task(
            config=self.tasks_config["meeting_preparation_task"],
            context=[
                self.research_task(),
                self.product_alignment_task(),
                self.sales_strategy_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates the MeetingPrep crew with configured agents and tasks.
        """
        try:
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                llm_timeout=LLMConfig.get_timeout("default"),
                max_iter=LLMConfig.get_max_iter(),
                max_rpm=10,  # Keeping existing value (lower than default 20)
                memory=True,
            )
        except Exception as e:
            logger.error(f"Error creating MeetingPrep crew: {str(e)}")
            raise
