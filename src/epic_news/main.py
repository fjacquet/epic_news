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

import asyncio
import datetime
import json
import os
import re
import warnings
from pathlib import Path
from typing import Any

from crewai.flow import Flow, listen, or_, router, start
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, PydanticDeprecatedSince20, PydanticDeprecatedSince211

from epic_news.config.mcp_config import close_mcp
from epic_news.config.routing_guide import ROUTING_GUIDE, routing_categories

# Patch CrewAI's Pydantic schema parser to support Python 3.10 ``X | Y`` unions
from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_news.company_news_crew import CompanyNewsCrew
from epic_news.crews.company_profiler.company_profiler_crew import CompanyProfilerCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import CrossReferenceReportCrew
from epic_news.crews.deep_research.deep_research import DeepResearchCrew
from epic_news.crews.fin_daily.fin_daily import FinDailyCrew
from epic_news.crews.geospatial_analysis.geospatial_analysis_crew import GeospatialAnalysisCrew
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.hr_intelligence.hr_intelligence_crew import HRIntelligenceCrew
from epic_news.crews.information_extraction.information_extraction_crew import InformationExtractionCrew
from epic_news.crews.legal_analysis.legal_analysis_crew import LegalAnalysisCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.news_daily.news_daily import NewsDailyCrew
from epic_news.crews.pestel.pestel_crew import PestelCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.rss_weekly.rss_weekly_crew import RssWeeklyCrew
from epic_news.crews.saint_daily.saint_daily import SaintDailyCrew
from epic_news.crews.sales_prospecting.sales_prospecting_crew import SalesProspectingCrew
from epic_news.crews.shopping_advisor.shopping_advisor import ShoppingAdvisorCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew
from epic_news.crew_registry import CREW_REGISTRY, CrewSpec
from epic_news.models.content_state import ContentState, CrewCategories
from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.models.crews.company_news_report import CompanyNewsReport
from epic_news.models.crews.company_profiler_report import CompanyProfileReport
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.models.crews.geospatial_analysis_report import GeospatialAnalysisReport
from epic_news.models.crews.hr_intelligence_report import HRIntelligenceReport
from epic_news.models.crews.legal_analysis_report import LegalAnalysisReport
from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.models.crews.tech_stack_report import TechStackReport
from epic_news.models.crews.web_presence_report import WebPresenceReport
from epic_news.services.menu_designer_service import MenuDesignerService, MenuPlanError
from epic_news.tools.recent_search_tool import RecentSearchTool
from epic_news.utils.concurrency import bounded_map

# Import the normalization utility
from epic_news.utils.diagnostics import dump_crewai_state, parse_crewai_output
from epic_news.utils.directory_utils import ensure_output_directories
from epic_news.utils.docx_report.crews.book_summary import assemble_book_summary_docx
from epic_news.utils.docx_report.crews.company_news import assemble_company_news_docx
from epic_news.utils.docx_report.crews.cooking import assemble_cooking_docx
from epic_news.utils.docx_report.crews.deep_research import assemble_deep_research_docx
from epic_news.utils.docx_report.crews.fin_daily import assemble_fin_daily_docx
from epic_news.utils.docx_report.crews.meeting_prep import assemble_meeting_prep_docx
from epic_news.utils.docx_report.crews.menu import assemble_menu_docx
from epic_news.utils.docx_report.crews.news_daily import assemble_news_daily_docx
from epic_news.utils.docx_report.crews.osint import assemble_osint_docx
from epic_news.utils.docx_report.crews.pestel import assemble_pestel_docx
from epic_news.utils.docx_report.crews.poem import assemble_poem_docx
from epic_news.utils.docx_report.crews.rss_weekly import assemble_rss_docx
from epic_news.utils.docx_report.crews.saint import assemble_saint_docx
from epic_news.utils.docx_report.crews.sales_prospecting import assemble_sales_prospecting_docx
from epic_news.utils.docx_report.crews.shopping import assemble_shopping_docx
from epic_news.utils.docx_report.dispatch import emit_report
from epic_news.utils.email_sender import EmailDeliveryError, send_report_email
from epic_news.utils.flow_enforcement import akickoff_flow, kickoff_flow
from epic_news.utils.flow_helpers import load_or_parse_model
from epic_news.utils.holiday_report import assemble_holiday_docx
from epic_news.utils.interrupt import RunCancelledError, install_force_quit_handler, raise_if_cancelled
from epic_news.utils.logger import setup_logging
from epic_news.utils.menu_days import DEFAULT_MENU_DAYS
from epic_news.utils.menu_generator import MenuGenerator
from epic_news.utils.observability import get_observability_tools, trace_task
from epic_news.utils.recipe_export import export_recipe, recipe_from_result
from epic_news.utils.report_utils import load_rss_weekly_report, prepare_email_params
from epic_news.utils.rss_utils import fetch_articles_from_opml
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

# Where the classifier writes its routing decision. It is NOT a rendered report: if
# state.output_file still points here at email time, no crew produced a report and the
# email step must refuse to deliver this JSON as if it were one.
CLASSIFY_DECISION_FILE = "output/classify/decision.md"


OSINT_REPORT_STEMS = (
    "company_profile",
    "tech_stack",
    "web_presence",
    "hr_intelligence",
    "legal_analysis",
    "geospatial_analysis",
)
# Per-report cap (characters of JSON) so the six reports stay a bounded prompt (~30k tokens).
OSINT_REPORT_MAX_CHARS = 20_000


def _load_osint_reports(osint_dir: Path) -> str:
    """Compact JSON of the OSINT sub-reports written by the parallel run, one key per stem.

    Missing or unreadable reports are skipped; each report is capped at OSINT_REPORT_MAX_CHARS.
    """
    reports: dict[str, Any] = {}
    for stem in OSINT_REPORT_STEMS:
        path = osint_dir / f"{stem}.json"
        try:
            text = json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False)
        except (OSError, ValueError) as exc:
            logger.warning(f"OSINT sub-report {path} skipped: {exc}")
            continue
        if len(text) > OSINT_REPORT_MAX_CHARS:
            logger.warning(
                f"OSINT sub-report {stem} truncated from {len(text)} to {OSINT_REPORT_MAX_CHARS} chars"
            )
            text = text[:OSINT_REPORT_MAX_CHARS] + "...[truncated]"
        reports[stem] = text
    return "\n".join(f'"{stem}": {text}' for stem, text in reports.items())


