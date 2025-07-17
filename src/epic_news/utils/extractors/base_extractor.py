"""Base extractor class for crew content extraction.

This module defines the abstract base class that all content extractors must implement.
"""

from abc import ABC, abstractmethod
from typing import Any


class ContentExtractor(ABC):
    """Abstract base class for content extractors."""

    @abstractmethod
    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and structure content data from state data."""
