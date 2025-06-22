"""
ShoppingAdvisorCrew module for comprehensive shopping advice and product analysis.

This module implements a specialized crew that provides comprehensive shopping advice
including product research, price comparison between Switzerland and France,
competitor analysis, and generates professional HTML reports with actionable recommendations.
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.tools.utility_tools import get_reporting_tools
from epic_news.tools.web_tools import get_search_tools, get_scrape_tools
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.utils.logger import get_logger

logger = get_logger(__name__)


@CrewBase
class ShoppingAdvisorCrew:
    """ShoppingAdvisorCrew that creates comprehensive shopping advice reports."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def product_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["product_researcher"],
            tools=get_search_tools() + get_scrape_tools(),
            verbose=True,
        )

    @agent
    def price_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["price_analyst"],
            tools=get_search_tools() + get_scrape_tools(),
            verbose=True,
        )

    @agent
    def competitor_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["competitor_analyst"],
            tools=get_search_tools() + get_scrape_tools(),
            verbose=True,
        )

    @agent
    def shopping_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["shopping_advisor"],
            tools=get_reporting_tools(),
            verbose=True,
        )

    @task
    def product_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["product_research_task"],
        )

    @task
    def price_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["price_analysis_task"],
        )

    @task
    def competitor_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["competitor_analysis_task"],
        )

    @task
    def shopping_advice_task(self) -> Task:
        return Task(
            config=self.tasks_config["shopping_advice_task"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
