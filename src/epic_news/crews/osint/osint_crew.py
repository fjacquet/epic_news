from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet
from dotenv import load_dotenv
import os
import inspect

load_dotenv()

# Initialize comprehensive Composio toolset
toolset = ComposioToolSet()

# Core search and information gathering tools
search_tools = toolset.get_tools(
    actions=[
        "COMPOSIO_SEARCH_SEARCH",
        "COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH",
        "FIRECRAWL_CRAWL_URLS",
    ]
)

# Financial and business intelligence tools
finance_tools = toolset.get_tools(
    actions=[
        "COMPOSIO_SEARCH_FINANCE_SEARCH",
        "COMPOSIO_SEARCH_NEWS_SEARCH",
    ]
)

# Social media and digital presence tools
social_tools = toolset.get_tools(
    actions=[
        "REDDIT_SEARCH_ACROSS_SUBREDDITS",
        # 'TWITTER_SEARCH_TWEETS',  # If available
    ]
)

# Technical and cybersecurity tools
tech_tools = toolset.get_tools(
    actions=[
        "HACKERNEWS_GET_FRONTPAGE",
        "GITHUB_SEARCH_REPOSITORIES",  # If available
    ]
)

# Combine all tools for agents that need comprehensive access
all_tools = toolset.get_tools(
    actions=[
        "COMPOSIO_SEARCH_SEARCH",
        "COMPOSIO_SEARCH_FINANCE_SEARCH",
        "COMPOSIO_SEARCH_NEWS_SEARCH",
        "COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH",
        "FIRECRAWL_CRAWL_URLS",
        "REDDIT_SEARCH_ACROSS_SUBREDDITS",
        # 'TWITTER_SEARCH_TWEETS',  # If available
        "HACKERNEWS_GET_FRONTPAGE",
        "GITHUB_SEARCH_REPOSITORIES",  # If available
    ]
)


