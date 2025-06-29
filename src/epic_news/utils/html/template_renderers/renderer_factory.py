"""
Renderer Factory

Factory class to create appropriate renderers based on crew type.
Centralizes renderer instantiation and provides fallback to generic renderer.
"""

from .base_renderer import BaseRenderer
from .book_summary_renderer import BookSummaryRenderer
from .financial_renderer import FinancialRenderer
from .generic_renderer import GenericRenderer
from .poem_renderer import PoemRenderer
from .saint_renderer import SaintRenderer


class RendererFactory:
    """Factory for creating crew-specific HTML renderers."""

    # Mapping of crew types to their specific renderers
    _RENDERER_MAP: dict[str, type[BaseRenderer]] = {
        "BOOK_SUMMARY": BookSummaryRenderer,
        "FINDAILY": FinancialRenderer,
        "POEM": PoemRenderer,
        "SAINT": SaintRenderer,
        # Add more mappings as needed
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
