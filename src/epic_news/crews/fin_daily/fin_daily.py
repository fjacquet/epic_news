from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import KrakenAssetListTool, KrakenTickerInfoTool
from crewai_tools import DirectoryReadTool, FileReadTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.tools.finance_tools import get_crypto_research_tools, get_stock_research_tools
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class FinDailyCrew:
    """FinDaily crew for comprehensive financial portfolio analysis.

    This crew analyzes stock, crypto, and ETF portfolios. The 3 portfolio-analysis
    tasks (stock, crypto, ETF) run asynchronously in parallel. The 3 suggestion
    tasks run synchronously: each depends via context on its async analysis task,
    and an async task may not have an async task in its context (CrewAI 1.15+).
    A final report task then consolidates all findings.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

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
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],  # type: ignore[index]
            # No tools - synthesizes from context provided by analyst tasks
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
            verbose=True,
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
            # Own agent instance: shares the stock_analyst role with the stock analysis
            # task, so needs a distinct executor to run concurrently (CrewAI 1.15+).
            agent=self.stock_analyst().copy(),  # type: ignore[call-arg]
            async_execution=True,  # Independent task, can run in parallel
        )

    @task
    def stock_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["stock_suggestion_task"],  # type: ignore[index, arg-type]
            # Sync: depends on stock_portfolio_analysis_task (async) via context, and
            # an async task may not have an async task in its context (CrewAI 1.15+).
            async_execution=False,
        )

    @task
    def etf_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["etf_suggestion_task"],  # type: ignore[index, arg-type]
            # Sync: see note on stock_suggestion_task.
            async_execution=False,
        )

    @task
    def crypto_suggestion_task(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["crypto_suggestion_task"],  # type: ignore[index, arg-type]
            # Sync: see note on stock_suggestion_task.
            async_execution=False,
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
        )
