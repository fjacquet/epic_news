from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_custom_tools import KrakenAssetListTool
from crewai_tools import DirectoryReadTool

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.tools.finance_tools import get_crypto_research_tools, get_stock_research_tools
from epic_news.tools.output_file_read_tool import OutputFileReadTool
from epic_news.tools.scraper_factory import get_scraper


@CrewBase
class FinDailyCrew:
    """FinDaily crew for comprehensive financial portfolio analysis.

    This crew analyzes stock, crypto, and ETF portfolios. Every task runs
    sequentially (async_execution=False): the 3 portfolio-analysis tasks first, then
    the 3 suggestion tasks that consume them via context, then a final report task
    consolidating all findings. See tests/crews/test_async_agent_isolation.py for why
    concurrent async execution is off across the project.
    """

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods

    @agent
    def stock_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["stock_analyst"],
            tools=get_stock_research_tools()
            + [
                # Reads the portfolio CSVs ({stock_csv_path}/{etf_csv_path} under data/);
                # scoped so scraped content cannot steer it to other local files.
                OutputFileReadTool(root="data"),
                # Scope to this crew's own output dir; a bare DirectoryReadTool()
                # defaults to the CWD and exposes the whole repo.
                DirectoryReadTool("output/findaily"),
                get_scraper(),
            ],
            llm=LLMConfig.get_openrouter_llm(),
            # Analyses every ticker of the 60+ line portfolio CSV, roughly one tool call
            # each; the CREW_MAX_ITER default would cut it off partway through.
            max_iter=30,
            verbose=True,
        )

    @agent
    def crypto_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["crypto_analyst"],
            # get_crypto_research_tools() already includes KrakenTickerInfoTool.
            tools=get_crypto_research_tools() + [KrakenAssetListTool(), get_scraper()],
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            # No tools - synthesizes from context provided by analyst tasks
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @task
    def stock_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_portfolio_analysis_task"],
            async_execution=False,
        )

    @task
    def crypto_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["crypto_portfolio_analysis_task"],
            async_execution=False,
        )

    # NEW: ETF portfolio analysis task
    @task
    def etf_portfolio_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_portfolio_analysis_task"],
            # Own agent instance: shares the stock_analyst role with the stock analysis
            # task, so it keeps a distinct executor of its own.
            agent=self.stock_analyst(),
            async_execution=False,
        )

    @task
    def stock_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_suggestion_task"],
            # Consumes stock_portfolio_analysis_task via context.
            async_execution=False,
        )

    @task
    def etf_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_suggestion_task"],
            # Consumes its analysis task via context; see stock_suggestion_task.
            async_execution=False,
        )

    @task
    def crypto_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["crypto_suggestion_task"],
            # Consumes its analysis task via context; see stock_suggestion_task.
            async_execution=False,
        )

    @task
    def final_report_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_generation_task"],
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
        )
