from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from epic_news.tools.exchange_rate_tool import ExchangeRateTool
from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.web_tools import get_scrape_tools, get_search_tools, get_youtube_tools
from epic_news.tools.report_tools import get_report_tools

from epic_news.models.report import ReportHTMLOutput

# TODO: Consider if get_news_tools might also be relevant for some agents.

load_dotenv()

@CrewBase
class HolidayPlannerCrew():
    """HolidayPlanner crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        super().__init__()
        self._init_tools()

    def _init_tools(self):
        """Initializes and stores all tools for the crew using factory functions."""
        search_tools = get_search_tools() # Provides SerperDevTool
        scrape_tools = get_scrape_tools() # Provides ScrapeNinjaTool
        youtube_tools = get_youtube_tools() # Provides YoutubeVideoSearchTool
        rag_tools = get_rag_tools()
        exchange_rate_tool = ExchangeRateTool()
        report_tools = get_report_tools()

        # Tools for travel research: general search, video, scraping
        self.travel_research_tools = search_tools + youtube_tools + scrape_tools + rag_tools + [exchange_rate_tool]
        
        # Tools for accommodation: general search, scraping
        # (SerperDevTool for general queries, ScrapeNinjaTool for specific details)
        self.accommodation_search_tools = search_tools + scrape_tools + rag_tools + [exchange_rate_tool]

        # Tools for content creation: general search, scraping (for final details, links)
        self.content_creation_tools = search_tools + scrape_tools + rag_tools + [exchange_rate_tool] + report_tools

        # General tools: a comprehensive set for versatile agents like the itinerary architect
        combined_tools_list = (
            self.travel_research_tools
            + self.accommodation_search_tools
            + self.content_creation_tools
        )
        seen_tool_names = set()
        unique_tools = []
        for tool in combined_tools_list:
            if hasattr(tool, 'name') and tool.name not in seen_tool_names:
                unique_tools.append(tool)
                seen_tool_names.add(tool.name)
            elif not hasattr(tool, 'name'): # Handle tools without a name, though unlikely for BaseTool derivatives
                # Decide on a strategy: add them anyway, or log a warning, or skip
                # For now, let's add them if they don't have a name, assuming they are unique by instance
                # Or, better, ensure all tools have a name or a unique ID
                # For robust de-duplication, all tools should ideally have a unique, hashable identifier like 'name'
                # If a tool truly has no name, it might indicate an issue with its definition or it might be a non-standard tool object.
                # Adding a simple check to avoid errors if a tool instance somehow doesn't have 'name'.
                # A more robust solution would be to ensure all tools conform to having a 'name'.
                # For now, let's assume tools lacking a name are unique enough or should be included.
                # However, the primary expectation is that tools from crewAI & crewai_tools will have a .name.
                if tool not in unique_tools: # Fallback to object identity if no name - less reliable for de-duplication
                    unique_tools.append(tool)
        self.general_tools = unique_tools

    @agent
    def travel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["travel_researcher"],
            tools=self.travel_research_tools, # To be populated by _init_tools
            verbose=False,
            reasoning=True,
            allow_delegation=True
        )

    @agent
    def accommodation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["accommodation_specialist"],
            tools=self.accommodation_search_tools, # To be populated by _init_tools
            verbose=False,  
            reasoning=True,
            allow_delegation=True,
        )

    @agent
    def itinerary_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["itinerary_architect"],
            tools=self.general_tools, # To be populated by _init_tools (e.g., search + scrape)
            verbose=False,
            reasoning=True,
            allow_delegation=True,
        )

    @agent
    def budget_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["budget_manager"],
            tools=self.accommodation_search_tools, # To be populated by _init_tools (e.g., shopping search)
            verbose=False,
            allow_delegation=False,
        )

    @agent
    def content_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config["content_formatter"],
            tools=self.content_creation_tools, # To be populated by _init_tools
            verbose=False,
            allow_delegation=False,
        )

    @task
    def research_destination(self) -> Task:
        return Task(
            config=self.tasks_config['research_destination'],
            async_execution=True
        )

    @task
    def recommend_accommodation_and_dining(self) -> Task:
        return Task(
            config=self.tasks_config['recommend_accommodation_and_dining'],
            async_execution=True
        )

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config['plan_itinerary'],
            async_execution=True
        )

    @task
    def analyze_and_optimize_budget(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_and_optimize_budget'],
            async_execution=True
        )

    @task
    def format_and_translate_guide(self) -> Task:
        return Task(
            config=self.tasks_config['format_and_translate_guide'],
            async_execution=False,
            output_file='output/travel_guides/itinerary.html',
            output_pydantic=ReportHTMLOutput
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HolidayPlanner crew"""
        # Use a minimal LLM configuration that relies on environmental defaults
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False, # Consistent with agent verbosity
            max_retry_limit=5,
            max_rpm=30,  # Rate limiting to avoid API issues
        )
