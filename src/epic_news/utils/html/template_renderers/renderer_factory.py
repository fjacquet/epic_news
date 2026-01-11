"""
Renderer Factory

Factory class to create appropriate renderers based on crew type.
Centralizes renderer instantiation and provides fallback to generic renderer.
"""

from .base_renderer import BaseRenderer
from .book_summary_renderer import BookSummaryRenderer
from .company_news_renderer import CompanyNewsRenderer
from .company_profiler_renderer import CompanyProfilerRenderer
from .cooking_renderer import CookingRenderer
from .cross_reference_report_renderer import CrossReferenceReportRenderer
from .deep_research_renderer import DeepResearchRenderer
from .financial_renderer import FinancialRenderer
from .generic_renderer import GenericRenderer
from .geospatial_analysis_renderer import GeospatialAnalysisRenderer
from .holiday_renderer import HolidayRenderer
from .hr_intelligence_renderer import HRIntelligenceRenderer
from .legal_analysis_renderer import LegalAnalysisRenderer
from .meeting_prep_renderer import MeetingPrepRenderer
from .menu_renderer import MenuRenderer
from .news_daily_renderer import NewsDailyRenderer
from .osint_global_renderer import OSINTGlobalRenderer
from .poem_renderer import PoemRenderer
from .rss_weekly_renderer import RssWeeklyRenderer
from .saint_renderer import SaintRenderer
from .sales_prospecting_renderer import SalesProspectingRenderer
from .shopping_renderer import ShoppingRenderer
from .tech_stack_renderer import TechStackRenderer
from .web_presence_renderer import WebPresenceRenderer


class RendererFactory:
    """Factory for creating crew-specific HTML renderers."""

    def __init__(self):
        """Initialize the deep research renderer."""
        super().__init__()

    # Mapping of crew types to their specific renderers
    _RENDERER_MAP: dict[str, type[BaseRenderer]] = {
        "BOOK_SUMMARY": BookSummaryRenderer,
        "COMPANY_NEWS": CompanyNewsRenderer,
        "COMPANY_PROFILE": CompanyProfilerRenderer,
        "COOKING": CookingRenderer,
        "CROSS_REFERENCE_REPORT": CrossReferenceReportRenderer,
        "DEEPRESEARCH": DeepResearchRenderer,
        "FINDAILY": FinancialRenderer,
        "GENERIC": GenericRenderer,
        "GEOSPATIAL_ANALYSIS": GeospatialAnalysisRenderer,
        "HOLIDAY_PLANNER": HolidayRenderer,
        "HR_INTELLIGENCE": HRIntelligenceRenderer,
        "LEGAL_ANALYSIS": LegalAnalysisRenderer,
        "MEETING_PREP": MeetingPrepRenderer,
        "OSINT_GLOBAL": OSINTGlobalRenderer,
        "MENU": MenuRenderer,
        "NEWSDAILY": NewsDailyRenderer,
        "POEM": PoemRenderer,
        "RSS_WEEKLY": RssWeeklyRenderer,
        "SAINT": SaintRenderer,
        "SALES_PROSPECTING": SalesProspectingRenderer,
        "SALESPROSPECTING": SalesProspectingRenderer,
        "SHOPPING": ShoppingRenderer,
        "TECH_STACK": TechStackRenderer,
        "WEB_PRESENCE": WebPresenceRenderer,
    }

    @classmethod
    def create_renderer(cls, crew_type: str) -> BaseRenderer:
        """
        Create appropriate renderer for the given crew type.

        Args:
            crew_type: Type of crew (e.g., "BOOK_SUMMARY", "FINDAILY", etc.)

        Returns:
            Renderer instance for the crew type
        """
        renderer_class = cls._RENDERER_MAP.get(crew_type, GenericRenderer)
        return renderer_class()

    @classmethod
    def get_supported_crew_types(cls) -> list[str]:
        """
        Get list of crew types with specialized renderers.

        Returns:
            List of supported crew type strings
        """
        return list(cls._RENDERER_MAP.keys())

    @classmethod
    def register_renderer(cls, crew_type: str, renderer_class: type[BaseRenderer]) -> None:
        """
        Register a new renderer for a crew type.

        Args:
            crew_type: Type of crew
            renderer_class: Renderer class to register
        """
        cls._RENDERER_MAP[crew_type] = renderer_class

    @classmethod
    def has_specialized_renderer(cls, crew_type: str) -> bool:
        """
        Check if a crew type has a specialized renderer.

        Args:
            crew_type: Type of crew to check

        Returns:
            True if specialized renderer exists, False otherwise
        """
        return crew_type in cls._RENDERER_MAP
