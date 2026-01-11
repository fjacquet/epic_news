from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from loguru import logger

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
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
            config=self.agents_config["lead_researcher_agent"],  # type: ignore[index]
            tools=get_search_tools() + get_scrape_tools() + get_yahoo_finance_tools(),
            allow_delegation=False,
            reasoning=True,
            max_reasoning_attempts=3,
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
            config=self.agents_config["product_specialist_agent"],  # type: ignore[index]
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
            config=self.agents_config["sales_strategist_agent"],  # type: ignore[index]
            tools=get_search_tools() + get_scrape_tools() + get_yahoo_finance_tools(),
            reasoning=True,
            max_reasoning_attempts=3,
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
            config=self.agents_config["briefing_coordinator_agent"],  # type: ignore[index]
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
            config=self.tasks_config["research_task"],  # type: ignore[arg-type, index]
            agent=self.lead_researcher_agent(),  # type: ignore[call-arg]
            async_execution=True,
        )

    @task
    def product_alignment_task(self) -> Task:
        """
        Define the product alignment task for analyzing product fit.
        """
        return Task(
            config=self.tasks_config["product_alignment_task"],  # type: ignore[arg-type, index]
            async_execution=True,
        )  # type: ignore[call-arg]

    @task
    def sales_strategy_task(self) -> Task:
        """
        Define the sales strategy task for developing sales approaches.
        """
        return Task(
            config=self.tasks_config["sales_strategy_task"],  # type: ignore[arg-type, index]
            async_execution=True,
        )  # type: ignore[call-arg]

    @task
    def meeting_preparation_task(self) -> Task:
        """
        Define the meeting preparation task for creating the final briefing.
        Uses MeetingPrepReport Pydantic model for structured output validation.
        """
        return Task(
            config=self.tasks_config["meeting_preparation_task"],  # type: ignore[arg-type, index]
            context=[
                self.research_task(),  # type: ignore[call-arg]
                self.product_alignment_task(),  # type: ignore[call-arg]
                self.sales_strategy_task(),  # type: ignore[call-arg]
            ],
            output_pydantic=MeetingPrepReport,
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates the MeetingPrep crew with configured agents and tasks.
        """
        try:
            return Crew(
                agents=self.agents,  # type: ignore[attr-defined]
                tasks=self.tasks,  # type: ignore[attr-defined]
                process=Process.sequential,
                llm_timeout=LLMConfig.get_timeout("default"),  # type: ignore[call-arg]
                max_iter=LLMConfig.get_max_iter(),
                max_rpm=10,  # Keeping existing custom value (lower than default 20)
                memory=True,
                verbose=True,
            )
        except Exception as e:
            logger.error(f"Error creating MeetingPrep crew: {str(e)}")
            raise
