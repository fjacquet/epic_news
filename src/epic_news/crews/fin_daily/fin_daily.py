from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
from epic_news.tools.finance_tools import get_crypto_research_tools, get_stock_research_tools
from epic_news.tools.kraken_api_tool import KrakenAssetListTool, KrakenTickerInfoTool
from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
from epic_news.tools.utility_tools import get_reporting_tools


@CrewBase
class FinDailyCrew:
    """FinDaily crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        self._init_tools()

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    def _init_tools(self):
        """Initialize tools for the crew's agents."""
        self.stock_tools = get_stock_research_tools() + [
            FileReadTool(),
            DirectoryReadTool(),
            ScrapeNinjaTool(),
        ]
        self.crypto_tools = get_crypto_research_tools() + [
            KrakenAssetListTool(),
            KrakenTickerInfoTool(),
            ScrapeNinjaTool(),
        ]
        self.reporting_tools = get_reporting_tools()

    @agent
    def stock_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["stock_analyst"],
            tools=self.stock_tools,
            verbose=True,
        )

    @agent
    def crypto_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["crypto_analyst"],
            tools=self.crypto_tools,
            verbose=True,
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            tools=self.stock_tools + self.crypto_tools,
            verbose=True,
        )

    @agent
    def reporting_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_specialist"],
            tools=self.reporting_tools,
            verbose=True,
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

    @task
    def stock_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_suggestion_task"],
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
                self.stock_suggestion_task(),
                self.crypto_suggestion_task(),
            ],
            output_file="output/findaily/report.html",
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
