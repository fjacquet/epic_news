from composio_crewai import ComposioToolSet
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.models.report import ReportHTMLOutput
from epic_news.tools.report_tools import get_report_tools

load_dotenv()

# Set up the tools for marketing tasks
toolset = ComposioToolSet()
marketing_tools = toolset.get_tools(
    actions=[
        "COMPOSIO_SEARCH_SEARCH",
        "COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH",
    ]
)


@CrewBase
class MarketingWritersCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def marketing_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["marketing_specialist"],
            tools=marketing_tools + get_report_tools(),
            verbose=True,
            llm_timeout=300,
            respect_context_window=True,
        )

    @agent
    def copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["copywriter"],
            tools=marketing_tools + get_report_tools(),
            verbose=True,
            llm_timeout=300,
            respect_context_window=True,
        )

    @task
    def analyze_market_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_market_task"],
            agent=self.marketing_specialist(),
            verbose=True,
            llm_timeout=300,
        )

    @task
    def enhance_message_task(self) -> Task:
        return Task(
            config=self.tasks_config["enhance_message_task"],
            agent=self.copywriter(),
            output_file="output/marketing/enhanced_message.html",
            output_pydantic=ReportHTMLOutput,
            verbose=True,
            llm_timeout=300,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Marketing Writers crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
