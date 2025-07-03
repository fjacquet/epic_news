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
import json
import os
import re
import warnings
from pathlib import Path

from crewai.flow import Flow, listen, or_, router, start
from dotenv import load_dotenv
from pydantic import PydanticDeprecatedSince20, PydanticDeprecatedSince211

from epic_news.bin.fetch_rss_articles import fetch_articles_from_opml
from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_news.company_news_crew import CompanyNewsCrew
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
from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew
from epic_news.crews.news_daily.news_daily import NewsDailyCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.rss_weekly.rss_weekly_crew import RssWeeklyCrew
from epic_news.crews.saint_daily.saint_daily import SaintDailyCrew
from epic_news.crews.sales_prospecting.sales_prospecting_crew import SalesProspectingCrew
from epic_news.crews.shopping_advisor.shopping_advisor import ShoppingAdvisorCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew
from epic_news.models.book_summary_report import BookSummaryReport
from epic_news.models.content_state import ContentState
from epic_news.models.financial_report import FinancialReport
from epic_news.models.meeting_prep_report import MeetingPrepReport
from epic_news.models.paprika_recipe import PaprikaRecipe
from epic_news.models.poem_models import PoemJSONOutput
from epic_news.models.saint_data import SaintData
from epic_news.utils.debug_utils import (
    dump_crewai_state,
    parse_crewai_output,
)
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.utils.html.book_summary_html_factory import (
    book_summary_to_html,
)
from epic_news.utils.html.company_news_html_factory import company_news_to_html
from epic_news.utils.html.daily_news_html_factory import daily_news_to_html
from epic_news.utils.html.fin_daily_html_factory import findaily_to_html
from epic_news.utils.html.holiday_plan_html_factory import holiday_plan_to_html
from epic_news.utils.html.meeting_prep_html_factory import meeting_prep_to_html
from epic_news.utils.html.poem_html_factory import poem_to_html
from epic_news.utils.html.recipe_html_factory import recipe_to_html
from epic_news.utils.html.saint_html_factory import saint_to_html
from epic_news.utils.html.shopping_advice_html_factory import shopping_advice_to_html
from epic_news.utils.logger import get_logger
from epic_news.utils.menu_generator import MenuGenerator
from epic_news.utils.observability import get_observability_tools, trace_task
from epic_news.utils.report_utils import (
    generate_rss_weekly_html_report,
)
from epic_news.utils.string_utils import create_topic_slug

# Import function explicitly to ensure availability during runtime

# Suppress the specific Pydantic deprecation warnings globally
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince211)
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)

