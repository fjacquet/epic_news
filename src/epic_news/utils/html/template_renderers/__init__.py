"""
Template Renderers Package

Modular HTML rendering system for different crew types.
Each renderer focuses on a single responsibility.
"""

from .base_renderer import BaseRenderer
from .book_summary_renderer import BookSummaryRenderer
from .financial_renderer import FinancialRenderer
from .generic_renderer import GenericRenderer
from .poem_renderer import PoemRenderer
from .renderer_factory import RendererFactory
from .saint_renderer import SaintRenderer

__all__ = [
    "BaseRenderer",
    "BookSummaryRenderer",
    "FinancialRenderer",
    "GenericRenderer",
    "PoemRenderer",
    "SaintRenderer",
    "RendererFactory",
]
