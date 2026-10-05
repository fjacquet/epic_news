"""ContentState keeps one report, the raw output and the OSINT sub-reports (simplification S6)."""

import json
import re
from pathlib import Path

from epic_news.models.content_state import ContentState
from epic_news.models.crews.poem_report import PoemJSONOutput

REMOVED = {
    "company_profile",
    "tech_stack",
    "tech_stack_report",
    "contact_info_report",
    "lead_score_report",
    "geospatial_analysis",
    "osint_report",
    "hr_intelligence_report",
    "legal_analysis_report",
    "web_presence_report",
    "cross_reference_report",
    "pestel_report",
    "news_report",
    "company_news_report",
    "deep_research_report",
    "rss_weekly_report",
    "fin_daily_report",
    "news_daily_report",
    "saint_daily_report",
    "post_report",
    "location_report",
    "holiday_plan",
    "recipe",
    "menu_designer_report",
    "menu_plan",
    "book_summary",
    "shopping_advice_report",
    "shopping_advice_model",
    "poem",
    "meeting_prep_report",
    "financial_report_model",
    "news_daily_model",
    "saint_daily_model",
}
CREWS_DIR = Path(__file__).resolve().parents[2] / "src" / "epic_news" / "crews"


def _poem() -> PoemJSONOutput:
    return PoemJSONOutput.model_validate({"title": "Titre", "poem": "Vers"})


def test_result_fields_are_report_raw_output_and_osint():
    fields = set(ContentState.model_fields)
    assert {"report", "raw_output", "osint", "final_report", "error_message"} <= fields
    assert not (REMOVED & fields)


def test_results_never_reach_crew_inputs():
    state = ContentState(user_request="x")
    state.report = _poem()
    state.raw_output = object()
    state.osint = {"tech_stack": _poem()}
    inputs = state.to_crew_inputs()
    assert not ({"report", "raw_output", "osint"} & set(inputs))


def test_dump_keeps_the_report_fields():
    state = ContentState(user_request="x")
    state.report = _poem()
    state.osint = {"tech_stack": _poem()}
    dumped = json.loads(state.model_dump_json(exclude={"raw_output"}))
    assert dumped["report"]["title"] == "Titre"
    assert dumped["osint"]["tech_stack"]["poem"] == "Vers"


def test_no_crew_prompt_uses_a_removed_field():
    placeholders: set[str] = set()
    for yaml_file in CREWS_DIR.glob("*/config/*.yaml"):
        placeholders |= set(re.findall(r"\{(\w+)\}", yaml_file.read_text(encoding="utf-8")))
    assert not (placeholders & (REMOVED | {"report", "raw_output", "osint"}))
