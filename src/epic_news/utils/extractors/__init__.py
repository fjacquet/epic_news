"""Content extractors package for different crew types.

This package provides a modular approach to extracting structured content from different
crew outputs. Each extractor is responsible for one specific crew type, following the
Single Responsibility Principle.
"""

# Keep __init__.py minimal - "Light as a Haiku" philosophy
from epic_news.utils.extractors.factory import ContentExtractorFactory as ContentExtractorFactory
