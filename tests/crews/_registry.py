"""Shared crew registry for crew-construction tests.

Centralizes the crew-class list so test_agent_llm_contract.py and
test_async_agent_isolation.py don't each maintain their own copy, and caches
crew construction (each crew is only built once per test session).
"""

from functools import cache

from epic_news.crews.classify.classify_crew import ClassifyCrew
from epic_news.crews.company_news.company_news_crew import CompanyNewsCrew
from epic_news.crews.company_profiler.company_profiler_crew import CompanyProfilerCrew
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.crews.cross_reference_report_crew.cross_reference_report_crew import (
    CrossReferenceReportCrew,
)
from epic_news.crews.deep_research.deep_research import DeepResearchCrew
from epic_news.crews.fin_daily.fin_daily import FinDailyCrew
from epic_news.crews.geospatial_analysis.geospatial_analysis_crew import (
    GeospatialAnalysisCrew,
)
from epic_news.crews.holiday_planner.holiday_planner_crew import HolidayPlannerCrew
from epic_news.crews.hr_intelligence.hr_intelligence_crew import HRIntelligenceCrew
from epic_news.crews.information_extraction.information_extraction_crew import (
    InformationExtractionCrew,
)
from epic_news.crews.legal_analysis.legal_analysis_crew import LegalAnalysisCrew
from epic_news.crews.library.library_crew import LibraryCrew
from epic_news.crews.meeting_prep.meeting_prep_crew import MeetingPrepCrew
from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew
from epic_news.crews.news_daily.news_daily import NewsDailyCrew
from epic_news.crews.pestel.pestel_crew import PestelCrew
from epic_news.crews.poem.poem_crew import PoemCrew
from epic_news.crews.post.post_crew import PostCrew

# ReceptionCrew is referenced nowhere outside its own package (dead-code
# candidate for the refactor phase) but the LLM contract still applies.
from epic_news.crews.reception.reception_crew import ReceptionCrew
from epic_news.crews.rss_weekly.rss_weekly_crew import RssWeeklyCrew
from epic_news.crews.saint_daily.saint_daily import SaintDailyCrew
from epic_news.crews.sales_prospecting.sales_prospecting_crew import (
    SalesProspectingCrew,
)
from epic_news.crews.shopping_advisor.shopping_advisor import ShoppingAdvisorCrew
from epic_news.crews.tech_stack.tech_stack_crew import TechStackCrew
from epic_news.crews.web_presence.web_presence_crew import WebPresenceCrew

ALL_CREW_CLASSES = [
    ClassifyCrew,
    CompanyNewsCrew,
    CompanyProfilerCrew,
    CookingCrew,
    CrossReferenceReportCrew,
    DeepResearchCrew,
    FinDailyCrew,
    GeospatialAnalysisCrew,
    HolidayPlannerCrew,
    HRIntelligenceCrew,
    InformationExtractionCrew,
    LegalAnalysisCrew,
    LibraryCrew,
    MeetingPrepCrew,
    MenuDesignerCrew,
    NewsDailyCrew,
    PestelCrew,
    PoemCrew,
    PostCrew,
    ReceptionCrew,
    RssWeeklyCrew,
    SaintDailyCrew,
    SalesProspectingCrew,
    ShoppingAdvisorCrew,
    TechStackCrew,
    WebPresenceCrew,
]

# NOTE: there is deliberately no ASYNC_CREW_CLASSES subset any more. Every crew runs its
# tasks sequentially (async_execution=False) because CrewAI 1.15+ concurrent async tasks
# share one AgentExecutor and can leak a raw tool_calls list into TaskOutput.raw — see
# test_async_agent_isolation.py, which enforces this across ALL_CREW_CLASSES.


@cache
def build_crew(crew_cls):
    """Build (once per session) and cache the wired Crew for a crew class."""
    return crew_cls().crew()