@CrewBase
class OsintCrew:
    """OSINT Intelligence Crew with Composio Tool Integration

    This crew orchestrates a professional OSINT investigation process using specialized agents
    with access to Composio intelligence tools. The workflow follows a structured intelligence cycle
    with chief_coordinator as the central orchestrator.
    """

    # Configuration files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Core coordination and reporting agents
    def chief_coordinator(self) -> Agent:
        """Central orchestrator for the OSINT investigation with delegation capabilities."""
        return Agent(
            config=self.agents_config["chief_coordinator"],
            verbose=True,
            allow_delegation=True,
            respect_context_window=True,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Final report specialist responsible for executive-level reporting."""
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def integration_analyst(self) -> Agent:
        """Integration specialist responsible for validating and combining intelligence."""
        return Agent(
            config=self.agents_config[
                "chief_coordinator"
            ],  # Reuse chief_coordinator config
            verbose=True,
            tools=all_tools,
            allow_delegation=True,
            respect_context_window=True,
        )

    # Core intelligence gathering agents
    @agent
    def company_profile_analyst(self) -> Agent:
        """Company profile specialist focusing on organizational intelligence."""
        return Agent(
            config=self.agents_config["company_profile_analyst"],
            verbose=True,
            tools=search_tools + finance_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def financial_analyst(self) -> Agent:
        """Financial intelligence specialist focusing on economic analysis."""
        return Agent(
            config=self.agents_config["financial_analyst"],
            verbose=True,
            tools=finance_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def industry_innovation_analyst(self) -> Agent:
        """Innovation intelligence specialist focusing on R&D and patents."""
        return Agent(
            config=self.agents_config["industry_innovation_analyst"],
            verbose=True,
            tools=search_tools + tech_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def competitor_mapping_analyst(self) -> Agent:
        """Competitive intelligence specialist for market analysis."""
        return Agent(
            config=self.agents_config["competitor_mapping_analyst"],
            verbose=True,
            tools=search_tools + finance_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def social_media_analyst(self) -> Agent:
        """Digital presence analyst focusing on social media intelligence."""
        return Agent(
            config=self.agents_config["social_media_analyst"],
            verbose=True,
            tools=social_tools + search_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def regulatory_analyst(self) -> Agent:
        """Regulatory intelligence specialist focusing on compliance and legal risks."""
        return Agent(
            config=self.agents_config["regulatory_analyst"],
            verbose=True,
            tools=search_tools + finance_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def cyber_threat_analyst(self) -> Agent:
        """Cyber threat intelligence specialist focusing on digital security."""
        return Agent(
            config=self.agents_config["cyber_threat_analyst"],
            verbose=True,
            tools=search_tools + tech_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    # Initial data gathering tasks
    @task
    def company_profile_task(self) -> Task:
        """Company profile creation - first phase task"""
        return Task(
            config=self.tasks_config["company_profile_task"],
            agent=self.company_profile_analyst,
            output_file="temp/company_profile.html",
        )

    @task
    def financial_task(self) -> Task:
        """Financial analysis - first phase task"""
        return Task(
            config=self.tasks_config["financial_task"],
            agent=self.financial_analyst,
            output_file="temp/financial_report.html",
        )

    @task
    def industry_innovation_task(self) -> Task:
        """Industry innovation analysis - first phase task"""
        return Task(
            config=self.tasks_config["industry_innovation_task"],
            agent=self.industry_innovation_analyst,
            output_file="temp/industry_innovation.html",
        )

    # Second phase tasks that use outputs from first phase
    @task
    def competitor_mapping_task(self) -> Task:
        """Competitor mapping - depends on company profile and financials"""
        return Task(
            config=self.tasks_config["competitor_mapping_task"],
            agent=self.competitor_mapping_analyst,
            input_files=["temp/company_profile.html", "temp/financial_report.html"],
            output_file="temp/competitor_mapping.html",
        )

    @task
    def social_media_sentiment_task(self) -> Task:
        """Social media analysis - builds on company profile"""
        return Task(
            config=self.tasks_config["social_media_sentiment_task"],
            agent=self.social_media_analyst,
            input_files=["temp/company_profile.html"],
            output_file="temp/social_media_sentiment.html",
        )

    @task
    def regulatory_overview_task(self) -> Task:
        """Regulatory analysis - uses company and financial data"""
        return Task(
            config=self.tasks_config["regulatory_overview_task"],
            agent=self.regulatory_analyst,
            input_files=["temp/company_profile.html", "temp/financial_report.html"],
            output_file="temp/regulatory_overview.html",
        )

    @task
    def cyber_threat_snapshot_task(self) -> Task:
        """Cyber threat assessment - uses company profile data"""
        return Task(
            config=self.tasks_config["cyber_threat_snapshot_task"],
            agent=self.cyber_threat_analyst,
            input_files=["temp/company_profile.html"],
            output_file="temp/cyber_threat_snapshot.html",
        )

    # Integration and reporting tasks
    @task
    def validation_notes(self) -> Task:
        """Validation of all gathered intelligence"""
        return Task(
            config=self.tasks_config["validation_notes"],
            agent=self.integration_analyst,
            input_files=[
                "temp/company_profile.html",
                "temp/financial_report.html",
                "temp/industry_innovation.html",
                "temp/competitor_mapping.html",
                "temp/social_media_sentiment.html",
                "temp/regulatory_overview.html",
                "temp/cyber_threat_snapshot.html",
            ],
            output_file="temp/validation_notes.html",
        )

    @task
    def unified_narrative_outline(self) -> Task:
        """Create unified narrative from all intelligence"""
        return Task(
            config=self.tasks_config["unified_narrative_outline"],
            agent=self.integration_analyst,
            input_files=[
                "temp/company_profile.html",
                "temp/financial_report.html",
                "temp/industry_innovation.html",
                "temp/competitor_mapping.html",
                "temp/social_media_sentiment.html",
                "temp/regulatory_overview.html",
                "temp/cyber_threat_snapshot.html",
                "temp/validation_notes.html",
            ],
            output_file="temp/unified_narrative.html",
        )

    @task
    def intelligence_report(self) -> Task:
        """Final comprehensive intelligence report"""
        return Task(
            config=self.tasks_config["intelligence_report"],
            agent=self.integration_analyst,
            input_files=[
                "temp/company_profile.html",
                "temp/financial_report.html",
                "temp/industry_innovation.html",
                "temp/competitor_mapping.html",
                "temp/social_media_sentiment.html",
                "temp/regulatory_overview.html",
                "temp/cyber_threat_snapshot.html",
                "temp/validation_notes.html",
                "temp/unified_narrative.html",
            ],
            output_file="temp/intelligence_report.html",
        )

    @task
    def executive_summary(self) -> Task:
        """Executive summary based on the full intelligence report"""
        return Task(
            config=self.tasks_config["executive_summary"],
            agent=self.reporting_analyst,
            input_files=["temp/intelligence_report.html"],
            output_file="temp/executive_summary.html",
        )

    @task
    def reporter_task(self) -> Task:
        """Final report compilation in French as requested"""
        return Task(
            config=self.tasks_config["reporter_task"],
            agent=self.reporting_analyst,
            input_files=[
                "temp/intelligence_report.html",
                "temp/executive_summary.html",
            ],
            output_file="output/{company}_osint_report.html",
        )

    @property
    def tasks(self):
        """Dynamic task discovery using reflection"""
        tasks = []
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_crewai_task'):
                tasks.append(method())
        return tasks

    @property
    def agents(self):
        """Dynamic agent discovery using reflection"""
        agents = []
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_crewai_agent'):
                agents.append(method())
        return agents

    @crew
    def crew(self) -> Crew:
        """Creates the OSINT crew with hierarchical process to reduce LLM calls"""
        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            # Use hierarchical process instead of sequential to respect task dependencies
            process=Process.hierarchical,
            verbose=True,
        )
