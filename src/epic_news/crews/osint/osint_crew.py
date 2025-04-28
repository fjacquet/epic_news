from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from composio_crewai import ComposioToolSet
from dotenv import load_dotenv

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
            memory=True,
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
            memory=True,
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

    @agent
    def company_profiler(self) -> Agent:
        """Company profile specialist for detailed corporate intelligence."""
        return Agent(
            config=self.agents_config["company_profiler"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def web_presence_investigator(self) -> Agent:
        """Web presence investigator for online digital footprint analysis."""
        return Agent(
            config=self.agents_config["web_presence_investigator"],
            verbose=True,
            tools=search_tools + social_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def hr_intelligence_specialist(self) -> Agent:
        """HR intelligence specialist for workforce and talent analysis."""
        return Agent(
            config=self.agents_config["hr_intelligence_specialist"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def tech_stack_analyst(self) -> Agent:
        """Tech stack analyst for technology infrastructure assessment."""
        return Agent(
            config=self.agents_config["tech_stack_analyst"],
            verbose=True,
            tools=search_tools + tech_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def language_specialist(self) -> Agent:
        """Language specialist for multilingual content analysis."""
        return Agent(
            config=self.agents_config["language_specialist"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def legal_analyst(self) -> Agent:
        """Legal analyst for regulatory and compliance assessment."""
        return Agent(
            config=self.agents_config["legal_analyst"],
            verbose=True,
            tools=search_tools + finance_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    @agent
    def geospatial_analyst(self) -> Agent:
        """Geospatial analyst for location-based intelligence."""
        return Agent(
            config=self.agents_config["geospatial_analyst"],
            verbose=True,
            tools=all_tools,
            allow_delegation=False,
            respect_context_window=True,
        )

    # Primary OSINT tasks - Core intelligence gathering
    @task
    def company_profile_task(self) -> Task:
        """Collect comprehensive company profile intelligence."""
        return Task(
            config=self.tasks_config["company_profile_task"],
            agent=self.company_profile_analyst(),
            output_file="output/osint/company_profile.md",
        )

    @task
    def financial_task(self) -> Task:
        """Collect detailed financial intelligence."""
        return Task(
            config=self.tasks_config["financial_task"],
            agent=self.financial_analyst(),
            output_file="output/osint/financial_report.md",
        )

    @task
    def industry_innovation_task(self) -> Task:
        """Collect innovation and R&D intelligence."""
        return Task(
            config=self.tasks_config["industry_innovation_task"],
            agent=self.industry_innovation_analyst(),
            output_file="output/osint/industry_innovation_report.md",
        )

    @task
    def competitor_mapping_task(self) -> Task:
        """Map the competitive landscape with SWOT analysis."""
        return Task(
            config=self.tasks_config["competitor_mapping_task"],
            agent=self.competitor_mapping_analyst(),
            output_file="output/osint/competitor_mapping_report.md",
        )

    @task
    def social_media_sentiment_task(self) -> Task:
        """Analyze social media presence and sentiment."""
        return Task(
            config=self.tasks_config["social_media_sentiment_task"],
            agent=self.social_media_analyst(),
            output_file="output/osint/social_media_report.md",
        )

    @task
    def regulatory_overview_task(self) -> Task:
        """Analyze regulatory compliance and legal risks."""
        return Task(
            config=self.tasks_config["regulatory_overview_task"],
            agent=self.regulatory_analyst(),
            output_file="output/osint/regulatory_report.md",
        )

    @task
    def cyber_threat_snapshot_task(self) -> Task:
        """Assess cyber security posture and digital risks."""
        return Task(
            config=self.tasks_config["cyber_threat_snapshot_task"],
            agent=self.cyber_threat_analyst(),
            output_file="output/osint/cyber_threat_report.md",
        )

    @task
    def reporter_task(self) -> Task:
        """Generate a formatted report on the specified company."""
        return Task(
            config=self.tasks_config["reporter_task"],
            agent=self.reporting_analyst(),
            output_file="output/osint/reporter.md",
        )

    @task
    def validation_notes_task(self) -> Task:
        """Thoroughly examine each crew member's report for accuracy and completeness."""
        return Task(
            config=self.tasks_config["validation_notes"],
            agent=self.integration_analyst(),
            output_file="output/osint/validation_notes.md",
        )

    @task
    def unified_narrative_outline_task(self) -> Task:
        """Combine findings into a cohesive and comprehensive narrative."""
        return Task(
            config=self.tasks_config["unified_narrative_outline"],
            agent=self.integration_analyst(),
            output_file="output/osint/unified_narrative_outline.md",
        )

    @task
    def intelligence_gaps_task(self) -> Task:
        """Analyze synthesized data to identify remaining gaps in the investigation."""
        return Task(
            config=self.tasks_config["intelligence_gaps"],
            agent=self.integration_analyst(),
            output_file="output/osint/intelligence_gaps.md",
        )

    @task
    def cross_reference_report_task(self) -> Task:
        """Perform cross-referencing of all data points to ensure accuracy."""
        return Task(
            config=self.tasks_config["cross_reference_report"],
            agent=self.integration_analyst(),
            output_file="output/osint/cross_reference_report.md",
        )

    @task
    def risk_assessment_task(self) -> Task:
        """Evaluate gathered intelligence to assess potential risks."""
        return Task(
            config=self.tasks_config["risk_assessment"],
            agent=self.integration_analyst(),
            output_file="output/osint/risk_assessment.md",
        )

    @task
    def intelligence_report_task(self) -> Task:
        """Develop detailed intelligence report summarizing findings."""
        return Task(
            config=self.tasks_config["intelligence_report"],
            agent=self.integration_analyst(),
            output_file="output/osint/intelligence_report.md",
        )

    @task
    def client_presentation_report_task(self) -> Task:
        """Format intelligence report for clear and effective client presentation."""
        return Task(
            config=self.tasks_config["client_presentation_report"],
            agent=self.integration_analyst(),
            output_file="output/osint/client_presentation_report.md",
        )

    @task
    def final_qa_checklist_task(self) -> Task:
        """Perform final review of the report to ensure accuracy and completeness."""
        return Task(
            config=self.tasks_config["final_qa_checklist"],
            agent=self.integration_analyst(),
            output_file="output/osint/final_qa_checklist.md",
        )

    @task
    def executive_summary_task(self) -> Task:
        """Create concise executive summary of critical findings."""
        return Task(
            config=self.tasks_config["executive_summary"],
            agent=self.integration_analyst(),
            output_file="output/osint/executive_summary.md",
        )

    @task
    def debriefing_notes_task(self) -> Task:
        """Organize debriefing session with crew to review findings."""
        return Task(
            config=self.tasks_config["debriefing_notes"],
            agent=self.integration_analyst(),
            output_file="output/osint/debriefing_notes.md",
        )

    @task
    def delivery_confirmation_task(self) -> Task:
        """Utilize secure channels to deliver final report."""
        return Task(
            config=self.tasks_config["delivery_confirmation"],
            agent=self.integration_analyst(),
            output_file="output/osint/delivery_confirmation.md",
        )

    @task
    def company_core_info_task(self) -> Task:
        """Gather core information about the company."""
        return Task(
            config=self.tasks_config["company_core_info"],
            agent=self.company_profiler(),
            output_file="output/osint/company_core_info.md",
        )

    @task
    def company_history_task(self) -> Task:
        """Research and document company history."""
        return Task(
            config=self.tasks_config["company_history"],
            agent=self.company_profiler(),
            output_file="output/osint/company_history.md",
        )

    @task
    def company_financials_task(self) -> Task:
        """Analyze company financial statements."""
        return Task(
            config=self.tasks_config["company_financials"],
            agent=self.company_profiler(),
            output_file="output/osint/company_financials.md",
        )

    @task
    def company_market_position_task(self) -> Task:
        """Evaluate company market position and competitive landscape."""
        return Task(
            config=self.tasks_config["company_market_position"],
            agent=self.company_profiler(),
            output_file="output/osint/company_market_position.md",
        )

    @task
    def company_products_services_task(self) -> Task:
        """Document company products and services."""
        return Task(
            config=self.tasks_config["company_products_services"],
            agent=self.company_profiler(),
            output_file="output/osint/company_products_services.md",
        )

    @task
    def company_management_task(self) -> Task:
        """Research and analyze company management team."""
        return Task(
            config=self.tasks_config["company_management"],
            agent=self.company_profiler(),
            output_file="output/osint/company_management.md",
        )

    @task
    def company_legal_compliance_task(self) -> Task:
        """Document legal and regulatory issues faced by company."""
        return Task(
            config=self.tasks_config["company_legal_compliance"],
            agent=self.company_profiler(),
            output_file="output/osint/company_legal_compliance.md",
        )

    @task
    def company_public_perception_task(self) -> Task:
        """Assess company public perception and reputation."""
        return Task(
            config=self.tasks_config["company_public_perception"],
            agent=self.company_profiler(),
            output_file="output/osint/company_public_perception.md",
        )

    @task
    def financial_statements_review_task(self) -> Task:
        """Review financial statements of the company."""
        return Task(
            config=self.tasks_config["financial_statements_review"],
            agent=self.financial_analyst(),
            output_file="output/osint/financial_statements_review.md",
        )

    @task
    def financial_analysis_trends_task(self) -> Task:
        """Analyze financial trends of the company."""
        return Task(
            config=self.tasks_config["financial_analysis_trends"],
            agent=self.financial_analyst(),
            output_file="output/osint/financial_analysis_trends.html",
        )

    @task
    def financial_ratios_analysis_task(self) -> Task:
        """Calculate and analyze key financial ratios."""
        return Task(
            config=self.tasks_config["financial_ratios_analysis"],
            agent=self.financial_analyst(),
            output_file="output/osint/financial_ratios_analysis.html",
        )

    @task
    def cash_flow_analysis_task(self) -> Task:
        """Analyze cash flow statements of the company."""
        return Task(
            config=self.tasks_config["cash_flow_analysis"],
            agent=self.financial_analyst(),
            output_file="output/osint/cash_flow_analysis.html",
        )

    @task
    def debt_leverage_assessment_task(self) -> Task:
        """Assess debt and leverage of the company."""
        return Task(
            config=self.tasks_config["debt_leverage_assessment"],
            agent=self.financial_analyst(),
            output_file="output/osint/debt_leverage_assessment.html",
        )

    @task
    def online_news_and_press_analysis_task(self) -> Task:
        """Analyze online news and press coverage of the company."""
        return Task(
            config=self.tasks_config["online_news_and_press_analysis"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/online_news_analysis.html",
        )

    @task
    def domain_and_ip_analysis_task(self) -> Task:
        """Analyze domain and IP infrastructure of the company."""
        return Task(
            config=self.tasks_config["domain_and_ip_analysis"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/domain_ip_analysis.html",
        )

    @task
    def employee_and_executive_online_presence_task(self) -> Task:
        """Investigate online presence of key employees and executives."""
        return Task(
            config=self.tasks_config["employee_and_executive_online_presence"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/employee_executive_presence.html",
        )

    @task
    def review_and_forum_analysis_task(self) -> Task:
        """Analyze customer reviews and forum discussions about the company."""
        return Task(
            config=self.tasks_config["review_and_forum_analysis"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/review_forum_analysis.html",
        )

    @task
    def news_and_press_translation_analysis_task(self) -> Task:
        """Analyze translations of news articles and press releases."""
        return Task(
            config=self.tasks_config["news_and_press_translation_analysis"],
            agent=self.language_specialist(),
            output_file="output/osint/news_translation.html",
        )

    @task
    def customer_review_language_analysis_task(self) -> Task:
        """Analyze language used in customer reviews across multiple languages."""
        return Task(
            config=self.tasks_config["customer_review_language_analysis"],
            agent=self.language_specialist(),
            output_file="output/osint/customer_reviews_language.html",
        )

    @task
    def regulatory_compliance_assessment_task(self) -> Task:
        """Assess compliance with relevant industry regulations."""
        return Task(
            config=self.tasks_config["regulatory_compliance_assessment"],
            agent=self.legal_analyst(),
            output_file="output/osint/regulatory_compliance.html",
        )

    @task
    def litigation_and_legal_dispute_analysis_task(self) -> Task:
        """Analyze litigation history and current legal disputes."""
        return Task(
            config=self.tasks_config["litigation_and_legal_dispute_analysis"],
            agent=self.legal_analyst(),
            output_file="output/osint/legal_disputes.html",
        )

    @task
    def environmental_impact_assessment_task(self) -> Task:
        """Assess company's environmental impact using geospatial data."""
        return Task(
            config=self.tasks_config["environmental_impact_assessment"],
            agent=self.geospatial_analyst(),
            output_file="output/osint/environmental_impact.html",
        )

    # Additional task methods for web presence investigations
    @task
    def initial_website_analysis_task(self) -> Task:
        """Analyze the company website structure and technologies."""
        return Task(
            config=self.tasks_config["initial_website_analysis"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/initial_website_analysis.html",
        )

    @task
    def social_media_presence_mapping_task(self) -> Task:
        """Map the company's social media presence and activity."""
        return Task(
            config=self.tasks_config["social_media_presence_mapping"],
            agent=self.web_presence_investigator(),
            output_file="output/osint/social_media_mapping.html",
        )

    # HR Intelligence tasks
    @task
    def employee_sentiment_analysis_task(self) -> Task:
        """Analyze employee sentiment and satisfaction."""
        return Task(
            config=self.tasks_config["employee_sentiment_analysis"],
            agent=self.hr_intelligence_specialist(),
            output_file="output/osint/employee_sentiment.html",
        )

    @task
    def organizational_structure_analysis_task(self) -> Task:
        """Analyze the company's organizational structure."""
        return Task(
            config=self.tasks_config["organizational_structure_analysis"],
            agent=self.hr_intelligence_specialist(),
            output_file="output/osint/organizational_structure.html",
        )

    # Technical stack analysis tasks
    @task
    def website_technology_identification_task(self) -> Task:
        """Identify technologies used on the company website."""
        return Task(
            config=self.tasks_config["website_technology_identification"],
            agent=self.tech_stack_analyst(),
            output_file="output/osint/website_tech_stack.html",
        )

    @task
    def cloud_service_identification_task(self) -> Task:
        """Identify cloud services used by the company."""
        return Task(
            config=self.tasks_config["cloud_service_identification"],
            agent=self.tech_stack_analyst(),
            output_file="output/osint/cloud_services.html",
        )

    # Language and cultural analysis tasks
    @task
    def multilingual_website_analysis_task(self) -> Task:
        """Analyze the company's multilingual content."""
        return Task(
            config=self.tasks_config["multilingual_website_analysis"],
            agent=self.language_specialist(),
            output_file="output/osint/multilingual_website.html",
        )

    @task
    def cultural_sensitivity_assessment_task(self) -> Task:
        """Assess the company's cultural sensitivity in communications."""
        return Task(
            config=self.tasks_config["cultural_sensitivity_assessment"],
            agent=self.language_specialist(),
            output_file="output/osint/cultural_sensitivity.html",
        )

    # Legal analysis tasks
    @task
    def legal_entity_verification_task(self) -> Task:
        """Verify the company's legal entity status."""
        return Task(
            config=self.tasks_config["legal_entity_verification"],
            agent=self.legal_analyst(),
            output_file="output/osint/legal_entity_verification.html",
        )

    @task
    def intellectual_property_assessment_task(self) -> Task:
        """Assess the company's intellectual property portfolio."""
        return Task(
            config=self.tasks_config["intellectual_property_assessment"],
            agent=self.legal_analyst(),
            output_file="output/osint/ip_assessment.html",
        )

    # Geospatial analysis tasks
    @task
    def company_location_mapping_task(self) -> Task:
        """Map the company's physical locations."""
        return Task(
            config=self.tasks_config["company_location_mapping"],
            agent=self.geospatial_analyst(),
            output_file="output/osint/company_locations.html",
        )

    @task
    def market_area_analysis_task(self) -> Task:
        """Analyze the company's market area."""
        return Task(
            config=self.tasks_config["market_area_analysis"],
            agent=self.geospatial_analyst(),
            output_file="output/osint/market_area_analysis.html",
        )

    @task
    def final_report_task(self) -> Task:
        """Create the final comprehensive intelligence report."""
        return Task(
            config=self.tasks_config["final_report_task"],
            agent=self.reporting_analyst(),
            output_file="output/osint/final.html",
            context=[
                # Core intelligence tasks
                self.company_profile_task(),
                self.financial_task(),
                self.industry_innovation_task(),
                self.competitor_mapping_task(),
                self.social_media_sentiment_task(),
                self.regulatory_overview_task(),
                self.cyber_threat_snapshot_task(),
                # Company profiling tasks
                self.company_core_info_task(),
                self.company_history_task(),
                self.company_financials_task(),
                self.company_market_position_task(),
                self.company_products_services_task(),
                self.company_management_task(),
                self.company_legal_compliance_task(),
                self.company_public_perception_task(),
                # Financial analysis tasks
                self.financial_statements_review_task(),
                self.financial_analysis_trends_task(),
                self.financial_ratios_analysis_task(),
                self.cash_flow_analysis_task(),
                self.debt_leverage_assessment_task(),
                # Web presence tasks
                self.initial_website_analysis_task(),
                self.social_media_presence_mapping_task(),
                self.online_news_and_press_analysis_task(),
                self.domain_and_ip_analysis_task(),
                self.employee_and_executive_online_presence_task(),
                self.review_and_forum_analysis_task(),
                # HR intelligence tasks
                self.employee_sentiment_analysis_task(),
                self.organizational_structure_analysis_task(),
                # Technical analysis tasks
                self.website_technology_identification_task(),
                self.cloud_service_identification_task(),
                # Language and cultural analysis
                self.multilingual_website_analysis_task(),
                self.cultural_sensitivity_assessment_task(),
                self.news_and_press_translation_analysis_task(),
                self.customer_review_language_analysis_task(),
                # Legal analysis
                self.legal_entity_verification_task(),
                self.intellectual_property_assessment_task(),
                self.regulatory_compliance_assessment_task(),
                self.litigation_and_legal_dispute_analysis_task(),
                # Geospatial analysis
                self.company_location_mapping_task(),
                self.market_area_analysis_task(),
                self.environmental_impact_assessment_task(),
                # Integration analysis
                self.validation_notes_task(),
                self.cross_reference_report_task(),
                self.risk_assessment_task(),
                self.intelligence_report_task(),
                self.executive_summary_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the OSINT Intelligence Crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.hierarchical,
            manager_agent=self.chief_coordinator(),
            memory=False,
            cache=False,
        )
