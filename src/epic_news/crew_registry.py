"""Crew metadata in one place (simplification S4).

One ``CrewSpec`` per crew: its routing key, report title, output model, JSON and DOCX
paths and DOCX assembler. Metadata only: routing stays in ``ReceptionFlow.determine_crew``
and every crew keeps its own ``@listen`` step. ``None`` marks a value the step computes
per run (a file named after the request) or does not have.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel

from epic_news.models.crews.book_summary_report import BookSummaryReport
from epic_news.models.crews.company_news_report import CompanyNewsReport
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.models.crews.cross_reference_report import CrossReferenceReport
from epic_news.models.crews.deep_research import DeepResearchReport
from epic_news.models.crews.financial_report import FinancialReport
from epic_news.models.crews.meeting_prep_report import MeetingPrepReport
from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.models.crews.news_daily_report import NewsDailyReport
from epic_news.models.crews.pestel_report import PestelReport
from epic_news.models.crews.poem_report import PoemJSONOutput
from epic_news.models.crews.rss_weekly_report import RssWeeklyReport
from epic_news.models.crews.saint_daily_report import SaintData
from epic_news.models.crews.sales_prospecting_report import SalesProspectingReport
from epic_news.models.crews.shopping_advice_report import ShoppingAdviceOutput
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
from epic_news.utils.holiday_report import assemble_holiday_docx


class CrewKey(StrEnum):
    """Routing key of every crew, plus UNKNOWN. Values equal names (classifier output)."""

    BOOK_SUMMARY = "BOOK_SUMMARY"
    COMPANY_NEWS = "COMPANY_NEWS"
    COOKING = "COOKING"
    DEEPRESEARCH = "DEEPRESEARCH"
    FINDAILY = "FINDAILY"
    HOLIDAY_PLANNER = "HOLIDAY_PLANNER"
    MEETING_PREP = "MEETING_PREP"
    MENU = "MENU"
    NEWSDAILY = "NEWSDAILY"
    OPEN_SOURCE_INTELLIGENCE = "OPEN_SOURCE_INTELLIGENCE"
    PESTEL = "PESTEL"
    POEM = "POEM"
    RSS = "RSS"
    SAINT = "SAINT"
    SALES_PROSPECTING = "SALES_PROSPECTING"
    SHOPPING = "SHOPPING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CrewSpec:
    """Metadata for one crew. It does not route and does not run anything."""

    key: CrewKey
    title: str
    model_cls: type[BaseModel] | None
    json_path: str | None
    docx_path: str | None
    docx_assembler: Callable[..., str]


_SPECS = (
    CrewSpec(
        CrewKey.POEM,
        "Création poétique",
        PoemJSONOutput,
        "output/poem/poem.json",
        "output/poem/poem.docx",
        assemble_poem_docx,
    ),
    CrewSpec(
        CrewKey.COMPANY_NEWS,
        "Actualités d'entreprise",
        CompanyNewsReport,
        "output/company_news/report.json",
        "output/company_news/report.docx",
        assemble_company_news_docx,
    ),
    CrewSpec(
        CrewKey.FINDAILY,
        "Analyse financière quotidienne",
        FinancialReport,
        "output/findaily/report.json",
        "output/findaily/report.docx",
        assemble_fin_daily_docx,
    ),
    CrewSpec(
        CrewKey.NEWSDAILY,
        "Revue de presse quotidienne",
        NewsDailyReport,
        "output/news_daily/news_data.json",
        "output/news_daily/report.docx",
        assemble_news_daily_docx,
    ),
    CrewSpec(
        CrewKey.SAINT,
        "Saint du jour",
        SaintData,
        "output/saint_daily/report.json",
        "output/saint_daily/report.docx",
        assemble_saint_docx,
    ),
    CrewSpec(
        CrewKey.BOOK_SUMMARY,
        "Analyse littéraire",
        BookSummaryReport,
        "output/library/book_summary.json",
        "output/library/book_summary.docx",
        assemble_book_summary_docx,
    ),
    CrewSpec(
        CrewKey.MEETING_PREP,
        "Préparation de réunion",
        MeetingPrepReport,
        "output/meeting/meeting_preparation.json",
        "output/meeting/meeting_preparation.docx",
        assemble_meeting_prep_docx,
    ),
    CrewSpec(
        CrewKey.SALES_PROSPECTING,
        "Prospection commerciale",
        SalesProspectingReport,
        "output/sales_prospecting/report.json",
        "output/sales_prospecting/report.docx",
        assemble_sales_prospecting_docx,
    ),
    CrewSpec(
        CrewKey.PESTEL,
        "Analyse PESTEL",
        PestelReport,
        "output/pestel/report.json",
        "output/pestel/report.docx",
        assemble_pestel_docx,
    ),
    CrewSpec(
        CrewKey.DEEPRESEARCH,
        "Recherche approfondie",
        DeepResearchReport,
        "output/deep_research/report.json",
        "output/deep_research/report.docx",
        assemble_deep_research_docx,
    ),
    CrewSpec(
        CrewKey.RSS,
        "Synthèse RSS hebdomadaire",
        RssWeeklyReport,
        "output/rss_weekly/final-report.json",
        "output/rss_weekly/report.docx",
        assemble_rss_docx,
    ),
    CrewSpec(CrewKey.COOKING, "Recette", PaprikaRecipe, None, None, assemble_cooking_docx),
    CrewSpec(CrewKey.MENU, "Menu de la semaine", WeeklyMenuPlan, None, None, assemble_menu_docx),
    CrewSpec(
        CrewKey.SHOPPING,
        "Conseil d'achat",
        ShoppingAdviceOutput,
        "output/shopping_advisor/shopping_advice.json",
        None,
        assemble_shopping_docx,
    ),
    CrewSpec(
        CrewKey.HOLIDAY_PLANNER,
        "Planificateur de vacances",
        None,
        "output/holiday/itinerary.json",
        "output/holiday/itinerary.docx",
        assemble_holiday_docx,
    ),
    CrewSpec(
        CrewKey.OPEN_SOURCE_INTELLIGENCE,
        "Intelligence open source",
        CrossReferenceReport,
        "output/osint/global_report.json",
        "output/osint/report.docx",
        assemble_osint_docx,
    ),
)

CREW_REGISTRY: dict[CrewKey, CrewSpec] = {spec.key: spec for spec in _SPECS}

# Crews whose Flow step runs through ReceptionFlow._run_standard.
STANDARD_CREWS: tuple[CrewKey, ...] = (
    CrewKey.POEM,
    CrewKey.COMPANY_NEWS,
    CrewKey.FINDAILY,
    CrewKey.NEWSDAILY,
    CrewKey.SAINT,
    CrewKey.BOOK_SUMMARY,
    CrewKey.MEETING_PREP,
    CrewKey.SALES_PROSPECTING,
    CrewKey.PESTEL,
    CrewKey.DEEPRESEARCH,
)
