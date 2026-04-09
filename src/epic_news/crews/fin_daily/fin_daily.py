from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.tools.finance_tools import get_crypto_research_tools, get_stock_research_tools
from epic_news.tools.kraken_api_tool import KrakenAssetListTool, KrakenTickerInfoTool
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class FinDailyCrew:
    """FinDaily crew for comprehensive financial portfolio analysis.

    This crew analyzes stock, crypto, and ETF portfolios in parallel for maximum performance.
    The 6 portfolio analysis and suggestion tasks execute asynchronously, then a final report
    consolidates all findings. Uses scoped memory to reduce token explosion.

    Performance: ~6x faster with async execution vs sequential.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        self._memory = LLMConfig.get_memory_config()

    @agent
    def stock_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["stock_analyst"],  # type: ignore[index]
            tools=get_stock_research_tools()
            + [
                FileReadTool(),
                DirectoryReadTool(),
                get_scraper(),
            ],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            memory=self._memory.scope("/agent/stock_analyst"),
        )

    @agent
    def crypto_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["crypto_analyst"],  # type: ignore[index]
            tools=get_crypto_research_tools()
            + [
                KrakenAssetListTool(),
                KrakenTickerInfoTool(),
                get_scraper(),
            ],
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            memory=self._memory.scope("/agent/crypto_analyst"),
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],  # type: ignore[index]
            # No tools - synthesizes from context provided by analyst tasks
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
            memory=self._memory.scope("/agent/investment_strategist"),
        )

    @task
    def stock_portfolio_analysis_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["stock_portfolio_analysis_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def crypto_portfolio_analysis_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["crypto_portfolio_analysis_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    # NEW: ETF portfolio analysis task
    @task
    def etf_portfolio_analysis_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["etf_portfolio_analysis_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def stock_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["stock_suggestion_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def etf_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["etf_suggestion_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def crypto_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["crypto_suggestion_task"],  # type: ignore[index, arg-type]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def final_report_generation_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["final_report_generation_task"],  # type: ignore[index, arg-type]
            context=[
                self.stock_portfolio_analysis_task(),  # type: ignore[call-arg]
                self.crypto_portfolio_analysis_task(),  # type: ignore[call-arg]
                self.etf_portfolio_analysis_task(),  # type: ignore[call-arg]
                self.stock_suggestion_task(),  # type: ignore[call-arg]
                self.etf_suggestion_task(),  # type: ignore[call-arg]
                self.crypto_suggestion_task(),  # type: ignore[call-arg]
            ],
            output_pydantic=FinancialReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the FinDaily crew"""
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
            memory=self._memory,
        )