def _category_from_classification(result: Any, categories: dict[str, str]) -> str:
    """Category chosen by ClassifyCrew's typed output; UNKNOWN when missing or invalid."""
    model = getattr(result, "pydantic", None)
    selected = (getattr(model, "selected_crew", "") or "").strip().upper()
    return selected if selected in categories else CrewCategories.UNKNOWN


"""                                                                                      """
"""                     All the magic is here                                            """
"""                                                                                      """


_PESTEL_DIMENSIONS = ("political", "economic", "social", "technological", "environmental", "legal")
_PESTEL_PRESEARCH_MAX_CHARS = 8000
_PESTEL_NO_RECENT_RESULTS = "No recent search results available; use recent_search or hybrid_search."


def _pestel_recent_research(topic: str, geography: str) -> dict[str, str]:
    """Run one last-12-months search per PESTEL dimension; return one text block per dimension."""
    tool = RecentSearchTool()

    def _search(dimension: str) -> str:
        raise_if_cancelled(f"PESTEL pre-search ({dimension})")
        query = f"{dimension} factors affecting {topic} in {geography}: latest developments"
        try:
            text = str(tool._run(query)).strip()
            payload = json.loads(text) if text else None
            if isinstance(payload, dict) and payload.get("error"):
                logger.warning(f"PESTEL pre-search error for {dimension}: {payload['error']}")
                return _PESTEL_NO_RECENT_RESULTS
        except RunCancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - a failed pre-search must not stop the analysis
            logger.warning(f"PESTEL pre-search failed for {dimension}: {exc}")
            return _PESTEL_NO_RECENT_RESULTS
        if not text:
            logger.warning(f"PESTEL pre-search returned nothing for {dimension}")
            return _PESTEL_NO_RECENT_RESULTS
        if len(text) > _PESTEL_PRESEARCH_MAX_CHARS:
            logger.info(f"PESTEL pre-search for {dimension} truncated from {len(text)} chars")
            text = text[:_PESTEL_PRESEARCH_MAX_CHARS] + " [truncated]"
        logger.info(f"PESTEL pre-search for {dimension}: {len(text)} chars")
        return text

    results = bounded_map(_search, _PESTEL_DIMENSIONS, "PESTEL_PRESEARCH_CONCURRENCY", 3)
    return dict(zip(_PESTEL_DIMENSIONS, results, strict=True))


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
        self.logger = logger
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
        self.logger.info("🤖 Kicking off Information Extraction Crew...")
        # Instantiate and run the information extraction crew (kickoff-only)
        extraction_crew = InformationExtractionCrew()
        extracted_data = kickoff_flow(
            extraction_crew,
            {
                "user_request": self.state.user_request,
                "categories": routing_categories(),
                "routing_guide": ROUTING_GUIDE,
            },
        )

        dump_crewai_state(extracted_data, "EXTRACTED_INFO")
        # The enrich task runs first, so its brief is the first task output. Store it as
        # the working context for downstream crews; fall back to the raw request when the
        # crew produced no usable brief (never worse than mailing the raw request).
        tasks_output = getattr(extracted_data, "tasks_output", None) or []
        brief = tasks_output[0].raw.strip() if tasks_output and tasks_output[0].raw else ""
        self.state.enriched_brief = brief or self.state.user_request
        # Update the state with the extracted information
        if extracted_data:
            # Assuming extracted_data has a .pydantic attribute for the model instance
            self.state.extracted_info = extracted_data.pydantic
            self.logger.info("✅ Information extraction complete.")
        else:
            self.logger.warning("⚠️ Information extraction failed or returned no data.")

    @listen("extract_info")
    @trace_task(tracer)
    def classify(self):
        """
        Classifies the user request into a predefined category.

        Uses the crew chosen during extraction (`extracted_info.selected_crew`) when it
        is a known category; otherwise falls back to `ClassifyCrew`, which writes its
        decision to `output/classify/decision.md`. The result updates
        `self.state.selected_crew`.
        """
        topic = (
            self.state.extracted_info.main_subject_or_activity
            if self.state.extracted_info and hasattr(self.state.extracted_info, "main_subject_or_activity")
            else "Unknown Topic"  # Provide a default if topic extraction failed or info is missing
        )
        self.logger.info(f"Routing request: '{self.state.user_request}' with topic: '{topic}'")
        # Define the output file path for the classification decision.
        self.state.output_file = CLASSIFY_DECISION_FILE

        candidate = (getattr(self.state.extracted_info, "selected_crew", None) or "").strip().upper()
        if candidate in self.state.categories and candidate != CrewCategories.UNKNOWN:
            parsed_category = candidate
            self.logger.info(f"✅ Crew selected during extraction: {parsed_category}")
        else:
            self.logger.info("🔁 Extraction gave no usable crew; falling back to ClassifyCrew")
            inputs = {**self.state.to_crew_inputs(), "routing_guide": ROUTING_GUIDE}
            classification_result = kickoff_flow(ClassifyCrew(), inputs)
            dump_crewai_state(classification_result, "CLASSIFICATION")
            parsed_category = _category_from_classification(classification_result, self.state.categories)

        self.state.selected_crew = parsed_category
        self.logger.info(f"✅ Classification complete. Selected crew: {self.state.selected_crew}")

    def _run_standard(self, spec: CrewSpec, crew: Any, inputs: dict[str, Any]) -> tuple[Any, BaseModel]:
        """Run a standard crew: kickoff, debug dump, model from its JSON, DOCX report.

        A JSON left by an earlier run is deleted first so it is never read as this run's
        output; an MCP server the crew started is stopped even if the kickoff fails.
        Returns the raw crew output and the validated model.
        """
        if spec.model_cls is None or spec.json_path is None or spec.docx_path is None:
            raise ValueError(f"{spec.key} is not a standard crew (missing model or paths)")
        model_cls, json_path, docx_path = spec.model_cls, spec.json_path, spec.docx_path
        Path(json_path).unlink(missing_ok=True)
        self.state.output_file = json_path
        inputs["output_file"] = json_path
        try:
            output = kickoff_flow(crew, inputs)
        finally:
            # CrewBase stops an MCP server only after a successful kickoff.
            close_mcp(crew)
        dump_crewai_state(output, spec.key)
        model = load_or_parse_model(json_path, model_cls, output, inputs, spec.title)
        emit_report(self.state, lambda: spec.docx_assembler(model, self.state.to_crew_inputs(), docx_path))
        return output, model

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
        if self.state.selected_crew == "DEEPRESEARCH":
            return "go_generate_deep_research"
        if self.state.selected_crew == "PESTEL":
            return "go_generate_pestel"
        # Fallback for unhandled or unknown crew types.
        # Consider logging this event for monitoring.
        self.logger.warning(f"⚠️ Unknown crew type: {self.state.selected_crew}. Routing to 'go_unknown'.")
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
        self.logger.warning("Unknown crew type selected or error in routing.")
        self.state.final_report = "Error: Unknown crew type or routing issue. Unable to process the request."
        # Ensure output_file is set, even if to a default, before writing.
        if not self.state.output_file:
            self.state.output_file = "output/unknown_request_error.md"
            self.logger.warning(f"Output file not set, defaulting to {self.state.output_file}")

    @listen("go_generate_poem")
    @trace_task(tracer)
    def generate_poem(self):
        """
        Handles requests classified for the 'PoemCrew'.

        Invokes the `PoemCrew` to generate a poem based on the provided topic.
        Sets `output_file` to `output/poem/poem.docx`.
        """
        inputs = self.state.to_crew_inputs()
        self.logger.info(f"Generating poem about: {inputs.get('topic', 'N/A')}")
        self._run_standard(CREW_REGISTRY["POEM"], PoemCrew(), inputs)

    @listen("go_generate_news_company")
    @trace_task(tracer)
    def generate_news_company(self):
        """
        Handles requests classified for the 'CompanyNewsCrew'.
        Invokes the `CompanyNewsCrew` to generate news content related to the given topic.
        """
        crew_inputs = self.state.to_crew_inputs()
        self.logger.info(f"Generating news about: {crew_inputs.get('topic', 'N/A')}")
        output, _ = self._run_standard(CREW_REGISTRY["COMPANY_NEWS"], CompanyNewsCrew(), crew_inputs)
        self.state.company_news_report = output

    @listen("go_generate_rss_weekly")
    @trace_task(tracer)
    async def generate_rss_weekly(self):
        """
        Handles requests classified for the 'RssWeeklyCrew'.

        This method orchestrates a three-step pipeline:
        1. Fetch articles from an OPML file.
        2. Translate the articles into French.
        3. Generate the DOCX report.
        """
        self.logger.info("📰 Generating RSS weekly report (new pipeline)...")
        base_path = Path("output/rss_weekly")
        base_path.mkdir(parents=True, exist_ok=True)

        opml_path = "data/feedly.opml"
        raw_report_path = base_path / "report.json"
        translated_report_path = base_path / "final-report.json"

        # Step 1: Fetch articles from OPML
        self.logger.info("Step 1: Fetching articles...")
        await fetch_articles_from_opml(opml_file_path=opml_path, output_file_path=str(raw_report_path))

        # Step 2: Translate articles using the refactored crew
        self.logger.info("Step 2: Translating articles...")
        translation_inputs = {
            "input_file": str(raw_report_path),
            "output_file": str(translated_report_path),
        }
        # This method is async (Step 1 awaits fetch_articles_from_opml); CrewAI 1.15
        # rejects a synchronous crew.kickoff() from within the running event loop.
        # Use the async flow wrapper, matching generate_osint.
        report_output = await akickoff_flow(RssWeeklyCrew(), translation_inputs)
        dump_crewai_state(report_output, "RSS_WEEKLY_TRANSLATION")

        # Step 2.5: Save the translated report
        self.logger.info(f"Step 2.5: Saving translated report to {translated_report_path}...")
        try:
            # Handle the case where the agent returns action traces instead of just JSON
            raw_output = report_output.raw

            # Check if the output contains action traces (starts with "Action:")
            if raw_output.strip().startswith("Action:"):
                self.logger.info("Detected action trace format in crew output, attempting to extract JSON...")
                # Try to find JSON in the output - look for the last JSON-like structure
                # This is a common pattern when agents output their thought process and then the final result
                json_matches = re.findall(r"\{[\s\S]*\}", raw_output)
                if json_matches:
                    # Use the last match which is likely the final result
                    potential_json = json_matches[-1]
                    try:
                        translated_data = json.loads(potential_json)
                        self.logger.info("Successfully extracted JSON from action trace output")
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
            self.logger.info("✅ Successfully saved translated report.")
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"❌ Failed to decode or save translated JSON from crew result: {e}")
            # Without the translated file there is no report to build: stop the run.
            raise

        # Step 3: Generate the DOCX report (an error stops the run; nothing is emailed)
        self.logger.info("Step 3: Generating report...")
        emit_report(
            self.state,
            lambda: assemble_rss_docx(
                load_rss_weekly_report(str(translated_report_path)),
                self.state.to_crew_inputs(),
                "output/rss_weekly/report.docx",
            ),
        )

        # Store the final report path in the state
        self.state.rss_weekly_report = f"Report generated at {self.state.output_file}"
        self.logger.info(f"✅ New RSS weekly pipeline complete. Report at: {self.state.output_file}")

    @listen("go_generate_findaily")
    @trace_task(tracer)
    def generate_findaily(self):
        """
        Handles requests classified for the 'FinDailyCrew'.

        Invokes the `FinDailyCrew` to generate a daily financial analysis report
        including stock portfolio analysis, crypto portfolio analysis, and new
        investment suggestions. Sets `output_file` to `output/findaily/report.docx`
        and stores the report in `self.state.fin_daily_report`.
        """

        self.logger.info("💰 Generating daily financial analysis report...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        stock_csv_file = "data/stock.csv"
        etf_csv_file = "data/etf.csv"
        inputs["stock_csv_path"] = os.path.abspath(stock_csv_file)
        inputs["etf_csv_path"] = os.path.abspath(etf_csv_file)
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")

        output, _ = self._run_standard(CREW_REGISTRY["FINDAILY"], FinDailyCrew(), inputs)
        self.state.fin_daily_report = output
        self.logger.info(f"✅ Financial report generated → {self.state.output_file}")

    @listen("go_generate_news_daily")
    @trace_task(tracer)
    def generate_news_daily(self):
        """
        Handles requests classified for the 'NewsDailyCrew'.

        Invokes the `NewsDailyCrew` to generate a daily news report in French
        covering top 10 news items for Suisse Romande, Suisse, France, Europe,
        World, Wars, and Economy. Sets `output_file` to `output/news_daily/report.docx`
        and stores the report in `self.state.news_daily_report`.
        """
        self.logger.info("📰 Generating daily news report in French...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        inputs["report_language"] = "French"

        # _run_standard points output_file at the rendered report (was the intermediate
        # JSON) so the email attaches — and the UI displays — the report, not raw JSON.
        output, news_daily_model = self._run_standard(CREW_REGISTRY["NEWSDAILY"], NewsDailyCrew(), inputs)
        self.state.news_daily_report = output
        self.state.news_daily_model = news_daily_model
        self.logger.info(f"✅ News content generated → {self.state.output_file}")

    @listen("go_generate_saint_daily")
    @trace_task(tracer)
    def generate_saint_daily(self):
        """
        Handles requests classified for the 'SaintDailyCrew'.

        Invokes the `SaintDailyCrew` to generate a daily saint report in French
        covering the saint of the day in Switzerland, including biography,
        significance, and connection to Swiss Catholic traditions.
        Sets `output_file` to `output/saint_daily/report.docx`
        and stores the report in `self.state.saint_daily_report`.
        """
        self.state.output_file = "output/saint_daily/report.json"
        self.logger.info("⛪ Generating daily saint report in French...")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()

        # Kick off the crew (kickoff-only orchestration)
        output = kickoff_flow(SaintDailyCrew(), inputs)
        dump_crewai_state(output, "SAINT_DAILY")
        self.state.saint_daily_report = output

        saint_model = load_or_parse_model(self.state.output_file, SaintData, output, inputs, "saint daily")
        self.state.saint_daily_model = saint_model
        emit_report(
            self.state,
            lambda: assemble_saint_docx(
                saint_model, self.state.to_crew_inputs(), "output/saint_daily/report.docx"
            ),
        )
        self.logger.info(f"✅ Saint content generated → {self.state.output_file}")

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
            self.logger.info(f"🔧 Updated topic_slug from mapped topic: {self.state.topic_slug}")

        self.state.output_file = f"{self.state.output_dir}/{self.state.topic_slug}.json"
        crew_inputs["output_file"] = f"{self.state.output_dir}/{self.state.topic_slug}.json"
        crew_inputs["patrika_file"] = f"{self.state.output_dir}/{self.state.topic_slug}.yaml"

        # Log what we're generating
        self.logger.info(f"🍳 Generating recipe for: {crew_inputs.get('topic', 'Unknown topic')}")
        self.logger.info(
            f"📁 YAML export will be saved to: {self.state.output_dir}/{self.state.topic_slug}.yaml"
        )
        self.logger.info(
            f"📁 JSON export will be saved to: {self.state.output_dir}/{self.state.topic_slug}.json"
        )
        self.logger.info(f"📁 Recipe will be saved to: {self.state.output_dir}/{self.state.topic_slug}.docx")

        # Create crew using kickoff-only orchestration (PR-003 enforcement)
        cooking_result = kickoff_flow(CookingCrew(), crew_inputs)
        dump_crewai_state(cooking_result, "COOKING")

        recipe_model = recipe_from_result(cooking_result, crew_inputs)
        export_recipe(recipe_model, crew_inputs["patrika_file"], crew_inputs["output_file"])

        docx_file = f"{self.state.output_dir}/{self.state.topic_slug}.docx"
        emit_report(
            self.state,
            lambda: assemble_cooking_docx(recipe_model, self.state.to_crew_inputs(), docx_file),
        )
        self.logger.info("✅ Recipe generation complete")

    @listen("go_generate_menu_designer")
    @trace_task(tracer)
    def generate_menu_designer(self):
        """
        Orchestrates the end-to-end weekly menu generation process with validation and error recovery.
        """
        self.logger.info("🍽️ Starting Menu Designer Workflow with Validation")

        # Initialize utilities and output directory
        menu_generator = MenuGenerator()

        # Extract user preferences from state using to_crew_inputs
        crew_inputs = self.state.to_crew_inputs()
        output_dir = "output/menu_designer"

        # Use MenuDesignerService with validation
        self.logger.info("🗓️ Step 1/2: Planning the weekly menu structure with validation")

        try:
            menu_plan = MenuDesignerService().generate_menu_plan(
                constraints=crew_inputs.get("constraints", ""),
                preferences=crew_inputs.get("preferences", ""),
                user_context=crew_inputs.get("user_context", ""),
                season=crew_inputs.get("season", "hiver"),
                current_date=crew_inputs.get("current_date", "2025-01-27"),
                menu_slug=crew_inputs.get("menu_slug", "menu_hebdomadaire"),
                num_days=crew_inputs.get("num_days", DEFAULT_MENU_DAYS),
            )
        except MenuPlanError as e:
            # No placeholder menu: stop the run so no report, recipes or email go out.
            self.logger.error(f"❌ Menu plan could not be produced, stopping the run: {e}")
            raise

        self.logger.info("✅ Menu plan validated successfully")

        docx_file = f"{output_dir}/{crew_inputs['menu_slug']}.docx"
        emit_report(self.state, lambda: assemble_menu_docx(menu_plan, crew_inputs, docx_file))
        self.logger.info(f"✅ Menu plan report written to {self.state.output_file}")

        # Store the validated menu plan in state
        self.state.menu_plan = menu_plan
        final_report = self.state.output_file

        # Convert WeeklyMenuPlan back to dict for recipe parsing (parse_menu_structure)
        menu_structure_result = menu_plan.model_dump()

        # Parse menu structure and generate recipes (step 2)
        self.logger.info("👩‍🍳 Step 2/2: Generating individual recipes")

        recipe_specs = menu_generator.parse_menu_structure(menu_structure_result)

        recipes = self._generate_menu_recipes(recipe_specs)
        generated = sum(recipe is not None for recipe in recipes)
        self.logger.info(f"🍳 {generated}/{len(recipe_specs)} recipes generated")

        # Point output_file at the rendered report so send_email emails it (every
        # other generate_* sets this; without it send_email keeps the classify path).
        self.state.output_file = final_report
        self.state.menu_designer_report = final_report

    def _generate_menu_recipe(self, recipe_spec: dict[str, Any]) -> PaprikaRecipe | None:
        """Generate and export one menu recipe; log and skip it on a provider failure."""
        recipe_slug = create_topic_slug(f"{recipe_spec['code']} {recipe_spec['name']}")
        request = {
            "topic": recipe_spec["name"],
            "topic_slug": recipe_slug,
            "preferences": (
                f"Type: {recipe_spec['type']}, Day: {recipe_spec['day']}, Meal: {recipe_spec['meal']}"
            ),
            "patrika_file": f"output/cooking/{recipe_slug}.yaml",
            "output_file": f"output/cooking/{recipe_slug}.json",
        }
        try:
            recipe = recipe_from_result(kickoff_flow(CookingCrew(), request), request)
            export_recipe(recipe, request["patrika_file"], request["output_file"])
            return recipe
        except RunCancelledError:
            raise
        except Exception as e:
            self.logger.error(f"  ❌ Error with {recipe_spec['code']}: {e}")
            return None

    def _generate_menu_recipes(self, recipe_specs: list[dict[str, Any]]) -> list[PaprikaRecipe | None]:
        """Generate menu recipes in parallel (MENU_RECIPE_CONCURRENCY, default 3), in menu order."""
        return bounded_map(self._generate_menu_recipe, recipe_specs, "MENU_RECIPE_CONCURRENCY")

    @listen("go_generate_book_summary")
    @trace_task(tracer)
    def generate_book_summary(self):
        """
        Handles requests classified for the 'LibraryCrew'.

        Invokes the `LibraryCrew` to generate a book summary. Sets the main output
        to `output/library/book_summary.json`. The summary is stored in
        `self.state.book_summary`.
        """

        inputs = self.state.to_crew_inputs()
        inputs["output_file"] = "output/library/book_summary.json"
        self.logger.info(f"Generating book summary for: {inputs.get('topic', 'N/A')}")

        output = kickoff_flow(LibraryCrew(), inputs)
        dump_crewai_state(output, "BOOK_SUMMARY")
        self.state.book_summary = output

        book_summary_model = load_or_parse_model(
            inputs["output_file"], BookSummaryReport, output, inputs, "book summary"
        )
        # emit_report records the report path in state.output_file so the
        # Streamlit UI / API (app.py reads flow.state.output_file) can locate it.
        emit_report(
            self.state,
            lambda: assemble_book_summary_docx(
                book_summary_model, self.state.to_crew_inputs(), "output/library/book_summary.docx"
            ),
        )

    @listen("go_generate_shopping_advice")
    @trace_task(tracer)
    def generate_shopping_advice(self):
        """
        Handles requests classified for the 'ShoppingAdvisorCrew'.

        Uses ShoppingAdvisorCrew to generate structured shopping advice data,
        then builds the DOCX report.
        Sets `output_file` to `output/shopping_advisor/shopping-advice-<slug>.docx`.
        """
        # No need to create directories as ensure_output_directories() is called at init

        self.logger.info(f"🛒 Generating shopping advice for: {self.state.user_request}")

        # Prepare inputs for ShoppingAdvisorCrew
        crew_inputs = self.state.to_crew_inputs()
        crew_inputs["output_file"] = "output/shopping_advisor/shopping_advice.json"

        # Generate structured shopping advice data (kickoff-only)
        shopping_result = kickoff_flow(ShoppingAdvisorCrew(), crew_inputs)
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
            self.logger.warning("⚠️ Could not extract ShoppingAdviceOutput from crew result")
            return

        self.logger.info(f"🔍 ShoppingAdviceOutput extracted: {shopping_advice_obj.product_info.name}")
        # Store in CrewAI state
        self.state.shopping_advice_model = shopping_advice_obj

        # Set output file path
        topic = self.state.extracted_info.topic or "product-recommendation"
        topic_slug = create_topic_slug(topic)
        docx_file = f"output/shopping_advisor/shopping-advice-{topic_slug}.docx"

        emit_report(
            self.state,
            lambda: assemble_shopping_docx(shopping_advice_obj, self.state.to_crew_inputs(), docx_file),
        )
        self.logger.info(f"✅ Shopping advice content generated → {self.state.output_file}")

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
            self.logger.warning(f"⚠️ No company specified for meeting prep, using topic as company: {company}")

        self.logger.info(f"Generating meeting prep for company: {company or 'N/A'}")

        current_inputs["output_file"] = "output/meeting/meeting_preparation.json"
        output = kickoff_flow(MeetingPrepCrew(), current_inputs)
        dump_crewai_state(output, "MEETING_PREP")

        meeting_model = load_or_parse_model(
            current_inputs["output_file"], MeetingPrepReport, output, current_inputs, "meeting prep"
        )
        self.state.meeting_prep_report = meeting_model
        emit_report(
            self.state,
            lambda: assemble_meeting_prep_docx(
                meeting_model, self.state.to_crew_inputs(), "output/meeting/meeting_preparation.docx"
            ),
        )

    @listen("go_generate_sales_prospecting_report")
    @trace_task(tracer)
    def generate_sales_prospecting_report(self):
        """
        Handles requests classified for the 'SalesProspectingCrew'.

        Invokes the `SalesProspectingCrew` to generate a sales prospecting report,
        including contact information and an approach strategy. Sets `output_file`
        to `output/sales_prospecting/report.docx` and stores the report
        in `self.state.contact_info_report`.
        """
        self.state.output_file = "output/sales_prospecting/report.json"
        inputs = self.state.to_crew_inputs()
        company = inputs.get("company")
        # The crew's YAML prompts use {company} and {our_product}; both must be present.
        # ContentState.our_product defaults to "", so setdefault alone would keep it empty.
        if not inputs.get("our_product"):
            inputs["our_product"] = "our product/service"
        our_product = inputs["our_product"]
        if not company:
            self.logger.warning("Sales prospecting: no target company found in the request")
        self.logger.info(
            f"Generating sales prospecting report for: {company or 'N/A'} regarding {our_product}"
        )

        # Kickoff-only orchestration with JSON-first parsing
        self.state.output_file = "output/sales_prospecting/report.json"
        inputs["output_file"] = self.state.output_file
        output = kickoff_flow(SalesProspectingCrew(), inputs)
        dump_crewai_state(output, "SALES_PROSPECTING")

        report_model = load_or_parse_model(
            self.state.output_file, SalesProspectingReport, output, inputs, "sales prospecting"
        )
        emit_report(
            self.state,
            lambda: assemble_sales_prospecting_docx(
                report_model, self.state.to_crew_inputs(), "output/sales_prospecting/report.docx"
            ),
        )
        self.logger.info(f"✅ Sales prospecting report generated → {self.state.output_file}")

    @listen("go_generate_deep_research")
    @trace_task(tracer)
    def generate_deep_research(self):
        """
        Handles requests classified for the 'DeepResearchCrew'.

        Invokes the `DeepResearchCrew` to generate a comprehensive research report
        on the specified topic using web search, Wikipedia, and content analysis.
        Sets `output_file` to `output/deep_research/report.docx` and stores the report
        in `self.state.deep_research_report`.
        """
        output_file = "output/deep_research/report.json"
        self.state.output_file = output_file
        topic = self.state.to_crew_inputs().get("topic", "N/A")
        self.logger.info(f"🔍 Generating deep research report for: {topic}")

        # Prepare inputs for the crew
        inputs = self.state.to_crew_inputs()
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        inputs["output_file"] = output_file

        # A report.json left by an earlier run must not be read as this run's output.
        Path(output_file).unlink(missing_ok=True)

        deep_research_crew = DeepResearchCrew()
        try:
            output = kickoff_flow(deep_research_crew, inputs)
        finally:
            # CrewBase stops the Wikipedia MCP server only after a successful kickoff.
            close_mcp(deep_research_crew)
        dump_crewai_state(output, "DEEP_RESEARCH")

        model = load_or_parse_model(output_file, DeepResearchReport, output, inputs, "deep_research")
        self.state.deep_research_report = model

        emit_report(
            self.state,
            lambda: assemble_deep_research_docx(model, inputs, "output/deep_research/report.docx"),
        )
        self.logger.info(f"✅ Deep research report generated → {self.state.output_file}")

    @listen("go_generate_pestel")
    @trace_task(tracer)
    def generate_pestel(self):
        """Handle requests classified for the 'PestelCrew'.

        Runs a six-dimension PESTEL analysis (Political, Economic, Social,
        Technological, Environmental, Legal) on the user's topic and writes
        the consolidated report as a DOCX, the attachment-of-record for the
        email step.
        """
        self.state.output_file = "output/pestel/report.json"
        inputs = self.state.to_crew_inputs()
        info = self.state.extracted_info
        if info is not None:
            # The topic stays the request's subject (company, else the extracted
            # subject already in inputs); the location only scopes the geography.
            entity = info.target_company or inputs.get("topic") or info.destination_location
            if entity:
                inputs["topic"] = entity
            geo = (
                info.destination_location
                if info.destination_location and info.destination_location != entity
                else None
            )
            inputs["geography"] = geo or "global"
            inputs["language"] = info.output_language or "English"
        else:
            inputs.setdefault("geography", "global")
            inputs.setdefault("language", "English")
        inputs["current_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        recent = _pestel_recent_research(str(inputs.get("topic", "")), inputs["geography"])
        for dimension, text in recent.items():
            inputs[f"recent_{dimension}"] = text
        self.logger.info(
            f"📊 Generating PESTEL analysis for: {inputs.get('topic', 'N/A')} "
            f"(geo={inputs['geography']}, lang={inputs['language']})"
        )

        pestel_crew = PestelCrew()
        try:
            output = kickoff_flow(pestel_crew, inputs)
        finally:
            # CrewBase stops the Wikipedia MCP server only after a successful kickoff.
            close_mcp(pestel_crew)
        dump_crewai_state(output, "PESTEL")

        # No placeholder report: a parsing failure stops the run (nothing is emailed).
        pestel_model = load_or_parse_model(self.state.output_file, PestelReport, output, inputs, "PESTEL")

        self.state.pestel_report = pestel_model

        emit_report(
            self.state,
            lambda: assemble_pestel_docx(
                pestel_model, self.state.to_crew_inputs(), "output/pestel/report.docx"
            ),
        )
        self.logger.info(f"✅ PESTEL report written to {self.state.output_file}")

    @listen("go_generate_osint")
    @trace_task(tracer)
    async def generate_osint(self):
        """
        Handles requests classified for the 'OPEN_SOURCE_INTELLIGENCE' (OSINT) crew.

        Runs 6 independent OSINT crews in PARALLEL using asyncio.gather() for ~5-6x speedup,
        then runs cross-reference report sequentially.

        Sets `output_file` to `output/osint/report.docx`.
        """
        company = self.state.to_crew_inputs().get("company") or self.state.to_crew_inputs().get(
            "topic", "N/A"
        )
        self.logger.info(f"🚀 Generating OSINT report for: {company}")
        self.logger.info("⚡ Running 6 OSINT crews in PARALLEL for maximum speed...")

        # Run all OSINT crews in parallel (already in async context from CrewAI flow)
        await self._run_osint_parallel()

        # The DOCX consolidates the JSON files the pipeline just wrote.
        emit_report(
            self.state, lambda: assemble_osint_docx(self.state.to_crew_inputs(), "output/osint/report.docx")
        )

    async def _run_osint_parallel(self):
        """
        Run 6 independent OSINT crews in parallel using asyncio.gather().

        This provides ~5-6x speedup compared to sequential execution.
        After parallel crews complete, runs cross-reference report sequentially.
        """
        import time

        start_time = time.perf_counter()
        inputs = self.state.to_crew_inputs()

        # Define the 6 independent crews to run in parallel
        # Each is (crew_name, json_file, model_class, crew_class, state_attr, dump_label)
        parallel_crews = [
            (
                "company_profile",
                "output/osint/company_profile.json",
                CompanyProfileReport,
                CompanyProfilerCrew,
                "company_profile",
                "COMPANY_PROFILE",
            ),
            (
                "tech_stack",
                "output/osint/tech_stack.json",
                TechStackReport,
                TechStackCrew,
                "tech_stack",
                "TECH_STACK",
            ),
            (
                "web_presence",
                "output/osint/web_presence.json",
                WebPresenceReport,
                WebPresenceCrew,
                "web_presence_report",
                "WEB_PRESENCE",
            ),
            (
                "hr_intelligence",
                "output/osint/hr_intelligence.json",
                HRIntelligenceReport,
                HRIntelligenceCrew,
                "hr_intelligence_report",
                "HR_INTELLIGENCE",
            ),
            (
                "legal_analysis",
                "output/osint/legal_analysis.json",
                LegalAnalysisReport,
                LegalAnalysisCrew,
                "legal_analysis_report",
                "LEGAL_ANALYSIS",
            ),
            (
                "geospatial_analysis",
                "output/osint/geospatial_analysis.json",
                GeospatialAnalysisReport,
                GeospatialAnalysisCrew,
                "geospatial_analysis",
                "GEOSPATIAL_ANALYSIS",
            ),
        ]

        # A crew that fails this run must not leave a previous run's report (maybe another
        # target) for the consolidated report to pick up.
        for _, json_file, *_rest in parallel_crews:
            Path(json_file).unlink(missing_ok=True)

        # Create async tasks for all 6 crews
        async def run_crew(
            crew_name: str,
            json_file: str,
            model_class: type,
            crew_class: type,
            state_attr: str,
            dump_label: str,
        ) -> tuple[str, Any]:
            """Run a single crew asynchronously."""
            crew_inputs = inputs.copy()
            crew_inputs["output_file"] = json_file

            self.logger.info(f"🔄 Starting {crew_name} crew...")
            output = await akickoff_flow(crew_class(), crew_inputs)
            dump_crewai_state(output, dump_label)

            # Parse and persist
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                model = model_class.model_validate(data)  # type: ignore[attr-defined]
                self.logger.info(f"📄 Loaded {crew_name} model from saved JSON file")
            except Exception:
                model = parse_crewai_output(output, model_class, crew_inputs)

            # The crews' own output_file is not always written; the consolidated report reads these.
            Path(json_file).write_text(model.model_dump_json(), encoding="utf-8")

            self.logger.info(f"✅ {crew_name} completed and JSON written to {json_file}")
            return (state_attr, output)

        # Run all 6 crews in parallel
        self.logger.info("⚡ Launching 6 crews in parallel with asyncio.gather()...")
        tasks = [
            run_crew(name, json_f, model_cls, crew_cls, state_attr, dump_label)
            for name, json_f, model_cls, crew_cls, state_attr, dump_label in parallel_crews
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and update state
        for result in results:
            if isinstance(result, BaseException):
                self.logger.error(f"❌ Crew failed with error: {result}")
            elif isinstance(result, tuple):
                state_attr, output = result
                setattr(self.state, state_attr, output)

        parallel_elapsed = time.perf_counter() - start_time
        self.logger.info(f"⚡ 6 parallel crews completed in {parallel_elapsed:.2f}s")

        # Now run cross-reference report sequentially (depends on all parallel crews)
        self.logger.info("🔗 Running cross-reference report...")
        await self._run_cross_reference_report(inputs)

        total_elapsed = time.perf_counter() - start_time
        self.logger.info(f"✅ Full OSINT pipeline completed in {total_elapsed:.2f}s")

    async def _run_cross_reference_report(self, inputs: dict[str, Any]) -> None:
        """Run cross-reference report after all parallel crews complete."""
        json_file = "output/osint/global_report.json"

        self.state.output_file = json_file
        company = inputs.get("company") or inputs.get("topic", "N/A")
        self.logger.info(f"Generating Cross Reference Report for: {company}")

        crew_inputs = inputs.copy()
        crew_inputs["output_file"] = json_file
        crew_inputs["osint_reports"] = _load_osint_reports(Path("output/osint"))
        # A previous run's report (maybe another target) must not stand in for this one.
        Path(json_file).unlink(missing_ok=True)
        output = await akickoff_flow(CrossReferenceReportCrew(), crew_inputs)
        self.state.cross_reference_report = output

        dump_crewai_state(output, "CROSS_REFERENCE_REPORT")
        report_model = load_or_parse_model(
            json_file, CrossReferenceReport, output, crew_inputs, "cross reference"
        )
        # The crew's own output_file is not always written; the OSINT DOCX reads this file.
        Path(json_file).write_text(report_model.model_dump_json(), encoding="utf-8")
        self.logger.info(f"✅ Cross reference report generated: {json_file}")

    @listen("go_generate_holiday_plan")
    @trace_task(tracer)
    def generate_holiday_plan(self):
        """
        Handles requests classified for the 'HolidayPlannerCrew'.

        Invokes the `HolidayPlannerCrew` to research a holiday itinerary, then
        assembles a DOCX travel guide from the crew's research fragments.
        When extraction yields no single 'destination' (e.g. a multi-stop road
        trip), falls back to the raw user request so the crew still runs. Sets
        `output_file` to `output/holiday/itinerary.docx` and stores the crew
        result in `self.state.holiday_plan`.
        """
        current_inputs = self.state.to_crew_inputs()
        current_inputs["output_file"] = "output/holiday/itinerary.json"

        if not current_inputs.get("destination"):
            # A multi-stop road trip (Montreux→Montpellier→Anglet→…) has no single
            # "destination", so extraction routinely leaves destination_location empty
            # even when the request is full of places. Skipping here silently left
            # output_file at the classifier's decision.md and emailed that instead of an
            # itinerary. Fall back to the raw request, which carries the full route.
            self.logger.warning("⚠️ No structured destination extracted; falling back to the enriched brief.")
            current_inputs["destination"] = self.state.enriched_brief or self.state.user_request

        # Ensure all required template variables are provided with defaults
        required_vars = {
            "family": current_inputs.get("family", "1 person"),
            "destination": current_inputs.get("destination", "unknown destination"),
            "duration": current_inputs.get("duration", "1 day"),
            "origin": current_inputs.get("origin", "Switzerland"),
            "user_preferences_and_constraints": current_inputs.get(
                "user_preferences_and_constraints", "No specific preferences"
            ),
        }
        current_inputs.update(required_vars)

        self.logger.info(f"Starting HolidayPlannerCrew with inputs: {current_inputs}")
        self.logger.info(f"Required variables: {required_vars}")

        # Run the research crew (no giant format task); then assemble a DOCX from bounded fragments.
        crew_result = kickoff_flow(HolidayPlannerCrew(), current_inputs)
        dump_crewai_state(crew_result, "HOLIDAY_PLANNER")

        docx_file = "output/holiday/itinerary.docx"
        assemble_holiday_docx(crew_result, current_inputs, docx_file)
        self.state.output_file = docx_file
        self.state.holiday_plan = crew_result
        return "generate_holiday_plan"

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
            "generate_holiday_plan",
            "generate_rss_weekly",
            "generate_findaily",
            "generate_news_daily",
            "generate_saint_daily",
            "generate_menu_designer",
            "generate_pestel",
            "generate_deep_research",
        )
    )
    @trace_task(tracer)
    def send_email(self):
        """
        Sends an email with the generated report attached, if applicable.

        This is the final step of the flow. It composes an email with the selected
        content and attaches the generated DOCX report.
        """
        if not self.state.email_sent:
            self.logger.info("📬 Preparing to send email...")

            # Respect environment toggle: EPIC_ENABLE_EMAIL
            flag = os.getenv("EPIC_ENABLE_EMAIL", "false")
            enable_email = str(flag).strip().lower() in {"1", "true", "yes", "on"}
            if not enable_email:
                self.logger.info(
                    "✉️ Email sending disabled by EPIC_ENABLE_EMAIL=%r; skipping email step.",
                    flag,
                )
                self.state.email_sent = True
                return "send_email"

            # No report was generated: output_file still points at the classifier's
            # decision file. Mailing it would deliver the routing JSON as if it were the
            # user's report (a real HOLIDAY_PLANNER run did exactly this). Refuse, and
            # leave email_sent False so the failure is visible rather than papered over.
            if self.state.output_file == CLASSIFY_DECISION_FILE:
                self.logger.error(
                    "🚫 No report was generated (output_file still {}); refusing to email "
                    "the classification decision as a report.",
                    self.state.output_file,
                )
                self.state.email_sent = False
                return "send_email"

            # Use utility function to prepare all email parameters
            email_inputs = prepare_email_params(self.state)

            # A report email without its report is partial: do not send it.
            attachment_path = email_inputs.get("attachment_path")
            if not attachment_path or not Path(attachment_path).is_file():
                self.logger.error(
                    "🚫 Report file {} does not exist on disk; not sending an email without its report.",
                    attachment_path,
                )
                self.state.email_sent = False
                return "send_email"

            self.logger.info(
                "✉️  Email payload: recipient={} subject={!r} attachment={}",
                email_inputs.get("recipient_email"),
                email_inputs.get("subject"),
                attachment_path,
            )

            # Delivery is deterministic: the recipient, the report and the MIME type
            # are all known here. An LLM asked to "send this" substituted the
            # recipient with the placeholder "[EMAIL]" and still reported success,
            # so no agent sits between the validated inputs and the Gmail API.
            try:
                send_report_email(
                    recipient=email_inputs["recipient_email"],
                    subject=email_inputs["subject"],
                    html_body=email_inputs["body"],
                    attachment_path=attachment_path,
                )
            except EmailDeliveryError as e:
                self.logger.error("❌ Email NOT sent: {}", e)
                self.state.email_sent = False
            except Exception as e:
                self.state.email_sent = False
                self.logger.exception("❌ Unexpected error during email sending: {}", e)
            else:
                self.state.email_sent = True
        else:
            self.logger.info("📧 Email already sent for this request. Skipping.")
        return "send_email"  # Implicitly returns method name


def kickoff(user_input: str | None = None):
    """
    Initializes and runs the ReceptionFlow.

    This function serves as the main entry point for executing the entire
    crew orchestration process. It instantiates the `ReceptionFlow` and
    invokes its `run()` method to start the sequence of tasks.
    It can optionally take a user_input string to override the default.

    Returns:
        None. The flow runs for its side effects; the console entry point runs
        ``sys.exit(kickoff())``, which needs None/int — not the flow object.
    """
    setup_logging()
    # A single Ctrl+C cannot stop a flow method: CrewAI runs it in a worker thread that
    # keeps calling the provider and writing report files. Second Ctrl+C exits for real.
    install_force_quit_handler()
    # Sweep/automation hook: let EPIC_NEWS_REQUEST drive the request without
    # editing the hardcoded query below. An explicit user_input arg still wins.
    # Log loudly when it fires (after setup_logging, so it lands in the configured
    # logs) — a leaked/stale env var must not silently reroute a real request to
    # the sweep string with no trace in production.
    env_override = os.getenv("EPIC_NEWS_REQUEST")
    if not user_input and env_override:
        logger.warning("⚠️  EPIC_NEWS_REQUEST override active — request forced to: {!r}", env_override)
        user_input = env_override
    # If user_input is not provided, use a default value.
    request = (
        user_input
        if user_input
        else "Fait moi un etat sur les dernieres actualites de la stack crewai en 2026 en français"
        # else "Fait moi un rapport PESTLE a propos de la societe pictet aujourd'hui en français"
        # else "get the rss weekly report"
        # else "Complete OSINT analysis of Mistral.AI"
        # else "get the daily  news report"
        # else "conduct a deep research study on a travel on the north of the italy between san remo and Genova. Give me the best hotel and restaurant options."
        # + "How to book italian train, electrical bicylce and cultural events. I will be alone for 1 week in end of july "
        # else "conduct a deep research study on the the progress of quantum computing and the possible application in cryptography, genetics and generative AI "
        # else "conduct a deep research on nutanix technologies for the cloud native"
        # else "Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French"
        # else "Donne moi le saint du jour en français"
        # else "Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French"
        # else "let's find a sales prospect at temenos  to sell our product : dell powerflex"
        # else "Complete OSINT analysis of Temenos Group"
        # else "let's plan a weekend in cinque terre for 1 person in end of july, I start from finale ligure, give the best hotel and restaurant options"
        # else "get me all news for company JT International SA"
        # else "get the daily news report"
        # else "Meeting preparation for JT International SA with the  CTO to discuss PowerFlex deployment in switzerland for their new 9 OpenShift clusters "
        # else "Get me the recipe for Salade Cesar"
        # else "let's plan a weekend in cinque terre for 1 person in end of july, I start from finale ligure, give the best hotel and restaurant options"
        # else "get the rss weekly report"
        # else "Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus ethique et non israélienne"
        # else "get the daily  news report"
        # else "Donne moi le saint du jour en français"
        # else "Get me a poem on the mouse of the desert Muad dib"
        # else "tell me all about the book : Clamser à Tataouine de Raphaël Quenard"
        #
    )

    reception_flow = ReceptionFlow(user_request=request)
    try:
        reception_flow.kickoff()
    except Exception:
        # Without this, an unhandled flow exception exits with a bare status 1:
        # loguru never captures it and `crewai flow kickoff` swallows the subprocess
        # stderr, so the real traceback is written nowhere. Log it, then re-raise.
        logger.exception("❌ Flow kickoff failed — full traceback follows")
        raise
    # The console entry runs `sys.exit(kickoff())`; sys.exit() treats a non-None,
    # non-int arg as an error message (prints its repr, exits 1). Returning the
    # flow object made every successful run exit 1. Return None so success exits 0.
    return


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
    flow.plot(output_path)


if __name__ == "__main__":
    # To run the flow, execute this script from the command line:
    # python -m src.epic_news.main
    # You can also pass a custom request:
    # python -m src.epic_news.main "Your custom request here"
    #
    # 📋 For a complete list of supported use cases and example prompts,
    # see USE_CASES.md in the project root directory.
    # Examples: "Analyze my portfolio", "Recipe for cookies", "News about AI"
    kickoff(user_input="What stocks are in my portfolio?")
