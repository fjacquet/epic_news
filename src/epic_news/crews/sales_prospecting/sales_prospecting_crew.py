
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

from epic_news.tools.email_search import get_email_search_tools
from epic_news.tools.web_tools import get_search_tools
from epic_news.tools.report_tools import get_report_tools
from epic_news.tools.data_centric_tools import get_data_centric_tools
from epic_news.models.report import ReportHTMLOutput
from epic_news.models.data_metrics import StructuredDataReport

load_dotenv()


@CrewBase
class SalesProspectingCrew():
    """Sales Prospecting crew for finding sales contacts at target companies"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self) -> None:
        self._init_tools()

    def _init_tools(self) -> None:
        """Initialize tools for the crew."""
        # It's crucial to have a variety of tools. General search is good for context,
        # but specialized tools are essential for finding specific information like emails.
        self.search_tools = get_search_tools()
        self.email_search_tools = get_email_search_tools()
        self.read_tools = [FileReadTool(), DirectoryReadTool("output/sales_prospecting")]
        self.report_tools = get_report_tools()
        self.data_centric_tools = get_data_centric_tools()

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["company_researcher"],
            tools=[*self.search_tools, *self.email_search_tools, *self.read_tools, *self.report_tools, *self.data_centric_tools],
            verbose=True,
            llm_timeout=300,
            reasoning=True,     
            max_reasoning_attempts=5,
            respect_context_window=True
        )

    @agent
    def org_structure_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["org_structure_analyst"],
            tools=[*self.search_tools, *self.email_search_tools, *self.read_tools, *self.report_tools, *self.data_centric_tools],
            verbose=True,
            reasoning=True,     
            max_reasoning_attempts=5,
            llm_timeout=300,
            respect_context_window=True
        )

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],
            tools=[*self.search_tools, *self.email_search_tools, *self.read_tools, *self.report_tools, *self.data_centric_tools],
            verbose=True,
            reasoning=True,     
            max_reasoning_attempts=5,
            llm_timeout=300,
            respect_context_window=True
        )

    @agent
    def sales_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["sales_strategist"],
            tools=[*self.search_tools, *self.email_search_tools, *self.read_tools, *self.report_tools, *self.data_centric_tools],
            verbose=True,
            reasoning=True,     
            max_reasoning_attempts=5,
            llm_timeout=300,
            respect_context_window=True
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_company_task"],
            async_execution=True,
        )

    @task
    def analyze_org_structure_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_org_structure_task"],
            async_execution=True,
        )

    @task
    def find_key_contacts_task(self) -> Task:
        return Task(
            config=self.tasks_config["find_key_contacts_task"],
            async_execution=True,
        )

    @task
    def develop_approach_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["develop_approach_strategy_task"],
            async_execution=False,
            output_pydantic=ReportHTMLOutput,
        )
        
    @task
    def generate_sales_metrics_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_sales_metrics_task"],
            async_execution=False,
            output_pydantic=StructuredDataReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Sales Prospecting crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            reasoning=True,     
            max_reasoning_attempts=5,
            max_iter=5,
            max_retry_limit=3,
            max_rpm=10, 
        )
