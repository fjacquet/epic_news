"""Cooking extractor module for COOKING crew content.

This module provides the extractor for CookingCrew output to parse it into
a structured PaprikaRecipe model.
"""

from typing import Any

from loguru import logger

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.extractors.base_extractor import ContentExtractor


class CookingExtractor(ContentExtractor):
    """Extractor for COOKING crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract cooking-specific data using PaprikaRecipe Pydantic model."""

        recipe_obj = state_data.get("recipe", {})

        # Debug logging
        logger.debug("🔍 DEBUG COOKING extraction:")
        logger.debug(f"  recipe_obj type: {type(recipe_obj)}")
        logger.debug(
            f"  recipe_obj keys: {list(recipe_obj.keys()) if hasattr(recipe_obj, 'keys') else 'N/A'}"
        )

        # Check if we have a direct PaprikaRecipe model (new flow)
        recipe_model = None
        if "paprika_model" in recipe_obj:
            paprika_data = recipe_obj["paprika_model"]
            # Handle case where paprika_model is serialized as dict
            if isinstance(paprika_data, dict):
                try:
                    recipe_model = PaprikaRecipe(**paprika_data)
                    logger.debug(f"  ✅ PaprikaRecipe reconstructed from dict: {recipe_model.name}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to reconstruct PaprikaRecipe from dict: {e}")
                    recipe_model = PaprikaRecipe(name="Recette", ingredients="", directions="")  # type: ignore[call-arg]
            else:
                # Direct PaprikaRecipe object
                recipe_model = paprika_data
                logger.debug(f"  ✅ Direct PaprikaRecipe model found: {recipe_model.name}")
        else:
            # Fallback to old flow with raw data parsing
            recipe_raw = recipe_obj.get("raw", "")
            logger.debug(f"  recipe_raw (first 200 chars): {str(recipe_raw)[:200]}...")

            # Try YAML parsing first (since CookingCrew outputs YAML), then JSON as fallback
            try:
                recipe_model = PaprikaRecipe.from_yaml_string(recipe_raw)
                logger.debug(f"  ✅ YAML parsing successful, recipe: {recipe_model.name}")
            except Exception as e:
                logger.warning(f"  ⚠️ YAML parsing failed, trying JSON: {e}")
                try:
                    recipe_model = PaprikaRecipe.from_json_string(recipe_raw)
                    logger.debug(f"  ✅ JSON parsing successful, recipe: {recipe_model.name}")
                except Exception as e2:
                    logger.error(f"  ❌ Both YAML and JSON parsing failed: {e2}")
                    recipe_model = PaprikaRecipe(name="Recette", ingredients="", directions="")  # type: ignore[call-arg]

        # Use Pydantic model to get template data
        content_data = recipe_model.to_template_data()
        logger.debug(f"  🔍 Template data extracted: {content_data.get('recipe_title', 'Unknown')}")

        return content_data
