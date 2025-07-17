"""Shopping extractor module for SHOPPING crew content.

This module provides the extractor for ShoppingCrew output to parse it into
a structured ShoppingAdviceOutput model.
"""

from typing import Any

from loguru import logger

from epic_news.models.crews.shopping_advice_report import ShoppingAdviceOutput
from epic_news.utils.extractors.base_extractor import ContentExtractor


class ShoppingExtractor(ContentExtractor):
    """Extractor for SHOPPING crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract shopping-specific data using ShoppingAdviceOutput Pydantic model."""
        logger.debug("🔍 DEBUG SHOPPING extraction:")
        shopping_obj = state_data.get("shopping_advice_model")
        logger.debug(f"  shopping_obj type: {type(shopping_obj)}")

        if shopping_obj is None:
            logger.warning("  ⚠️ No shopping_advice_model found in state")
            return {"error": "No shopping advice data available"}

        # Handle case where shopping_obj is a dict (due to serialization)
        if isinstance(shopping_obj, dict):
            logger.debug(f"  shopping_obj keys: {list(shopping_obj.keys())}")
            if "shopping_advice_model" in shopping_obj:
                shopping_obj = shopping_obj["shopping_advice_model"]
            # Reconstruct ShoppingAdviceOutput from dict
            try:
                shopping_obj = ShoppingAdviceOutput(**shopping_obj)
                logger.debug(
                    f"  ✅ ShoppingAdviceOutput reconstructed from dict: {shopping_obj.product_info.name}"
                )
            except Exception as e:
                logger.error(f"  ❌ Failed to reconstruct ShoppingAdviceOutput: {e}")
                return {"error": f"Failed to parse shopping advice data: {e}"}
        elif isinstance(shopping_obj, ShoppingAdviceOutput):
            logger.debug(f"  ✅ ShoppingAdviceOutput instance: {shopping_obj.product_info.name}")
        else:
            logger.error(f"  ❌ Unexpected shopping_obj type: {type(shopping_obj)}")
            return {"error": f"Unexpected shopping advice data type: {type(shopping_obj)}"}

        # Extract template data from ShoppingAdviceOutput
        template_data = {
            "product_name": shopping_obj.product_info.name,
            "product_overview": shopping_obj.product_info.overview,
            "product_specifications": shopping_obj.product_info.key_specifications,
            "product_pros": shopping_obj.product_info.pros,
            "product_cons": shopping_obj.product_info.cons,
            "target_audience": shopping_obj.product_info.target_audience,
            "common_issues": shopping_obj.product_info.common_issues,
            "switzerland_prices": [
                {
                    "retailer": price.retailer,
                    "price": price.price,
                    "url": price.url,
                    "shipping_cost": price.shipping_cost,
                    "total_cost": price.total_cost,
                    "notes": price.notes,
                }
                for price in shopping_obj.switzerland_prices
            ],
            "france_prices": [
                {
                    "retailer": price.retailer,
                    "price": price.price,
                    "url": price.url,
                    "shipping_cost": price.shipping_cost,
                    "total_cost": price.total_cost,
                    "notes": price.notes,
                }
                for price in shopping_obj.france_prices
            ],
            "competitors": [
                {
                    "name": comp.name,
                    "price_range": comp.price_range,
                    "key_features": comp.key_features,
                    "pros": comp.pros,
                    "cons": comp.cons,
                    "target_audience": comp.target_audience,
                }
                for comp in shopping_obj.competitors
            ],
            "executive_summary": shopping_obj.executive_summary,
            "final_recommendations": shopping_obj.final_recommendations,
            "best_deals": shopping_obj.best_deals,
            "user_preferences_context": shopping_obj.user_preferences_context,
        }

        logger.debug(f"  🔍 Template data extracted: {template_data['product_name']}")
        return template_data