# Suppress specific Pydantic deprecation warnings by message content
warnings.filterwarnings("ignore", message=".*`max_items` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*`min_items` is deprecated.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

load_dotenv()

# Initialize observability tools at the module level
observability_tools = get_observability_tools(crew_name="reception_flow")
tracer = observability_tools["tracer"]
dashboard = observability_tools["dashboard"]
hallucination_guard = observability_tools["hallucination_guard"]

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
        self.tracer = tracer
        self.dashboard = dashboard
        self.hallucination_guard = hallucination_guard

    @start()
    @trace_task(tracer)
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
    @trace_task(tracer)
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

        dump_crewai_state(extracted_data, "EXTRACTED_INFO")
        # Update the state with the extracted information
        if extracted_data:
            # Assuming extracted_data has a .pydantic attribute for the model instance
            self.state.extracted_info = extracted_data.pydantic
            print("✅ Information extraction complete.")
        else:
            print("⚠️ Information extraction failed or returned no data.")
        # return "extract_info" # Implicitly returns the method name as the next step

    @listen("extract_info")
    @trace_task(tracer)
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
        dump_crewai_state(classification_result, "CLASSIFICATION")

        # Parse the result and update the state with the selected crew category.
        # The classification_result might contain 'Thought: ...' prefixes.
        # We need to extract the actual category name that appears first in the response.
        raw_classification = str(classification_result)  # Ensure it's a string
        parsed_category = "UNKNOWN"  # Default to UNKNOWN

        # Find the first occurrence of any category in the response
        earliest_position = len(raw_classification)
        for category_key in self.state.categories:
            position = raw_classification.find(category_key)
            if position != -1 and position < earliest_position:
                earliest_position = position
                parsed_category = category_key

        self.state.selected_crew = parsed_category
        print(
            f"✅ Classification complete. Raw: '{raw_classification}', Selected crew: {self.state.selected_crew}"
        )
        # return "classify" # Implicitly returns the method name as the next step

    @router("classify")
    @trace_task(tracer)
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
        if self.state.selected_crew == "BOOK_SUMMARY":
            return "go_generate_book_summary"
        if self.state.selected_crew == "COOKING":
            return "go_generate_recipe"
        if self.state.selected_crew == "MENU":
            return "go_generate_menu_designer"
        if self.state.selected_crew == "SHOPPING":
            return "go_generate_shopping_advice"
        if self.state.selected_crew == "POEM":
            return "go_generate_poem"
        if self.state.selected_crew == "COMPANY_NEWS":
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
    @trace_task(tracer)
    def end_unknown(self):
        """
        Handles cases where the request classification is 'unknown' or routing fails.

        This method is a fallback for unhandled crew types. It sets a generic
        error message as the `final_report` and writes this message to the
        `output_file` (which might be `output/classify/decision.md` if classification failed early,
        or a default if not set by a prior step).
        """
        print("⚠�� Unknown crew type selected or error in routing.")
        self.state.final_report = "Error: Unknown crew type or routing issue. Unable to process the request."
        # Ensure output_file is set, even if to a default, before writing.
        if not self.state.output_file:
            self.state.output_file = "output/unknown_request_error.md"
            print(f"Output file not set, defaulting to {self.state.output_file}")
        # return "go_unknown" # Implicitly returns method name

    @listen("go_generate_poem")
    @trace_task(tracer)
    def generate_poem(self):
        """
        Handles requests classified for the 'PoemCrew'.

        Invokes the `PoemCrew` to generate a poem based on the provided topic.
        Sets `output_file` to `output/poem/poem.html` and stores the generated
        poem in `self.state.poem`.
        """
        self.state.output_file = "output/poem/poem.json"
        print(f"Generating poem about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the poem
        output = PoemCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        dump_crewai_state(output, "POEM")

        html_file = "output/poem/poem.html"
        # Parse CrewOutput to PoemJSONOutput
        if hasattr(output, "output") and isinstance(output.output, PoemJSONOutput):
            poem_model = output.output
        else:
            poem_model = PoemJSONOutput.model_validate(json.loads(output.raw))
        poem_to_html(poem_model, html_file=html_file)

        # return "generate_poem"

    @listen("go_generate_news_company")
    @trace_task(tracer)
    def generate_news_company(self):
        """
        Handles requests classified for the 'CompanyNewsCrew'.
        Invokes the `CompanyNewsCrew` to generate news content related to the given topic.
        """
        # Import function explicitly to ensure availability during runtime

        self.state.output_file = "output/company_news/report.json"
        print(f"Generating news about: {self.state.to_crew_inputs().get('topic', 'N/A')}")

        # Generate the news
        self.state.company_news_report = CompanyNewsCrew().crew().kickoff(inputs=self.state.to_crew_inputs())
        dump_crewai_state(self.state.company_news_report, "NEWS_COMPANY")
        html_file = "output/company_news/report.html"
        company_news_to_html(self.state.company_news_report, html_file=html_file)

        # return "generate_news_company"

    @listen("go_generate_rss_weekly")
    @trace_task(tracer)
    async def generate_rss_weekly(self):
        """
        Handles requests classified for the 'RssWeeklyCrew'.

        This method orchestrates a three-step pipeline:
        1. Fetch articles from an OPML file.
        2. Translate the articles into French.
        3. Generate a final HTML report.
        """
        print("📰 Generating RSS weekly report (new pipeline)...")
        base_path = Path("output/rss_weekly")
        base_path.mkdir(parents=True, exist_ok=True)

        opml_path = "data/feedly.opml"
        raw_report_path = base_path / "report.json"
        translated_report_path = base_path / "final-report.json"
        html_report_path = base_path / "report.html"

        # Step 1: Fetch articles from OPML
        print("Step 1: Fetching articles...")
        await fetch_articles_from_opml(opml_file_path=opml_path, output_file_path=str(raw_report_path))

        # Step 2: Translate articles using the refactored crew
        print("Step 2: Translating articles...")
        translation_inputs = {
            "input_file": str(raw_report_path),
            "output_file": str(translated_report_path),
        }
        report_output = RssWeeklyCrew().crew().kickoff(inputs=translation_inputs)
        dump_crewai_state(report_output, "RSS_WEEKLY_TRANSLATION")

        # Step 2.5: Save the translated report
        print(f"Step 2.5: Saving translated report to {translated_report_path}...")
        try:
            # Handle the case where the agent returns action traces instead of just JSON
            raw_output = report_output.raw

            # Check if the output contains action traces (starts with "Action:")
            if raw_output.strip().startswith("Action:"):
                print("Detected action trace format in crew output, attempting to extract JSON...")
                # Try to find JSON in the output - look for the last JSON-like structure
                # This is a common pattern when agents output their thought process and then the final result
                json_matches = re.findall(r"\{[\s\S]*\}", raw_output)
                if json_matches:
                    # Use the last match which is likely the final result
                    potential_json = json_matches[-1]
                    try:
                        translated_data = json.loads(potential_json)
                        print("Successfully extracted JSON from action trace output")
                    except json.JSONDecodeError:
                        raise ValueError("Found JSON-like structure but couldn't parse it")
                else:
                    raise ValueError("No JSON structure found in the crew output")
            else:
                # Normal case - the output is already JSON
                translated_data = json.loads(raw_output)

            # Post-process the data to match the expected RssFeeds model structure
            # If the data only has 'articles' but no 'rss_feeds', transform it
            if "articles" in translated_data and "rss_feeds" not in translated_data:
                # Create a wrapper with the expected structure
                processed_data = {
                    "rss_feeds": [
                        {
                            "feed_url": "translated_feed",  # Placeholder feed URL
                            "articles": [],
                        }
                    ]
                }

                # Add link and published fields if they don't exist
                for article in translated_data["articles"]:
                    if "link" not in article:
                        article["link"] = ""  # Add empty link if missing
                    if "published" not in article:
                        article["published"] = ""  # Add empty published date if missing

                # Add the articles to the feed
                processed_data["rss_feeds"][0]["articles"] = translated_data["articles"]

                # Replace the translated data with the processed data
                translated_data = processed_data

            with open(translated_report_path, "w", encoding="utf-8") as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            print("✅ Successfully saved translated report.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ Failed to decode or save translated JSON from crew result: {e}")
            # If we can't save the file, there's no point in continuing.
            return

        # Step 3: Generate the final HTML report
        print("Step 3: Generating HTML report...")
        generate_rss_weekly_html_report(
            json_file_path=str(translated_report_path),
            output_html_path=str(html_report_path),
        )

        # Store the final report path in the state
        self.state.rss_weekly_report = f"Report generated at {html_report_path}"
        self.state.output_file = str(html_report_path)
        print(f"✅ New RSS weekly pipeline complete. Report at: {html_report_path}")

    @listen("go_generate_findaily")
    @trace_task(tracer)
    def generate_findaily(self):
        """
        Handles requests classified for the 'FinDailyCrew'.

        Invokes the `FinDailyCrew` to generate a daily financial analysis report
        including stock portfolio analysis, crypto portfolio analysis, and new
        investment suggestions. Sets `output_file` to `output/findaily/report.html`
        and stores the report in `self.state.fin_daily_report`.
        """

        print("💰 Generating daily financial analysis report...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        stock_csv_file = "data/stock.csv"
        etf_csv_file = "data/etf.csv"
        inputs["stock_csv_path"] = os.path.abspath(stock_csv_file)
        inputs["etf_csv_path"] = os.path.abspath(etf_csv_file)
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        inputs["output_file"] = "output/findaily/report.json"

        # Kick off the crew
        report_content = FinDailyCrew().crew().kickoff(inputs=inputs)
        dump_crewai_state(report_content, "FIN_DAILY")
        html_file = "output/findaily/report.html"

        financial_report_model = parse_crewai_output(report_content, FinancialReport, inputs)
        findaily_to_html(financial_report_model, html_file=html_file)
        print(f"✅ Financial content generated and HTML written to {html_file}")

    @listen("go_generate_news_daily")
    @trace_task(tracer)
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
        inputs["output_file"] = "output/news_daily/news_data.json"

        # Kick off the crew
        report_content = NewsDailyCrew().crew().kickoff(inputs=inputs)
        self.state.news_daily_report = report_content
        dump_crewai_state(report_content, "NEWSDAILY")
        html_file = "output/news_daily/final_report.html"

        daily_news_to_html(report_content, html_file=html_file)

        # Store the news report model data for HTML rendering by generate_html_report
        if hasattr(report_content, "model_dump"):
            self.state.news_daily_model = report_content

        print(f"✅ News content generated and HTML written to {html_file}")

    @listen("go_generate_saint_daily")
    @trace_task(tracer)
    def generate_saint_daily(self):
        """
        Handles requests classified for the 'SaintDailyCrew'.

        Invokes the `SaintDailyCrew` to generate a daily saint report in French
        covering the saint of the day in Switzerland, including biography,
        significance, and connection to Swiss Catholic traditions.
        Sets `output_file` to `output/saint_daily/report.html`
        and stores the report in `self.state.saint_daily_report`.
        """
        self.state.output_file = "output/saint_daily/report.json"
        print("⛪ Generating daily saint report in French...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()

        # Kick off the crew
        report_content = SaintDailyCrew().crew().kickoff(inputs=inputs)
        dump_crewai_state(report_content, "SAINT_DAILY")
        # Store the saint report data for HTML rendering by generate_html_report
        self.state.saint_daily_report = report_content

        html_file = "output/saint_daily/report.html"
        # Store the saint report model data for HTML rendering (consistent with other crews)

        # Minimal, robust CrewAI pattern (like generate_poem)
        if hasattr(report_content, "output") and isinstance(report_content.output, SaintData):
            saint_model = report_content.output
        else:
            saint_model = SaintData.model_validate(json.loads(report_content.raw))
        self.state.saint_daily_model = saint_model
        saint_to_html(saint_model, html_file=html_file)

        print("✅ Saint content generated - HTML rendering will be handled by generate_html_report")

    @listen("go_generate_recipe")
    @trace_task(tracer)
    def generate_recipe(self):
        """
        Handles requests classified for the 'CookingCrew'.

        Invokes the `CookingCrew` to generate a recipe. The result is stored in `self.state.recipe`.
        """
        # Set output paths using project-relative paths
        # No need to create directories as ensure_output_directories() is called at init
        self.state.output_dir = "output/cooking"

        # Get crew inputs - to_crew_inputs() already handles mapping extracted_info fields
        # main_subject_or_activity → topic and user_preferences_and_constraints → special_needs
        crew_inputs = self.state.to_crew_inputs()

        # CRITICAL: Update topic_slug after crew_inputs mapping is applied
        # This ensures topic_slug reflects the mapped topic value from main_subject_or_activity
        if crew_inputs.get("topic") and not self.state.topic_slug:
            self.state.topic_slug = create_topic_slug(crew_inputs["topic"])
            print(f"🔧 Updated topic_slug from mapped topic: {self.state.topic_slug}")

        self.state.output_file = f"{self.state.output_dir}/{self.state.topic_slug}.json"
        crew_inputs["output_file"] = f"{self.state.output_dir}/{self.state.topic_slug}.json"
        crew_inputs["patrika_file"] = f"{self.state.output_dir}/{self.state.topic_slug}.yaml"
        crew_inputs["html_file"] = f"{self.state.output_dir}/{self.state.topic_slug}.html"

        # Log what we're generating
        print(f"🍳 Generating recipe for: {crew_inputs.get('topic', 'Unknown topic')}")
        print(f"📁 YAML export will be saved to: {self.state.output_dir}/{self.state.topic_slug}.yaml")
        print(f"📁 JSON export will be saved to: {self.state.output_dir}/{self.state.topic_slug}.json")
        print(f"📁 Recipte will be saved to: {self.state.output_dir}/{self.state.topic_slug}.html")

        # Create crew using context-driven approach with automatic topic_slug injection
        cooking_result = CookingCrew().crew().kickoff(inputs=crew_inputs)
        dump_crewai_state(cooking_result, "COOKING")

        # Generate HTML using recipe_to_html factory function
        html_file = f"{self.state.output_dir}/{self.state.topic_slug}.html"

        # Parse CrewAI output using utility function
        recipe_model = parse_crewai_output(cooking_result, PaprikaRecipe, crew_inputs)

        # Generate HTML directly
        recipe_to_html(recipe_model, html_file=html_file)

        print("✅ Recipe generation complete")

    @listen("go_generate_menu_designer")
    @trace_task(tracer)
    def generate_menu_designer(self):
        """
        Orchestrates the end-to-end weekly menu generation process using CrewAI native flows.
        """
        self.logger.info("🍽️ Starting Menu Designer Workflow")

        # Initialize utilities and output directory
        menu_generator = MenuGenerator()

        # Extract user preferences from state using to_crew_inputs
        crew_inputs = self.state.to_crew_inputs()
        output_dir = "output/menu_designer"

        # Prepare menu crew inputs using direct CrewAI approach
        self.logger.info("🗓️ Step 1/2: Planning the weekly menu structure")

        menu_structure_result = MenuDesignerCrew().crew().kickoff(inputs=crew_inputs)

        final_report = output_dir + "/" + crew_inputs["menu_slug"] + ".html"

        # Parse menu structure and generate recipes (step 2)
        self.logger.info("👩‍🍳 Step 2/2: Generating individual recipes")
        recipe_specs = menu_generator.parse_menu_structure(menu_structure_result)

        # Process recipes using direct CrewAI calls

        total_recipes = len(recipe_specs)

        cooking_crew = CookingCrew().crew()
        for i, recipe_spec in enumerate(recipe_specs):
            recipe_name = recipe_spec["name"]
            recipe_code = recipe_spec["code"]
            # Generate slug directly from recipe name
            recipe_slug = create_topic_slug(recipe_name)
            self.logger.info(f"  - Recipe {i + 1}/{total_recipes}: {recipe_name} ({recipe_code})")

            try:
                # Direct CrewAI call with slug already included
                recipe_request = {
                    "topic": recipe_spec["name"],
                    "topic_slug": recipe_slug,  # Include slug directly
                    "preferences": f"Type: {recipe_spec['type']}, Day: {recipe_spec['day']}, Meal: {recipe_spec['meal']}",
                }

                cooking_crew.kickoff(inputs=recipe_request)

            except Exception as e:
                self.logger.error(f"  ❌ Error with {recipe_code}: {e}")

        self.state.menu_designer_report = final_report
        return final_report

    @listen("go_generate_book_summary")
    @trace_task(tracer)
    def generate_book_summary(self):
        """
        Handles requests classified for the 'LibraryCrew'.

        Invokes the `LibraryCrew` to generate a book summary. Sets the main output
        to `output/library/book_summary.json`. The summary is stored in
        `self.state.book_summary`.
        """

        print(f"Generating book summary for: {self.state.to_crew_inputs().get('topic', 'N/A')}")
        inputs = self.state.to_crew_inputs()
        inputs["output_file"] = "output/library/book_summary.json"

        # Generate the book summary
        report_content = LibraryCrew().crew().kickoff(inputs=inputs)
        dump_crewai_state(report_content, "BOOK_SUMMARY")
        html_file = "output/library/book_summary.html"

        # Store the book summary data for HTML rendering by generate_html_report
        self.state.book_summary = report_content

        # Parse CrewAI output using utility function
        book_summary_model = parse_crewai_output(report_content, BookSummaryReport, inputs)

        # Generate HTML directly (don't store model in state - CrewAI Flow state has predefined schema)
        book_summary_to_html(book_summary_model, html_file=html_file)

    @listen("go_generate_shopping_advice")
    @trace_task(tracer)
    def generate_shopping_advice(self):
        """
        Handles requests classified for the 'ShoppingAdvisorCrew'.

        Uses ShoppingAdvisorCrew to generate structured shopping advice data,
        then HtmlDesignerCrew to generate the HTML report.
                Sets `output_file` to `output/shopping_advisor/shopping_advice.html`.
        """
        # No need to create directories as ensure_output_directories() is called at init

        print(f"🛒 Generating shopping advice for: {self.state.user_request}")

        # Prepare inputs for ShoppingAdvisorCrew
        crew_inputs = self.state.to_crew_inputs()
        crew_inputs["output_file"] = "output/shopping_advisor/shopping_advice.json"

        # Generate structured shopping advice data
        shopping_result = ShoppingAdvisorCrew().crew().kickoff(inputs=crew_inputs)
        dump_crewai_state(shopping_result, "SHOPPING_ADVISOR")

        # Extract ShoppingAdviceOutput from the result
        shopping_advice_obj = None
        if hasattr(shopping_result, "pydantic") and shopping_result.pydantic:
            shopping_advice_obj = shopping_result.pydantic
        elif hasattr(shopping_result, "tasks_output") and shopping_result.tasks_output:
            # Look for the shopping_data_task output
            for task_output in shopping_result.tasks_output:
                if hasattr(task_output, "pydantic") and task_output.pydantic:
                    shopping_advice_obj = task_output.pydantic
                    break

        if not shopping_advice_obj:
            print("⚠️ Could not extract ShoppingAdviceOutput from crew result")
            return

        print(f"🔍 ShoppingAdviceOutput extracted: {shopping_advice_obj.product_info.name}")
        # Store in CrewAI state
        self.state.shopping_advice_model = shopping_advice_obj

        # Set output file path
        topic = self.state.extracted_info.topic or "product-recommendation"
        topic_slug = topic.lower().replace(" ", "-").replace("'", "").replace('"', "")
        html_file = f"output/shopping_advisor/shopping-advice-{topic_slug}.html"
        self.state.output_file = html_file

        # Generate HTML using the factory function
        shopping_advice_to_html(shopping_advice_obj, topic=topic, html_file=html_file)

        print("✅ Shopping advice content generated - HTML rendering will be handled by generate_html_report")

    @listen("go_generate_meeting_prep")
    @trace_task(tracer)
    def generate_meeting_prep(self):
        """
        Handles requests classified for the 'MeetingPrepCrew'.

        Invokes `MeetingPrepCrew` to generate meeting preparation materials.
        It expects a 'company' name in the inputs, falling back to 'topic' if
        'company' is not available.
        """
        # No need to create directories as ensure_output_directories() is called at init

        # Prepare inputs and handle company fallback
        current_inputs = self.state.to_crew_inputs()
        company = current_inputs.get("company")
        if not company:
            company = current_inputs.get("topic")  # Fallback to topic if company is not specified
            current_inputs["company"] = company  # Ensure 'company' key is in inputs for the crew
            print(f"⚠️ No company specified for meeting prep, using topic as company: {company}")

        print(f"Generating meeting prep for company: {company or 'N/A'}")

        current_inputs["output_file"] = "output/meeting/meeting_preparation.json"
        # Generate the meeting prep
        meeting_result = MeetingPrepCrew().crew().kickoff(inputs=current_inputs)
        self.state.meeting_prep_report = meeting_result

        # Parse CrewAI output using utility function
        try:
            self.state.meeting_prep_report = parse_crewai_output(
                meeting_result, MeetingPrepReport, current_inputs
            )
            print("Successfully parsed meeting prep result to MeetingPrepReport model")
        except Exception as e:
            print(f"Error parsing meeting prep result: {e}")

        # Set the final report to the JSON output
        self.state.final_report = self.state.meeting_prep_report
        dump_crewai_state(self.state.meeting_prep_report, "MEETING_PREP")
        html_file = "output/meeting/meeting_preparation.html"
        meeting_prep_to_html(self.state.meeting_prep_report, html_file=html_file)

        # return "generate_meeting_prep"

    @listen("go_generate_sales_prospecting_report")
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
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
    @trace_task(tracer)
    def generate_holiday_plan(self):
        """
        Handles requests classified for the 'HolidayPlannerCrew'.

        Invokes the `HolidayPlannerCrew` to generate a holiday itinerary.
        Requires a 'destination' in the inputs. Sets `output_file` to
        `output/travel_guides/itinerary.html` and stores the plan in
        `self.state.holiday_plan`. Returns 'error' if no destination is found.
        """
        current_inputs = self.state.to_crew_inputs()
        current_inputs["output_file"] = "output/travel_guides/itinerary.json"

        if not current_inputs.get("destination"):
            print("⚠️ No destination found for holiday plan. Aborting and routing to error.")
            # TODO: Define an actual 'error' step or handle this more gracefully.
            return "error"  # Or another appropriate error state like 'go_unknown'

        print(f"Starting HolidayPlannerCrew with inputs: {current_inputs}")

        # Run the crew
        holiday_plan = HolidayPlannerCrew().crew().kickoff(inputs=current_inputs)
        dump_crewai_state(holiday_plan, "HOLIDAY_PLANNER")
        html_file = "output/travel_guides/itinerary.html"
        holiday_plan_to_html(holiday_plan, html_file=html_file)
        self.state.holiday_plan = holiday_plan
        return "generate_holiday_plan"

    @listen("go_generate_marketing_content")
    @trace_task(tracer)
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
            "generate_menu_designer",
        )
    )
    @trace_task(tracer)
    def generate_html_report(self, *results):
        """
        Synchronizes the flow after a crew has finished its primary task.

        Now integrates HtmlDesignerCrew to generate professional HTML reports
        from the consolidated data before proceeding to the email sending step.
        """
        pass  # noqa: PIE790
        # self.logger.info("Join step reached. Generating professional HTML report with HtmlDesignerCrew.")

        # try:
        #     # Initialize HtmlDesignerCrew
        #     html_designer_crew = HtmlDesignerCrew()

        #     # Prepare state data for proper CrewAI Flow
        #     selected_crew = getattr(self.state, "selected_crew", "UNKNOWN")
        #     state_data = self.state.model_dump()
        #     state_data["selected_crew"] = selected_crew

        #     # Debug: Log available state data keys and analyze structure
        #     log_state_keys(state_data)
        #     analyze_crewai_output(state_data, selected_crew)

        #     # Debug: Dump complete CrewAI state to JSON file for easier debugging
        #     dump_crewai_state(state_data, selected_crew)

        #     # Debug: Log specific data if available (poem, recipe, etc.)
        #     filter_keywords = ["poem", "title", "recipe", "saint", "cook"]
        #     log_state_keys(state_data, filter_keywords)

        #     self.logger.info(f"🎨 Using proper CrewAI Flow to generate {selected_crew} HTML report...")
        #     self.logger.info("🌙 Dark mode and responsive design enabled automatically")

        #     # Ensure output directories exist using proper utility
        #     ensure_output_directories()

        #     # Use proper CrewAI Flow - prepare inputs and kickoff the crew
        #     # Ensure output file has .html extension for HTML reports
        #     html_output_file = self.state.output_file
        #     if html_output_file and not html_output_file.endswith(".html"):
        #         html_output_file = html_output_file.rsplit(".", 1)[0] + ".html"

        #     inputs = self.state.to_crew_inputs()
        #     inputs["state_data"] = state_data
        #     inputs["selected_crew"] = selected_crew
        #     inputs["output_file"] = html_output_file  # Required by task config

        #     # Proper CrewAI Flow execution
        #     result = html_designer_crew.crew().kickoff(inputs=inputs)

        #     html_result = f"HTML report generated successfully via CrewAI Flow for {selected_crew}"

        #     self.logger.info(
        #         "✅ Unified template system completed successfully. Professional HTML report generated."
        #     )
        #     self.logger.info(f"📄 Report available at: {html_output_file}")
        #     self.logger.debug(f"Template system result: {html_result}")

        #     # Update state with the generated HTML report path
        #     self.state.output_file = html_output_file

        #     self.logger.info(f"🎯 {selected_crew} report generated with unified CSS and dark mode support")

        # except Exception as e:
        #     # NO FALLBACK - Expose the real error for proper debugging
        #     error_msg = f"❌ HtmlDesignerCrew execution failed: {e}"
        #     self.logger.error(error_msg)
        #     self.logger.error(f"Selected crew: {selected_crew}")
        #     self.logger.error(f"State data keys: {list(state_data.keys())}")

        #     # Re-raise the exception to prevent silent failures
        #     raise RuntimeError(f"HTML generation failed for {selected_crew}: {e}") from e

    @listen(or_("generate_cross_reference_report", "generate_html_report"))
    @trace_task(tracer)
    def send_email(self):
        """
        Sends the generated report via email after specific crew completions or general join.

        This method listens to the completion of 'generate_cross_reference_report'
        or the general 'join' event (indicating completion of other main content-generating crews).
        It ensures an email is sent only once per flow execution by checking `self.state.email_sent`.

        It uses the prepare_email_params utility function to construct email parameters
        (recipient, subject, body, attachment) from the application state. The PostCrew
        is then invoked to handle the actual email dispatch.
        """

        if not self.state.email_sent:
            print("📬 Preparing to send email...")

            # Use utility function to prepare all email parameters
            # email_inputs = prepare_email_params(self.state)

            # # Log attachment status for better visibility
            # if email_inputs.get("attachment_path"):
            #     print(f"Using attachment: {email_inputs['attachment_path']}")
            # else:
            #     print("⚠️ No valid attachment file found. Email will be sent without attachment.")
        #     if email_inputs.get("attachment_path"):
        #         print(f"Using attachment: {email_inputs['attachment_path']}")
        #     else:
        #         print("⚠️ No valid attachment file found. Email will be sent without attachment.")

        #     # Instantiate and kickoff the PostCrew
        #     try:
        #         post_crew = PostCrew()
        #         email_result = post_crew.crew().kickoff(inputs=email_inputs)
        #         print(f"📧 Email sending process initiated. Result: {email_result}")
        #         self.state.email_sent = True  # Mark email as sent to prevent duplicates
        #     except Exception as e:
        #         print(f"❌ Error during email sending: {e}")
        # else:
        #     print("📧 Email already sent for this request. Skipping.")
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
    request = (
        user_input if user_input else "Get me the recipe for Salade Cesar"
        # else "get me all news for company JT International SA"
        # else "get the daily news report"
        # else "Meeting preparation for JT International SA with the  CTO to discuss PowerFlex deployment in switzerland for their new 9 OpenShift clusters "
        # else "Get me the recipe for Salade Cesar"
        # else "let's plan a weekend in cinque terre for 1 person in end of july, I start from finale ligure, give the best hotel and restaurant options"
        # else "get the rss weekly report"
        # else "Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus ethique et non israélienne"
        # else "get the daily  news report"
        # else "get the findaily report"
        # else "Donne moi le saint du jour en français"
        # else "Get me a poem on the mouse of the desert Muad dib"
        # else "tell me all about the book : Clamser à Tataouine de Raphaël Quenard"
        # else "Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French"
    )

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
    kickoff(user_input="Generate the weekly RSS report")

    # To generate a plot of the flow, uncomment the following line:
    # plot()
