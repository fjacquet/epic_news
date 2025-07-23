"""Content extractor factory module.

This module provides a factory pattern for creating the appropriate content extractor
for different crew types. It dynamically discovers and registers all extractor classes
at runtime, eliminating the need for manual registration in __init__.py.
"""

import importlib
import inspect
import pathlib
from typing import Any

from loguru import logger

from epic_news.utils.extractors.base_extractor import ContentExtractor


class ContentExtractorFactory:
    """Factory for creating content extractors based on crew type."""

    _extractors: dict[str, type[ContentExtractor]] = {}
    _initialized = False

    @classmethod
    def _register_extractors(cls) -> None:
        """Dynamically discover and register all extractor classes."""
        if cls._initialized:
            return

        # Get the directory containing all extractor modules
        current_dir = pathlib.Path(__file__).parent

        # Import GenericExtractor first as fallback
        try:
            from epic_news.utils.extractors.generic import GenericExtractor

            cls._extractors["GENERIC"] = GenericExtractor
        except ImportError:
            logger.warning("GenericExtractor not found")

        # Discover and register all other extractor classes
        for file in current_dir.glob("*.py"):
            # Skip __init__.py, this module, and base classes
            if file.name in ["__init__.py", "factory.py", "base_extractor.py", "generic.py"]:
                continue

            module_name = f"epic_news.utils.extractors.{file.stem}"
            try:
                module = importlib.import_module(module_name)

                # Find all ContentExtractor subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, ContentExtractor) and obj != ContentExtractor:
                        # Convert the class name to an uppercase crew type
                        # e.g., DeepResearchExtractor -> DEEPRESEARCH
                        crew_type = name.replace("Extractor", "").upper()
                        cls._extractors[crew_type] = obj
                        logger.debug(f"Registered extractor {name} for crew type {crew_type}")

            except ImportError as e:
                logger.warning(f"Could not import module {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error registering extractors from {module_name}: {e}")

        cls._initialized = True
        logger.info(f"Registered {len(cls._extractors)} extractors: {', '.join(cls._extractors.keys())}")

    @classmethod
    def get_extractor(cls, crew_type: str) -> ContentExtractor:
        """Get the appropriate extractor for the given crew type."""
        # Ensure extractors are registered
        if not cls._initialized:
            cls._register_extractors()

        extractor_class = cls._extractors.get(crew_type, cls._extractors.get("GENERIC"))
        if not extractor_class:
            from epic_news.utils.extractors.generic import GenericExtractor

            return GenericExtractor()

        return extractor_class()

    @classmethod
    def extract_content(cls, state_data: dict[str, Any], crew_type: str) -> dict[str, Any]:
        """Extract content data using the appropriate extractor."""
        extractor = cls.get_extractor(crew_type)
        return extractor.extract(state_data)
