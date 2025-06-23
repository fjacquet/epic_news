"""
Main orchestration module for the Epic News project.

This module defines and manages the primary workflow for processing user requests,
classifying them, and dispatching them to specialized crews (teams of AI agents)
for execution. It utilizes the `crewai.flow` paradigm to define a `ReceptionFlow`
class that orchestrates these steps.

Key functionalities include:
- Initializing necessary configurations and directories.
- Defining a default user request for testing or standalone execution.
- The `ReceptionFlow` class, which:
    - Extracts information from the user request.
    - Classifies the request to determine the appropriate crew.
    - Routes the request to specific handler methods that instantiate and run
      the corresponding crews (e.g., SalesProspectingCrew, CookingCrew, CompanyNewsCrew).
    - Manages the state of the operation, including input data and output files.
    - Handles the final step of sending an email report with the generated content.
- Utility functions to kickoff the flow (`kickoff`) and plot its structure (`plot`).
"""

import datetime
import os
import warnings

from crewai.flow import Flow, listen, or_, router, start
from dotenv import load_dotenv
from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211

from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_news.news_crew import CompanyNewsCrew
from epic_news.crews.company_profiler.company_profiler_crew import CompanyProfilerCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import CrossReferenceReportCrew
from epic_news.crews.fin_daily.fin_daily import FinDailyCrew
from epic_news.crews.geospatial_analysis.geospatial_analysis_crew import GeospatialAnalysisCrew
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.hr_intelligence.hr_intelligence_crew import HRIntelligenceCrew
from epic_news.crews.information_extraction.information_extraction_crew import InformationExtractionCrew
from epic_news.crews.legal_analysis.legal_analysis_crew import LegalAnalysisCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.marketing_writers.marketing_writers_crew import MarketingWritersCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.news_daily.news_daily import NewsDailyCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.post.post_crew import PostCrew
from epic_news.crews.rss_weekly.rss_weekly_crew import RssWeeklyCrew
from epic_news.crews.saint_daily.saint_daily import SaintDailyCrew
from epic_news.crews.sales_prospecting.sales_prospecting_crew import SalesProspectingCrew
from epic_news.crews.shopping_advisor.shopping_advisor import ShoppingAdvisorCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew
from epic_news.models.content_state import ContentState
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.utils.logger import get_logger

# Suppress the specific Pydantic deprecation warnings globally
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince211)
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

