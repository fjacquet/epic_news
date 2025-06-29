"""Content data extractors for different crew types.

This module provides a factory pattern for extracting and structuring content data
from different crew outputs. Each extractor is responsible for one specific crew type,
following the Single Responsibility Principle.
"""

import json
from abc import ABC, abstractmethod
from typing import Any

from epic_news.models.financial_report import FinancialReport
from epic_news.models.paprika_recipe import PaprikaRecipe
from epic_news.models.saint_data import SaintData
from epic_news.models.shopping_advice_models import ShoppingAdviceOutput


class ContentExtractor(ABC):
    """Abstract base class for content extractors."""

    @abstractmethod
    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and structure content data from state data."""


class PoemExtractor(ContentExtractor):
    """Extractor for POEM crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract poem-specific data from PoemCrew output."""
        poem_obj = state_data.get("poem", {})
        poem_raw = poem_obj.get("raw", "{}")

        try:
            poem_data = json.loads(poem_raw)
        except (json.JSONDecodeError, TypeError):
            poem_data = {}

        return {
            "poem_title": poem_data.get("title", "Création Poétique"),
            "poem_content": poem_data.get("poem", ""),
            "theme": state_data.get("user_request", ""),
            "author": "Epic News AI",
        }


class CookingExtractor(ContentExtractor):
    """Extractor for COOKING crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract cooking-specific data using PaprikaRecipe Pydantic model."""

        recipe_obj = state_data.get("recipe", {})

        # Debug logging
        print("🔍 DEBUG COOKING extraction:")
        print(f"  recipe_obj type: {type(recipe_obj)}")
        print(f"  recipe_obj keys: {list(recipe_obj.keys()) if hasattr(recipe_obj, 'keys') else 'N/A'}")

        # Check if we have a direct PaprikaRecipe model (new flow)
        recipe_model = None
        if "paprika_model" in recipe_obj:
            paprika_data = recipe_obj["paprika_model"]
            # Handle case where paprika_model is serialized as dict
            if isinstance(paprika_data, dict):
                try:
                    recipe_model = PaprikaRecipe(**paprika_data)
                    print(f"  ✅ PaprikaRecipe reconstructed from dict: {recipe_model.name}")
                except Exception as e:
                    print(f"  ⚠️ Failed to reconstruct PaprikaRecipe from dict: {e}")
                    recipe_model = PaprikaRecipe(name="Recette", ingredients="", directions="")
            else:
                # Direct PaprikaRecipe object
                recipe_model = paprika_data
                print(f"  ✅ Direct PaprikaRecipe model found: {recipe_model.name}")
        else:
            # Fallback to old flow with raw data parsing
            recipe_raw = recipe_obj.get("raw", "")
            print(f"  recipe_raw (first 200 chars): {str(recipe_raw)[:200]}...")

            # Try YAML parsing first (since CookingCrew outputs YAML), then JSON as fallback
            try:
                recipe_model = PaprikaRecipe.from_yaml_string(recipe_raw)
                print(f"  ✅ YAML parsing successful, recipe: {recipe_model.name}")
            except Exception as e:
                print(f"  ⚠️ YAML parsing failed, trying JSON: {e}")
                try:
                    recipe_model = PaprikaRecipe.from_json_string(recipe_raw)
                    print(f"  ✅ JSON parsing successful, recipe: {recipe_model.name}")
                except Exception as e2:
                    print(f"  ❌ Both YAML and JSON parsing failed: {e2}")
                    recipe_model = PaprikaRecipe(name="Recette", ingredients="", directions="")

        # Use Pydantic model to get template data
        content_data = recipe_model.to_template_data()
        print(f"  🔍 Template data extracted: {content_data.get('recipe_title', 'Unknown')}")
        return content_data


class NewsExtractor(ContentExtractor):
    """Extractor for news-related content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract news-specific data."""
        return {
            "articles": state_data.get("articles", []),
            "summary": state_data.get("summary", ""),
            "main_topic": state_data.get("main_topic", ""),
        }


class NewsDailyExtractor(ContentExtractor):
    """Extractor for daily news reports with structured content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract news daily report data using structured format."""
        print("🔍 DEBUG NEWS_DAILY extraction:")

        # Check for news_daily_model in state_data
        news_daily_report = state_data.get("news_daily_model")
        print(f"  news_daily_model type: {type(news_daily_report)}")

        if news_daily_report is None:
            # Try to find news daily report in raw data
            news_daily_data = state_data.get("news_daily_report", {})
            news_raw = news_daily_data.get("raw", "{}")
            print(f"  news_raw (first 200 chars): {str(news_raw)[:200]}...")

            try:
                # Try to parse as JSON
                if isinstance(news_raw, str):
                    news_data = json.loads(news_raw)
                else:
                    news_data = news_raw

                print("  ✅ News data parsed from raw data")
                return news_data
            except Exception as e:
                print(f"  ❌ Failed to parse news data from raw: {e}")
                return {"error": f"Failed to parse news report data: {e}"}
        elif isinstance(news_daily_report, dict):
            # Handle case where news_daily_report is already a dict
            print("  ✅ News data extracted from dict")
            return news_daily_report
        else:
            # Handle Pydantic model case
            try:
                if hasattr(news_daily_report, "model_dump"):
                    result = news_daily_report.model_dump()
                else:
                    result = dict(news_daily_report)
                print("  ✅ News data extracted from model")
                return result
            except Exception as e:
                print(f"  ❌ Failed to extract news data: {e}")
                return {"error": f"Failed to extract news report data: {e}"}


class SaintExtractor(ContentExtractor):
    """Extractor for SAINT crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract saint-specific data using Pydantic model."""

        saint_obj = state_data.get("saint_daily_report", {})
        saint_raw = saint_obj.get("raw", "{}")

        # Use Pydantic model to parse and validate the saint data
        saint_model = SaintData.from_json_string(saint_raw)
        return saint_model.to_template_data()


class ShoppingExtractor(ContentExtractor):
    """Extractor for SHOPPING crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract shopping-specific data using ShoppingAdviceOutput Pydantic model."""
        print("🔍 DEBUG SHOPPING extraction:")
        shopping_obj = state_data.get("shopping_advice_model")
        print(f"  shopping_obj type: {type(shopping_obj)}")

        if shopping_obj is None:
            print("  ⚠️ No shopping_advice_model found in state")
            return {"error": "No shopping advice data available"}

        # Handle case where shopping_obj is a dict (due to serialization)
        if isinstance(shopping_obj, dict):
            print(f"  shopping_obj keys: {list(shopping_obj.keys())}")
            if "shopping_advice_model" in shopping_obj:
                shopping_obj = shopping_obj["shopping_advice_model"]
            # Reconstruct ShoppingAdviceOutput from dict
            try:
                shopping_obj = ShoppingAdviceOutput(**shopping_obj)
                print(f"  ✅ ShoppingAdviceOutput reconstructed from dict: {shopping_obj.product_info.name}")
            except Exception as e:
                print(f"  ❌ Failed to reconstruct ShoppingAdviceOutput: {e}")
                return {"error": f"Failed to parse shopping advice data: {e}"}
        elif isinstance(shopping_obj, ShoppingAdviceOutput):
            print(f"  ✅ ShoppingAdviceOutput instance: {shopping_obj.product_info.name}")
        else:
            print(f"  ❌ Unexpected shopping_obj type: {type(shopping_obj)}")
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

        print(f"  🔍 Template data extracted: {template_data['product_name']}")
        return template_data


class FinancialExtractor(ContentExtractor):
    """Extractor for FIN_DAILY crew content."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract financial report data using FinancialReport Pydantic model."""
        print("🔍 DEBUG FINANCIAL extraction:")

        # Check for financial_report_model in state_data
        financial_report = state_data.get("financial_report_model")
        print(f"  financial_report type: {type(financial_report)}")

        if financial_report is None:
            # Try to find financial report in raw data
            fin_daily_data = state_data.get("fin_daily_report", {})
            fin_raw = fin_daily_data.get("raw", "{}")
            print(f"  fin_raw (first 200 chars): {str(fin_raw)[:200]}...")

            try:
                # Try to parse as JSON
                if isinstance(fin_raw, str):
                    fin_data = json.loads(fin_raw)
                else:
                    fin_data = fin_raw

                # Try to create FinancialReport from the data
                financial_report = FinancialReport.model_validate(fin_data)
                print(f"  ✅ FinancialReport parsed from raw data: {financial_report.title}")
            except Exception as e:
                print(f"  ❌ Failed to parse FinancialReport from raw data: {e}")
                return {"error": f"Failed to parse financial report data: {e}"}
        elif isinstance(financial_report, dict):
            # Handle case where financial_report is a dict (due to serialization)
            try:
                financial_report = FinancialReport.model_validate(financial_report)
                print(f"  ✅ FinancialReport reconstructed from dict: {financial_report.title}")
            except Exception as e:
                print(f"  ❌ Failed to reconstruct FinancialReport: {e}")
                print(f"  🔧 Creating fallback FinancialReport with available data...")
                
                # Create a fallback FinancialReport with available data
                financial_report = FinancialReport(
                    title=financial_report.get('title', 'Daily Financial Report'),
                    executive_summary=financial_report.get('executive_summary', 
                                                         financial_report.get('summary', 'Financial analysis summary not available')),
                    analyses=[],  # Empty list for now - can be enhanced later
                    suggestions=[]  # Empty list for now - can be enhanced later
                )
                print(f"  ✅ Fallback FinancialReport created: {financial_report.title}")

        # Return the financial report model object directly for TemplateManager
        # TemplateManager expects the actual model object, not a dictionary
        return {"financial_report_model": financial_report}


class GenericExtractor(ContentExtractor):
    """Generic extractor for unknown crew types."""

    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        """Extract generic content data."""
        return {
            "content": state_data.get("content", str(state_data)),
            "summary": state_data.get("summary", ""),
            "title": state_data.get("title", ""),
        }


class ContentExtractorFactory:
    """Factory for creating content extractors based on crew type."""

    _extractors = {
        "POEM": PoemExtractor,
        "COOKING": CookingExtractor,
        "NEWS": NewsExtractor,
        "NEWSDAILY": NewsDailyExtractor,
        "SAINT": SaintExtractor,
        "SHOPPING": ShoppingExtractor,
        "FINDAILY": FinancialExtractor,
    }

    @classmethod
    def get_extractor(cls, crew_type: str) -> ContentExtractor:
        """Get the appropriate extractor for the given crew type."""
        extractor_class = cls._extractors.get(crew_type, GenericExtractor)
        return extractor_class()

    @classmethod
    def extract_content(cls, state_data: dict[str, Any], crew_type: str) -> dict[str, Any]:
        """Extract content data using the appropriate extractor."""
        extractor = cls.get_extractor(crew_type)
        return extractor.extract(state_data)
