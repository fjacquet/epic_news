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
from epic_news.crews.html_designer.html_designer import HtmlDesignerCrew
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
from epic_news.models.content_state import ContentState
from epic_news.utils.debug_utils import analyze_crewai_output, dump_crewai_state, log_state_keys
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.utils.logger import get_logger
from epic_news.utils.menu_generator import MenuGenerator
from epic_news.utils.report_utils import get_final_report_content, write_output_to_file
from epic_news.utils.string_utils import create_topic_slug

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
        if self.state.selected_crew == "MENU":
            return "go_generate_menu_designer"
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
        self.state.output_file = "output/poem/poem.json"
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
        etf_csv_file = "data/etf.csv"
        inputs["stock_csv_path"] = os.path.abspath(stock_csv_file)
        inputs["etf_csv_path"] = os.path.abspath(etf_csv_file)
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

        # Structure the data for HtmlDesignerCrew consumption
        # HtmlDesignerCrew expects saint_daily_report.raw as a JSON string
        import json

        if hasattr(report_content, "raw") and report_content.raw:
            # If the output has a .raw attribute with JSON string
            saint_json_data = report_content.raw
        else:
            # If the output is the JSON object directly, convert to string
            saint_json_data = json.dumps(report_content) if report_content else "{}"

        # Create the expected structure for HtmlDesignerCrew
        self.state.saint_daily_report = {"raw": saint_json_data}

    @listen("go_generate_recipe")
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
            from epic_news.utils.string_utils import create_topic_slug

            self.state.topic_slug = create_topic_slug(crew_inputs["topic"])
            print(f"🔧 Updated topic_slug from mapped topic: {self.state.topic_slug}")

        self.state.output_file = f"{self.state.output_dir}/{self.state.topic_slug}.html"
        self.state.attachment_file = f"{self.state.output_dir}/{self.state.topic_slug}.yaml"

        # Update crew inputs to include attachment_file for paprika_yaml_task
        crew_inputs["attachment_file"] = self.state.attachment_file
        crew_inputs["output_file"] = self.state.output_file

        # Log what we're generating
        print(f"🍳 Generating recipe for: {crew_inputs.get('topic', 'Unknown topic')}")
        print(f"📁 YAML export will be saved to: {self.state.attachment_file}")

        # Create crew using context-driven approach with automatic topic_slug injection
        cooking_result = CookingCrew().crew().kickoff(inputs=crew_inputs)
        print("✅ Recipe generation complete")

        # Extract PaprikaRecipe from CookingCrew result and trigger HtmlDesignerCrew
        if hasattr(cooking_result, "tasks_output") and cooking_result.tasks_output:
            # Get the PaprikaRecipe from the recipe_state_task (last task)
            recipe_state_output = cooking_result.tasks_output[-1]  # Last task is recipe_state_task

            # Check if we have a PaprikaRecipe from any task output
            paprika_recipe = None
            for task_output in cooking_result.tasks_output:
                if hasattr(task_output, "pydantic") and task_output.pydantic:
                    paprika_recipe = task_output.pydantic
                    break

            if paprika_recipe:
                print(f"🔍 PaprikaRecipe extracted: {paprika_recipe.name}")
                print(
                    f"📄 CookingCrew completed {len(cooking_result.tasks_output)} tasks (cook, paprika_yaml, recipe_state)"
                )

                # Store in state for HtmlDesignerCrew using CrewAI state mechanism
                self.state.recipe = {"paprika_model": paprika_recipe}

                # Trigger HtmlDesignerCrew to generate HTML report
                from epic_news.crews.html_designer.html_designer import HtmlDesignerCrew

                html_crew = HtmlDesignerCrew()
                html_result = html_crew.render_unified_report(self.state.model_dump())
                print(f"✅ HTML report generated: {self.state.output_file}")
            else:
                print("⚠️ No PaprikaRecipe found in CookingCrew output")

    @listen("go_generate_menu_designer")
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

        Uses ShoppingAdvisorCrew to generate structured shopping advice data,
        then HtmlDesignerCrew to generate the HTML report.
        Sets `output_file` to `output/shopping_advisor/shopping_advice.html`.
        """
        # No need to create directories as ensure_output_directories() is called at init

        print(f"🛒 Generating shopping advice for: {self.state.user_request}")

        # Prepare inputs for ShoppingAdvisorCrew
        crew_inputs = self.state.to_crew_inputs()

        # Generate structured shopping advice data
        shopping_result = ShoppingAdvisorCrew().crew().kickoff(inputs=crew_inputs)
        print("✅ Shopping advice data generation complete")

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

        if shopping_advice_obj:
            print(f"🔍 ShoppingAdviceOutput extracted: {shopping_advice_obj.product_info.name}")
            # Store in CrewAI state for HtmlDesignerCrew
            self.state.shopping_advice_model = shopping_advice_obj
        else:
            print("⚠️ Could not extract ShoppingAdviceOutput from crew result")
            return

        # Set output file for HTML generation
        topic = self.state.extracted_info.topic or "product-recommendation"
        topic_slug = topic.lower().replace(" ", "-").replace("'", "").replace('"', "")
        self.state.output_file = f"output/shopping_advisor/shopping-advice-{topic_slug}.html"

        # Generate HTML report using HtmlDesignerCrew with unified template system
        # Use the same pattern as other crews: state_data + render_unified_report
        html_designer_crew = HtmlDesignerCrew()
        html_designer_crew.set_crew_context("SHOPPING", self.state.model_dump())

        # Prepare state data for template rendering
        state_data = self.state.model_dump()

        print("🎨 HtmlDesignerCrew configured for SHOPPING with unified template system")
        print(f"📄 Output path: {self.state.output_file}")
        print("🌙 Dark mode and responsive design enabled via universal template")

        # Generate HTML using unified template system (bypassing CrewAI kickoff)
        html_content = html_designer_crew.render_unified_report(state_data)

        # Write HTML content to file
        import os
        os.makedirs(os.path.dirname(self.state.output_file), exist_ok=True)
        with open(self.state.output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.state.shopping_advice_report = html_content
        print(f"✅ HTML report generated: {self.state.output_file}")

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
        # No need to create directories as ensure_output_directories() is called at init
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
            "generate_menu_designer",
        )
    )
    def join(self, *results):
        """
        Synchronizes the flow after a crew has finished its primary task.

        Now integrates HtmlDesignerCrew to generate professional HTML reports
        from the consolidated data before proceeding to the email sending step.
        """

        self.logger.info("Join step reached. Generating professional HTML report with HtmlDesignerCrew.")

        try:
            # Initialize HtmlDesignerCrew
            html_designer_crew = HtmlDesignerCrew()

            # Set crew context for dynamic output file routing
            selected_crew = getattr(self.state, "selected_crew", "UNKNOWN")
            html_designer_crew.set_crew_context(selected_crew)

            # Get the dynamic output file path
            output_file_path = html_designer_crew.output_file_path

            # Prepare state data for template rendering
            state_data = self.state.model_dump()

            # Debug: Log available state data keys and analyze structure
            log_state_keys(state_data)
            analyze_crewai_output(state_data, selected_crew)

            # Debug: Dump complete CrewAI state to JSON file for easier debugging
            dump_crewai_state(state_data, selected_crew)

            # Debug: Log specific data if available (poem, recipe, etc.)
            filter_keywords = ["poem", "title", "recipe", "saint", "cook"]
            log_state_keys(state_data, filter_keywords)

            self.logger.info(
                f"🎨 Using unified template system to generate {selected_crew} HTML report at {output_file_path}..."
            )
            self.logger.info("🌙 Dark mode and responsive design enabled automatically")

            # Generate HTML using unified template system
            html_content = html_designer_crew.render_unified_report(state_data)

            # Ensure output directory exists
            import os

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # Write HTML content to file
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            html_result = f"HTML report generated successfully at {output_file_path}"

            self.logger.info(
                "✅ Unified template system completed successfully. Professional HTML report generated."
            )
            self.logger.info(f"📄 Report available at: {output_file_path}")
            self.logger.debug(f"Template system result: {html_result}")

            # Update state with the generated HTML report path
            self.state.output_file = output_file_path

            self.logger.info(f"🎯 {selected_crew} report generated with unified CSS and dark mode support")

        except Exception as e:
            self.logger.error(f"Error in HtmlDesignerCrew execution: {e}")
            # Fallback to original report generation logic
            self.logger.info("Falling back to original report generation...")

            final_content = get_final_report_content(self.state)
            output_file = self.state.output_file

            success = write_output_to_file(final_content, output_file)

            if not success and final_content is None:
                self.logger.warning(f"No final content to write to {output_file}.")

    @listen(or_("generate_cross_reference_report", "join"))
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
        # from epic_news.utils.report_utils import prepare_email_params

        # if not self.state.email_sent:
        #     print("📬 Preparing to send email...")

        #     # Use utility function to prepare all email parameters
        #     email_inputs = prepare_email_params(self.state)

        #     # Log attachment status for better visibility
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
        user_input
        if user_input
        else "Donne moi des conseils d'achat pour un mac permettant de faire de l'AI en local "
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
    kickoff()

    # To generate a plot of the flow, uncomment the following line:
    # plot()