# Suppress specific Pydantic deprecation warnings by message content
warnings.filterwarnings("ignore", message=".*`max_items` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*`min_items` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

load_dotenv()

"""                                                                                      """
"""                     All the magic is here                                            """
"""                                                                                      """


# Default user request for demonstration, testing, or standalone execution.
# This can be dynamically set or replaced in a production environment.
class ReceptionFlow(Flow[ContentState]):
    """
    Manages the end-to-end process of receiving a user request,
    classifying it, dispatching it to the appropriate AI crew,
    and handling the output (e.g., sending an email report).

    This flow is built using the `crewai.flow` library, defining
    a sequence of states and transitions based on listeners and routers.
    The `ContentState` model is used to maintain and pass data
    throughout the flow.
    """

    def __init__(self, user_request: str):
        super().__init__()
        self._user_request = user_request
        self.logger = get_logger(__name__)

    @start()
    def feed_user_request(self):
        """
        Initializes the flow with the user's request.

        This is the entry point of the flow. It sets the initial user request
        in the flow's state and resets the `email_sent` flag to ensure an email
        is sent for each new flow execution.
        """
        # Reset the email_sent flag to ensure an email is sent for each new flow execution.
        ensure_output_directories()

        self.state.email_sent = False
        self.state.user_request = self._user_request
        # return "feed_user_request" # Implicitly returns the method name as the next step

    @listen("feed_user_request")
    def extract_info(self):
        """
        Extracts structured information from the raw user request.

        Utilizes the `InformationExtractionCrew` to parse the user's query
        and populate the `extracted_info` field in the flow's state.
        This structured information is then used for classification and
        as input for other crews.
        """
        print("🤖 Kicking off Information Extraction Crew...")
        # Instantiate and run the information extraction crew
        extraction_crew = InformationExtractionCrew()
        extracted_data = extraction_crew.crew().kickoff(inputs={"user_request": self.state.user_request})

        # Update the state with the extracted information
        if extracted_data:
            # Assuming extracted_data has a .pydantic attribute for the model instance
            self.state.extracted_info = extracted_data.pydantic
            print("✅ Information extraction complete.")
        else:
            print("⚠️ Information extraction failed or returned no data.")
        # return "extract_info" # Implicitly returns the method name as the next step

    @listen("extract_info")
    def classify(self):
        """
        Classifies the user request into a predefined category.

        Uses the `ClassifyCrew` and the extracted information (primarily the topic)
        to determine which specialized crew should handle the request.
        The result updates `self.state.selected_crew`, and the classification
        decision is saved to `output/classify/decision.md`.
        """
        topic = (
            self.state.extracted_info.main_subject_or_activity
            if self.state.extracted_info and hasattr(self.state.extracted_info, "main_subject_or_activity")
            else "Unknown Topic"  # Provide a default if topic extraction failed or info is missing
        )
        print(f"Routing request: '{self.state.user_request}' with topic: '{topic}'")
        # Define the output file path for the classification decision.
        self.state.output_file = "output/classify/decision.md"

        # Prepare input data for classification using the centralized method from ContentState.
        inputs = self.state.to_crew_inputs()

        # Instantiate and run the classification crew
        classify_crew = ClassifyCrew()
        classification_result = classify_crew.crew().kickoff(inputs=inputs)

        # Parse the result and update the state with the selected crew category.
        # The classification_result might contain 'Thought: ...' prefixes.
        # We need to extract the actual category name.
        raw_classification = str(classification_result)  # Ensure it's a string
        parsed_category = "UNKNOWN"  # Default to UNKNOWN
        for category_key in self.state.categories:
            if category_key in raw_classification:
                parsed_category = category_key
                break

        self.state.selected_crew = parsed_category
        print(
            f"✅ Classification complete. Raw: '{raw_classification}', Selected crew: {self.state.selected_crew}"
        )
        # return "classify" # Implicitly returns the method name as the next step

    @router("classify")
    def determine_crew(self):
        """
        Routes the flow to the appropriate crew handler based on classification.

        This router inspects `self.state.selected_crew` (determined by the
        `classify` step) and returns the name of the next flow step/method
        to execute (e.g., 'go_generate_sales_prospecting_report').
        If the crew type is not recognized, it defaults to 'go_unknown'.
        """
        if self.state.selected_crew == "HOLIDAY_PLANNER":
            return "go_generate_holiday_plan"
        if self.state.selected_crew == "MEETING_PREP":
            return "go_generate_meeting_prep"
        if self.state.selected_crew == "LIBRARY":
            return "go_generate_book_summary"
        if self.state.selected_crew == "COOKING":
            return "go_generate_recipe"
        if self.state.selected_crew == "SHOPPING":
            return "go_generate_shopping_advice"
        if self.state.selected_crew == "POEM":
            return "go_generate_poem"
        if self.state.selected_crew == "NEWSCOMPANY":
            return "go_generate_news_company"
        if self.state.selected_crew == "OPEN_SOURCE_INTELLIGENCE":
            return "go_generate_osint"
        if self.state.selected_crew == "MARKETING_WRITERS":
            return "go_generate_marketing_content"
        if self.state.selected_crew == "RSS":
            return "go_generate_rss_weekly"
        if self.state.selected_crew == "FINDAILY":
            return "go_generate_findaily"
        if self.state.selected_crew == "NEWSDAILY":
            return "go_generate_news_daily"
        if self.state.selected_crew == "SAINT":
            return "go_generate_saint_daily"
        if self.state.selected_crew == "SALES_PROSPECTING":
            return "go_generate_sales_prospecting_report"
        # Fallback for unhandled or unknown crew types.
        # Consider logging this event for monitoring.
        print(f"⚠️ Unknown crew type: {self.state.selected_crew}. Routing to 'go_unknown'.")
        return "go_unknown"

    @listen("go_unknown")
    def end_unknown(self):
        """
        Handles cases where the request classification is 'unknown' or routing fails.

        This method is a fallback for unhandled crew types. It sets a generic
        error message as the `final_report` and writes this message to the
        `output_file` (which might be `output/classify/decision.md` if classification failed early,
        or a default if not set by a prior step).
        """
        print("⚠️ Unknown crew type selected or error in routing.")
        self.state.final_report = "Error: Unknown crew type or routing issue. Unable to process the request."
        # Ensure output_file is set, even if to a default, before writing.
        if not self.state.output_file:
            self.state.output_file = "output/unknown_request_error.md"
            print(f"Output file not set, defaulting to {self.state.output_file}")
        # return "go_unknown" # Implicitly returns method name

    @listen("go_generate_poem")
    def generate_poem(self):
        """
        Handles requests classified for the 'PoemCrew'.

        Invokes the `PoemCrew` to generate a poem based on the provided topic.
        Sets `output_file` to `output/poem/poem.html` and stores the generated
        poem in `self.state.poem`.
        """
        self.state.output_file = "output/poem/poem.html"
        print(f"Generating poem about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the poem
        self.state.poem = PoemCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_poem"

    @listen("go_generate_news_company")
    def generate_news_company(self):
        """
        Handles requests classified for the 'CompanyNewsCrew'.

        Invokes the `CompanyNewsCrew` to generate news content related to the given topic.
        Sets `output_file` to `output/news/report.html` and stores the news report
        in `self.state.news_report`.
        """
        self.state.output_file = "output/news/report.html"
        print(f"Generating news about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the news
        self.state.news_report = CompanyNewsCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_news_company"

    @listen("go_generate_rss_weekly")
    def generate_rss_weekly(self):
        """
        Handles requests classified for the 'RssWeeklyCrew'.

        Invokes the `RssWeeklyCrew` to generate a weekly news summary from RSS feeds.
        Sets `output_file` to `output/rss_weekly/report.html` and stores the report
        in `self.state.rss_weekly_report`.
        """
        self.state.output_file = "output/rss_weekly/report.html"
        print("📰 Generating RSS weekly report...")

        # Prepare inputs for the crew, including the OPML file path
        inputs = self.state.to_crew_inputs()
        opml_file = "src/epic_news/crews/rss_weekly/data/feedly.opml"
        inputs["opml_file_path"] = os.path.abspath(opml_file)

        # Kick off the crew
        report_content = RssWeeklyCrew().crew().kickoff(inputs=inputs)
        self.state.rss_weekly_report = report_content

    @listen("go_generate_findaily")
    def generate_findaily(self):
        """
        Handles requests classified for the 'FinDailyCrew'.

        Invokes the `FinDailyCrew` to generate a daily financial analysis report
        including stock portfolio analysis, crypto portfolio analysis, and new
        investment suggestions. Sets `output_file` to `output/findaily/report.html`
        and stores the report in `self.state.fin_daily_report`.
        """
        self.state.output_file = "output/findaily/report.html"
        print("💰 Generating daily financial analysis report...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        stock_csv_file = "data/stock.csv"
        inputs["stock_csv_path"] = os.path.abspath(stock_csv_file)
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")

        # Kick off the crew
        report_content = FinDailyCrew().crew().kickoff(inputs=inputs)
        self.state.fin_daily_report = report_content

    @listen("go_generate_news_daily")
    def generate_news_daily(self):
        """
        Handles requests classified for the 'NewsDailyCrew'.

        Invokes the `NewsDailyCrew` to generate a daily news report in French
        covering top 10 news items for Suisse Romande, Suisse, France, Europe,
        World, Wars, and Economy. Sets `output_file` to `output/news_daily/final_report.html`
        and stores the report in `self.state.news_daily_report`.
        """
        self.state.output_file = "output/news_daily/final_report.html"
        print("📰 Generating daily news report in French...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        inputs["report_language"] = "French"

        # Kick off the crew
        report_content = NewsDailyCrew().crew().kickoff(inputs=inputs)
        self.state.news_daily_report = report_content

    @listen("go_generate_saint_daily")
    def generate_saint_daily(self):
        """
        Handles requests classified for the 'SaintDailyCrew'.

        Invokes the `SaintDailyCrew` to generate a daily saint report in French
        covering the saint of the day in Switzerland, including biography,
        significance, and connection to Swiss Catholic traditions.
        Sets `output_file` to `output/saint_daily/report.html`
        and stores the report in `self.state.saint_daily_report`.
        """
        self.state.output_file = "output/saint_daily/report.html"
        print("⛪ Generating daily saint report in French...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        inputs["report_language"] = "French"
        inputs["target_country"] = "Switzerland"

        # Kick off the crew
        report_content = SaintDailyCrew().crew().kickoff(inputs=inputs)
        self.state.saint_daily_report = report_content

    @listen("go_generate_recipe")
    def generate_recipe(self):
        """
        Handles requests classified for the 'CookingCrew'.

        Invokes the `CookingCrew` to generate a recipe. It sets the main output
        to `output/cooking/recipe.html` and an attachment (e.g., for Paprika app)
        to `output/cooking/recipe.yaml`. The result is stored in
        `self.state.recipe`.
        """
        # Ensure output directory exists
        os.makedirs("output/cooking", exist_ok=True)

        # Set output files
        self.state.output_file = "output/cooking/recipe.html"
        self.state.attachment_file = "output/cooking/recipe.yaml"

        # Get the topic and preferences from the user's request or extracted info
        topic = self.state.user_request or ""

        if self.state.extracted_info:
            if (
                hasattr(self.state.extracted_info, "main_subject_or_activity")
                and self.state.extracted_info.main_subject_or_activity
            ):
                topic = self.state.extracted_info.main_subject_or_activity
            if (
                hasattr(self.state.extracted_info, "user_preferences_and_constraints")
                and self.state.extracted_info.user_preferences_and_constraints
            ):
                preferences = self.state.extracted_info.user_preferences_and_constraints

        # Enhance the topic with preferences if available
        if preferences and preferences.lower() not in topic.lower():
            topic = f"{topic} ({preferences})"

        print(f"🍳 Generating recipe for: {topic}")

        # Generate the recipe with the specific topic and preferences
        crew_inputs = self.state.to_crew_inputs()

        # Add topic and preferences to crew inputs instead of constructor
        crew_inputs["topic"] = topic
        if preferences:
            crew_inputs["preferences"] = preferences

        # Create crew using context-driven approach (no constructor parameters)
        crew = CookingCrew().crew()

        # Kick off the crew with inputs
        self.state.recipe = crew.kickoff(inputs=crew_inputs)
        print("✅ Recipe generation complete")
        # return "generate_recipe"

    @listen("go_generate_book_summary")
    def generate_book_summary(self):
        """
        Handles requests classified for the 'LibraryCrew'.

        Invokes the `LibraryCrew` to generate a book summary. Sets the main output
        to `output/library/book_summary.html` and an attachment for research results
        to `output/library/research_results.md`. The summary is stored in
        `self.state.book_summary`.
        """
        self.state.output_file = "output/library/book_summary.html"
        self.state.attachment_file = "output/library/research_results.md"
        print(f"Generating book summary for: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the book summary
        self.state.book_summary = LibraryCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_book_summary"

    @listen("go_generate_shopping_advice")
    def generate_shopping_advice(self):
        """
        Handles requests classified for the 'ShoppingAdvisorCrew'.

        Invokes the `ShoppingAdvisorCrew` to generate comprehensive shopping advice
        including product research, price comparison between Switzerland and France,
        competitor analysis, and actionable recommendations. Sets `output_file` to
        `output/shopping_advisor/shopping_advice.html` and stores the report in
        `self.state.shopping_advice_report`.
        """
        # Ensure output directory exists
        os.makedirs("output/shopping_advisor", exist_ok=True)

        # Set output file
        self.state.output_file = "output/shopping_advisor/shopping_advice.html"

        print(f"🛒 Generating shopping advice for: {self.state.user_request}")

        # Debug: Show what inputs are being passed to the crew
        crew_inputs = self.state.to_crew_inputs()
        print(f"🔍 DEBUG - Crew inputs: {crew_inputs}")
        print(f"🔍 DEBUG - Topic: {crew_inputs.get('topic', 'NOT_FOUND')}")
        print(f"🔍 DEBUG - Objective: {crew_inputs.get('objective', 'NOT_FOUND')}")

        # Generate the shopping advice using CrewAI context-driven approach
        self.state.shopping_advice_report = ShoppingAdvisorCrew().crew().kickoff(inputs=crew_inputs)
        print("✅ Shopping advice generation complete")

    @listen("go_generate_meeting_prep")
    def generate_meeting_prep(self):
        """
        Handles requests classified for the 'MeetingPrepCrew'.

        Invokes `MeetingPrepCrew` to generate meeting preparation materials.
        It expects a 'company' name in the inputs, falling back to 'topic' if
        'company' is not available. Sets `output_file` to
        `output/meeting/meeting_preparation.html` and stores the report in
        `self.state.meeting_prep_report`.
        """
        self.state.output_file = "output/meeting/meeting_preparation.html"
        # Prepare inputs and handle company fallback
        current_inputs = self.state.to_crew_inputs()
        company = current_inputs.get("company")
        if not company:
            company = current_inputs.get("topic")  # Fallback to topic if company is not specified
            current_inputs["company"] = company  # Ensure 'company' key is in inputs for the crew
            print(f"⚠️ No company specified for meeting prep, using topic as company: {company}")

        print(f"Generating meeting prep for company: {company or 'N/A'}")

        # Generate the meeting prep
        self.state.meeting_prep_report = MeetingPrepCrew().crew().kickoff(inputs=current_inputs)
        # return "generate_meeting_prep"

    @listen("go_generate_sales_prospecting_report")
    def generate_sales_prospecting_report(self):
        """
        Handles requests classified for the 'SalesProspectingCrew'.

        Invokes the `SalesProspectingCrew` to generate a sales prospecting report,
        including contact information and an approach strategy. Sets `output_file`
        to `output/sales_prospecting/approach_strategy.html` and stores the report
        in `self.state.contact_info_report`.
        """
        self.state.output_file = "output/sales_prospecting/approach_strategy.html"
        company = self.state.to_crew_inputs().get("target_company")  # Expects 'target_company' from inputs
        our_product = self.state.to_crew_inputs().get(
            "our_product", "our product/service"
        )  # Default if not specified
        print(f"Generating sales prospecting report for: {company or 'N/A'} regarding {our_product}")

        self.state.contact_info_report = (
            SalesProspectingCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_contact_info" # Original comment, implies this was a rename/refactor

    @listen("go_generate_osint")
    def generate_osint(self):
        """
        Handles requests classified for the 'OPEN_SOURCE_INTELLIGENCE' (OSINT) crew.

        Invokes the `OSINTCrew` to gather open-source intelligence based on the topic.
        Sets `output_file` to `output/osint/global_report.html` and stores the report
        in `self.state.osint_report`. This is often part of a parallel data gathering process.
        """
        self.state.output_file = "output/osint/global_report.html"
        print(f"Generating OSINT report for: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # return "generate_osint"

    @listen("generate_osint")
    def generate_company_profile(self):
        """
        Generates a company profile based on the company name.

        This method is part of the OSINT process, focusing on gathering information
        about a company. It sets `output_file` to `output/osint/company_profile.html`
        and stores the profile in `self.state.company_profile`.
        """
        self.state.output_file = "output/osint/company_profile.html"
        print(
            f"Generating company profile for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        # Get company name from state inputs

        self.state.company_profile = CompanyProfilerCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_tech_stack(self):
        """
        Generates a tech stack report for the company.

        This method is part of the OSINT process, focusing on identifying the
        technologies used by a company. It sets `output_file` to `output/osint/tech_stack.html`
        and stores the report in `self.state.tech_stack`.
        """
        self.state.output_file = "output/osint/tech_stack.html"
        print(
            f"Generating Tech Stack for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        # Get company name from state inputs
        self.state.tech_stack = TechStackCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_web_presence(self):
        """
        Generates a web presence report for the company.

        This method is part of the OSINT process, focusing on analyzing the
        company's online presence. It sets `output_file` to `output/osint/web_presence.html`
        and stores the report in `self.state.web_presence_report`.
        """
        self.state.output_file = "output/osint/web_presence.html"
        print(
            f"Generating Web Presence for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        self.state.web_presence_report = WebPresenceCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_hr_intelligence(self):
        """
        Generates an HR intelligence report for the company.

        This method is part of the OSINT process, focusing on gathering information
        about the company's human resources. It sets `output_file` to `output/osint/hr_intelligence.html`
        and stores the report in `self.state.hr_intelligence_report`.
        """
        self.state.output_file = "output/osint/hr_intelligence.html"
        print(
            f"Generating HR Intelligence for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        self.state.hr_intelligence_report = (
            HRIntelligenceCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_legal_analysis(self):
        """
        Generates a legal analysis report for the company.

        This method is part of the OSINT process, focusing on analyzing the
        company's legal aspects. It sets `output_file` to `output/osint/legal_analysis.html`
        and stores the report in `self.state.legal_analysis_report`.
        """
        self.state.output_file = "output/osint/legal_analysis.html"
        print(
            f"Generating Legal Analysis for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        self.state.legal_analysis_report = (
            LegalAnalysisCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_geospatial_analysis(self):
        """
        Generates a geospatial analysis report for the company.

        This method is part of the OSINT process, focusing on analyzing the
        company's geospatial aspects. It sets `output_file` to `output/osint/geospatial_analysis.html`
        and stores the report in `self.state.geospatial_analysis`.
        """
        self.state.output_file = "output/osint/geospatial_analysis.html"
        print(
            f"Generating Geospatial Analysis for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        self.state.geospatial_analysis = (
            GeospatialAnalysisCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_company_profile"

    @listen("generate_osint")
    def generate_cross_reference_report(self):
        """
        Generates a cross-reference report based on the company name.

        This method is part of the OSINT process, focusing on generating a
        comprehensive report by cross-referencing various data points.
        It sets `output_file` to `output/osint/global_report.html` and stores
        the report in `self.state.cross_reference_report`.
        """
        self.state.output_file = "output/osint/global_report.html"
        print(
            f"Generating Cross Reference Report for: {self.state.to_crew_inputs().get('company') or self.state.to_crew_inputs().get('topic', 'N/A')}"
        )

        self.state.cross_reference_report = (
            CrossReferenceReportCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_company_profile"

    @listen("go_generate_holiday_plan")
    def generate_holiday_plan(self):
        """
        Handles requests classified for the 'HolidayPlannerCrew'.

        Invokes the `HolidayPlannerCrew` to generate a holiday itinerary.
        Requires a 'destination' in the inputs. Sets `output_file` to
        `output/travel_guides/itinerary.html` and stores the plan in
        `self.state.holiday_plan`. Returns 'error' if no destination is found.
        """
        self.state.output_file = "output/travel_guides/itinerary.html"
        current_inputs = self.state.to_crew_inputs()

        if not current_inputs.get("destination"):
            print("⚠️ No destination found for holiday plan. Aborting and routing to error.")
            # TODO: Define an actual 'error' step or handle this more gracefully.
            return "error"  # Or another appropriate error state like 'go_unknown'

        print(f"Starting HolidayPlannerCrew with inputs: {current_inputs}")

        # Run the crew
        self.state.holiday_plan = HolidayPlannerCrew().crew().kickoff(inputs=current_inputs)
        return "generate_holiday_plan"

    @listen("go_generate_marketing_content")
    def generate_marketing_content(self):
        """
        Handles requests classified for the 'MarketingWritersCrew'.

        Invokes `MarketingWritersCrew` to generate enhanced marketing content,
        typically in French, based on an original message or topic. Sets `output_file`
        to `output/marketing/enhanced_message.html` and stores the report in
        `self.state.marketing_report`.
        """
        self.state.output_file = "output/marketing/enhanced_message.html"
        print(f"Generating marketing content for topic: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Create and kickoff the marketing writers crew
        self.state.marketing_report = (
            MarketingWritersCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        )
        # return "generate_marketing_content"

    @listen(
        or_(
            "generate_poem",
            "generate_news_company",
            "generate_recipe",
            "generate_book_summary",
            "generate_shopping_advice",
            "generate_meeting_prep",
            "generate_sales_prospecting_report",
            "generate_osint",
            "generate_cross_reference_report",
            "generate_holiday_plan",
            "generate_marketing_content",
            "generate_rss_weekly",
            "generate_findaily",
            "generate_news_daily",
            "generate_saint_daily",
        )
    )
    def join(self, *results):
        """
        Synchronizes the flow after a crew has finished its primary task.

        Its primary role is to consolidate the final report into the
        designated output file using `_write_output_to_file()` before proceeding
        to the email sending step.
        """
        self.logger.info("Join step reached. Writing output to file before sending email.")
        self._write_output_to_file()

    def _get_final_report_content(self) -> str | None:
        """
        Retrieves the final report content from the application state.

        It iterates through a predefined list of report attributes in `self.state`
        and returns the content of the first one that is not None. This ensures
        that the output from whichever crew was run is correctly identified.

        Returns:
            The content of the final report as a string, or None if no report
            is found.
        """
        report_attributes = [
            "shopping_advice_report",
            "news_report",
            "recipe",
            "book_summary",
            "poem",
            "holiday_plan",
            "marketing_report",
            "meeting_prep_report",
            "contact_info_report",
            "cross_reference_report",
            "fin_daily_report",
            "rss_weekly_report",
            "post_report",
            "location_report",
            "osint_report",
            "company_profile",
            "tech_stack_report",
            "web_presence_report",
            "hr_intelligence_report",
            "legal_analysis_report",
            "geospatial_analysis",
            "lead_score_report",
            "tech_stack",
            "final_report",
            "news_daily_report",
            "saint_daily_report",
        ]

        for attr in report_attributes:
            content = getattr(self.state, attr, None)
            if content:
                self.logger.info(f"Found final report content in 'self.state.{attr}'")
                return str(content)

        self.logger.warning("No final report content found in any of the expected state attributes.")
        return None

    def _write_output_to_file(self):
        """
        Writes the final report content to the specified output file.

        This method retrieves the report content using `_get_final_report_content()`
        and writes it to the path stored in `self.state.output_file`. It handles
        directory creation and ensures the content is written with UTF-8 encoding.
        """
        final_content = self._get_final_report_content()
        output_file = self.state.output_file

        if not output_file:
            self.logger.warning("No output file path set in state. Skipping file write.")
            return

        if final_content:
            try:
                output_dir = os.path.dirname(output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    self.logger.info(f"Created output directory: {output_dir}")

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(final_content)
                self.logger.info(f"Successfully wrote final report to {output_file}")

            except Exception as e:
                self.logger.error(f"Error writing final report to {output_file}: {e}")
        else:
            self.logger.warning(f"No final content to write to {output_file}.")

    @listen(or_("generate_cross_reference_report", "join"))
    def send_email(self):
        """
        Sends the generated report via email after specific crew completions or general join.

        This method listens to the completion of 'generate_cross_reference_report'
        or the general 'join' event (indicating completion of other main content-generating crews).
        It ensures an email is sent only once per flow execution by checking `self.state.email_sent`.

        It constructs email parameters (recipient, subject, body, attachment) using
        information from `self.state`. The main report from `self.state.output_file`
        is typically attached. If `self.state.attachment_file` is set (e.g., for
        recipes with specific formats), that file is used as the attachment instead.
        The `PostCrew` is then invoked to handle the actual email dispatch.
        """
        if not self.state.email_sent:
            print("📬 Preparing to send email...")
            # Prepare email inputs
            subject_topic = (
                self.state.extracted_info.main_subject_or_activity
                if self.state.extracted_info
                and hasattr(self.state.extracted_info, "main_subject_or_activity")
                else "Your Report"
            )
            email_body_content = getattr(
                self.state,
                "final_report",
                "Please find your report attached or view content above if no attachment was generated.",
            )

            email_inputs = {
                "recipient_email": os.environ.get("MAIL"),  # Fetched from environment variable
                "subject": f"Your Epic News Report: {subject_topic}",
                "body": str(email_body_content),  # Ensure body is string
                "output_file": self.state.output_file or "",
                "topic": subject_topic,
            }

            # Determine attachment: specific attachment_file takes precedence over output_file
            attachment_to_send = None
            if (
                hasattr(self.state, "attachment_file")
                and self.state.attachment_file
                and os.path.exists(self.state.attachment_file)
            ):
                attachment_to_send = self.state.attachment_file
                print(f"Using specific attachment: {attachment_to_send}")
            elif self.state.output_file and os.path.exists(self.state.output_file):
                attachment_to_send = self.state.output_file
                print(f"Using main output file as attachment: {attachment_to_send}")
            else:
                print(
                    "⚠️ No valid attachment file found (neither specific attachment_file nor output_file exists or is set). Email will be sent without attachment."
                )

            # Always include attachment_path, even if empty, to satisfy PostCrew's task template
            email_inputs["attachment_path"] = attachment_to_send if attachment_to_send else ""

            # Instantiate and kickoff the PostCrew
            try:
                post_crew = PostCrew()
                email_result = post_crew.crew().kickoff(inputs=email_inputs)
                print(f"📧 Email sending process initiated. Result: {email_result}")
                self.state.email_sent = True  # Mark email as sent to prevent duplicates
            except Exception as e:
                print(f"❌ Error during email sending: {e}")
        else:
            print("📧 Email already sent for this request. Skipping.")
        # return "send_email" # Implicitly returns method name


def kickoff(user_input: str | None = None):
    """
    Initializes and runs the ReceptionFlow.

    This function serves as the main entry point for executing the entire
    crew orchestration process. It instantiates the `ReceptionFlow` and
    invokes its `run()` method to start the sequence of tasks.
    It can optionally take a user_input string to override the default.

    Returns:
        The completed ReceptionFlow object.
    """
    # If user_input is not provided, use a default value.
    request = user_input if user_input else "Qui est le saint du jour ?"

    reception_flow = ReceptionFlow(user_request=request)
    reception_flow.kickoff()
    return reception_flow


def plot(output_path: str = "flow.png"):
    """
    Generates a visual plot of the `ReceptionFlow`.

    This utility function creates an instance of `ReceptionFlow` and calls its
    `plot` method to generate a diagram representing the flow's structure
    (states and transitions). The diagram is saved to the specified `output_path`.

    Args:
        output_path: The file path where the flow diagram will be saved.
                     Defaults to "flow.png".
    """
    flow = ReceptionFlow(user_request="dummy request for plotting")
    flow.plot()


if __name__ == "__main__":
    # To run the flow, execute this script from the command line:
    # python -m src.epic_news.main
    # You can also pass a custom request:
    # python -m src.epic_news.main "Your custom request here"
    #
    # 📋 For a complete list of supported use cases and example prompts,
    # see USE_CASES.md in the project root directory.
    # Examples: "Analyze my portfolio", "Recipe for cookies", "News about AI"
    kickoff()

    # To generate a plot of the flow, uncomment the following line:
    # plot()
