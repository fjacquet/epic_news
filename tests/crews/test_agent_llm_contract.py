"""Contract: every agent's LLM must come from LLMConfig (OpenRouter base_url).

Agents without llm= resolve via env fallback and silently lose temperature,
base_url, and reasoning settings. Construction only — zero LLM calls.
"""

import os

import pytest

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("MODEL", "openrouter/test/model")

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

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ALL_CREWS = [
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

# Crews whose construction needs an external process (e.g. MCP server) or
# missing external config. Seed empty; populate ONLY with an inline reason
# if Step 2 shows a construction error that is genuinely environmental.
# Likely candidates: DeepResearchCrew, HolidayPlannerCrew, LibraryCrew
# (they start the Wikipedia MCP server) — add them ONLY if construction
# actually fails in this environment.
SKIP_CONSTRUCTION: dict[type, str] = {}


@pytest.mark.parametrize("crew_cls", ALL_CREWS, ids=lambda c: c.__name__)
def test_every_agent_uses_llmconfig(crew_cls):
    if crew_cls in SKIP_CONSTRUCTION:
        pytest.skip(SKIP_CONSTRUCTION[crew_cls])
    crew = crew_cls().crew()
    offenders = []
    for agent in crew.agents:
        base_url = getattr(agent.llm, "base_url", None)
        temperature = getattr(agent.llm, "temperature", None)
        # base_url alone does NOT discriminate in this codebase: CrewAI's
        # own env-fallback LLM construction (crewai.utilities.llm_utils.
        # _llm_via_environment_or_fallback) resolves the same OpenRouter
        # base_url from provider defaults for "openrouter/"-prefixed MODEL
        # values, even when llm= was never passed to Agent(). That fallback
        # path hardcodes temperature=None, whereas
        # LLMConfig.get_openrouter_llm() always sets a numeric temperature
        # (env LLM_TEMPERATURE, default 0.7). temperature is therefore the
        # attribute that actually discriminates "configured via LLMConfig"
        # from "env fallback" here.
        if base_url != OPENROUTER_BASE_URL or temperature is None:
            offenders.append(f"{agent.role!r} (base_url={base_url!r}, temperature={temperature!r})")
    assert not offenders, (
        f"{crew_cls.__name__}: agents not configured via LLMConfig.get_openrouter_llm(): {offenders}"
    )
