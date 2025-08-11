from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.models.crews.financial_report import FinancialReport
from epic_news.tools.finance_tools import get_crypto_research_tools, get_stock_research_tools
from epic_news.tools.kraken_api_tool import KrakenAssetListTool, KrakenTickerInfoTool
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class FinDailyCrew:
    """FinDaily crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def stock_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["stock_analyst"],
            tools=get_stock_research_tools()
            + [
                FileReadTool(),
                DirectoryReadTool(),
                get_scraper(),
            ],
            llm="gpt-5-mini",
            verbose=True,
            memory=True,
        )

    @agent
    def crypto_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["crypto_analyst"],
            tools=get_crypto_research_tools()
            + [
                KrakenAssetListTool(),
                KrakenTickerInfoTool(),
                get_scraper(),
            ],
            llm="gpt-5-mini",
            verbose=True,
            memory=True,
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            # No tools - synthesizes from context provided by analyst tasks
            llm="gpt-5-mini",
            verbose=True,
            memory=True,
        )

    @task
    def stock_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_portfolio_analysis_task"],
            verbose=True,
        )

    @task
    def crypto_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["crypto_portfolio_analysis_task"],
            verbose=True,
        )

    # NEW: ETF portfolio analysis task
    @task
    def etf_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_portfolio_analysis_task"],
            verbose=True,
        )

    @task
    def stock_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_suggestion_task"],
            verbose=True,
        )

    @task
    def etf_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_suggestion_task"],
            verbose=True,
        )

    @task
    def crypto_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["crypto_suggestion_task"],
            verbose=True,
        )

    @task
    def final_report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_generation_task"],
            verbose=True,
            context=[
                self.stock_portfolio_analysis_task(),
                self.crypto_portfolio_analysis_task(),
                self.etf_portfolio_analysis_task(),
                self.stock_suggestion_task(),
                self.etf_suggestion_task(),
                self.crypto_suggestion_task(),
            ],
            output_pydantic=FinancialReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the FinDaily crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            memory_config={
                "provider": "mem0",
                "config": {"user_id": "fin_daily"},
            },
        )
