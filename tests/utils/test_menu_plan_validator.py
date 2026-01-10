"""Tests for MenuPlanValidator utility."""

import json

from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.utils.menu_plan_validator import MenuPlanValidator


class TestMenuPlanValidator:
    """Test cases for MenuPlanValidator."""

    def test_validate_and_fix_dish_info_valid(self):
        """Test validation of valid dish info."""
        valid_dish = {
            "name": "Salade César",
            "dish_type": "entrée",
            "description": "Salade fraîche avec croûtons",
            "seasonal_ingredients": ["laitue", "parmesan"],
            "nutritional_highlights": "Riche en vitamines",
        }

        result = MenuPlanValidator.validate_and_fix_dish_info(valid_dish)
        assert result["name"] == "Salade César"
        assert result["dish_type"] == "entrée"
        assert isinstance(result["seasonal_ingredients"], list)

    def test_validate_and_fix_dish_info_invalid_enum(self):
        """Test fixing invalid dish_type enum."""
        invalid_dish = {
            "name": "Test Dish",
            "dish_type": "invalid_type",
            "description": "Test description",
            "seasonal_ingredients": ["ingredient1"],
            "nutritional_highlights": "Test highlights",
        }

        result = MenuPlanValidator.validate_and_fix_dish_info(invalid_dish)
        assert result["dish_type"] in ["entrée", "plat principal", "dessert"]

    def test_validate_and_fix_dish_info_missing_fields(self):
        """Test fixing missing required fields."""
        incomplete_dish = {"dish_type": "entrée"}

        result = MenuPlanValidator.validate_and_fix_dish_info(incomplete_dish)
        assert result["name"] is not None
        assert result["description"] is not None
        assert isinstance(result["seasonal_ingredients"], list)
        assert result["nutritional_highlights"] is not None

    def test_validate_and_fix_dish_info_null_seasonal_ingredients(self):
        """Test fixing null seasonal_ingredients."""
        dish_with_null = {
            "name": "Test Dish",
            "dish_type": "entrée",
            "description": "Test description",
            "seasonal_ingredients": None,
            "nutritional_highlights": "Test highlights",
        }

        result = MenuPlanValidator.validate_and_fix_dish_info(dish_with_null)
        assert isinstance(result["seasonal_ingredients"], list)
        assert len(result["seasonal_ingredients"]) > 0

    def test_validate_and_fix_weekly_plan_missing_daily_menus(self):
        """Test fixing missing daily_menus array."""
        incomplete_plan = {"week_start_date": "2025-01-27", "season": "hiver"}

        result = MenuPlanValidator.validate_and_fix_weekly_plan(incomplete_plan)
        assert isinstance(result["daily_menus"], list)
        assert len(result["daily_menus"]) == 7

    def test_validate_and_fix_weekly_plan_malformed_daily_menus(self):
        """Test fixing malformed daily_menus."""
        malformed_plan = {
            "week_start_date": "2025-01-27",
            "season": "hiver",
            "daily_menus": [
                {"day": "Lundi"},  # Missing required fields
                "invalid_menu",  # Not a dict
                None,  # Null value
            ],
        }

        result = MenuPlanValidator.validate_and_fix_weekly_plan(malformed_plan)
        assert len(result["daily_menus"]) == 7

        # Check first menu was fixed
        first_menu = result["daily_menus"][0]
        assert first_menu["day"] == "Lundi"
        assert "lunch" in first_menu
        assert "dinner" in first_menu

    def test_parse_and_validate_ai_output_valid_json(self):
        """Test parsing valid JSON AI output."""
        valid_json = {
            "week_start_date": "2025-01-27",
            "season": "hiver",
            "daily_menus": [
                {
                    "day": "Lundi",
                    "date": "2025-01-27",
                    "lunch": {
                        "meal_type": "déjeuner",
                        "starter": {
                            "name": "Salade verte",
                            "dish_type": "entrée",
                            "description": "Salade fraîche",
                            "seasonal_ingredients": ["laitue"],
                            "nutritional_highlights": "Vitamines",
                        },
                        "main_course": {
                            "name": "Poulet rôti",
                            "dish_type": "plat principal",
                            "description": "Poulet aux herbes",
                            "seasonal_ingredients": ["poulet", "herbes"],
                            "nutritional_highlights": "Protéines",
                        },
                    },
                    "dinner": {
                        "meal_type": "dîner",
                        "starter": {
                            "name": "Soupe",
                            "dish_type": "entrée",
                            "description": "Soupe de légumes",
                            "seasonal_ingredients": ["légumes"],
                            "nutritional_highlights": "Fibres",
                        },
                        "main_course": {
                            "name": "Poisson grillé",
                            "dish_type": "plat principal",
                            "description": "Poisson frais grillé",
                            "seasonal_ingredients": ["poisson"],
                            "nutritional_highlights": "Oméga-3",
                        },
                    },
                }
            ],
            "nutritional_balance": "Équilibré",
            "gustative_coherence": "Harmonieux",
            "constraints_adaptation": "Adapté",
            "preferences_integration": "Intégré",
        }

        result = MenuPlanValidator.parse_and_validate_ai_output(valid_json)
        assert isinstance(result, WeeklyMenuPlan)
        assert len(result.daily_menus) == 7  # Should be expanded to 7 days

    def test_parse_and_validate_ai_output_json_string(self):
        """Test parsing JSON string AI output."""
        json_string = json.dumps(
            {
                "week_start_date": "2025-01-27",
                "season": "hiver",
                "daily_menus": [],
                "nutritional_balance": "Test",
                "gustative_coherence": "Test",
                "constraints_adaptation": "Test",
                "preferences_integration": "Test",
            }
        )

        result = MenuPlanValidator.parse_and_validate_ai_output(json_string)
        assert isinstance(result, WeeklyMenuPlan)

    def test_parse_and_validate_ai_output_markdown_wrapped(self):
        """Test parsing markdown-wrapped JSON."""
        markdown_json = """```json
{
    "week_start_date": "2025-01-27",
    "season": "hiver",
    "daily_menus": [],
    "nutritional_balance": "Test",
    "gustative_coherence": "Test",
    "constraints_adaptation": "Test",
    "preferences_integration": "Test"
}
```"""

        result = MenuPlanValidator.parse_and_validate_ai_output(markdown_json)
        assert isinstance(result, WeeklyMenuPlan)

    def test_parse_and_validate_ai_output_invalid_json(self):
        """Test handling invalid JSON."""
        invalid_json = "{ invalid json structure"

        result = MenuPlanValidator.parse_and_validate_ai_output(invalid_json)
        assert result is None

    def test_create_fallback_menu_plan(self):
        """Test creating fallback menu plan."""
        fallback = MenuPlanValidator.create_fallback_menu_plan()

        assert isinstance(fallback, WeeklyMenuPlan)
        assert len(fallback.daily_menus) == 7
        assert fallback.week_start_date == "2025-01-27"
        assert fallback.season == "hiver"

        # Check each day has proper structure
        for daily_menu in fallback.daily_menus:
            assert daily_menu.lunch is not None
            assert daily_menu.dinner is not None
            assert daily_menu.lunch.starter is not None
            assert daily_menu.lunch.main_course is not None
            assert daily_menu.dinner.starter is not None
            assert daily_menu.dinner.main_course is not None

    def test_validate_and_fix_daily_meal_missing_dishes(self):
        """Test fixing daily meal with missing dishes."""
        incomplete_meal = {"meal_type": "déjeuner"}

        result = MenuPlanValidator.validate_and_fix_daily_meal(incomplete_meal, "déjeuner")
        assert result["meal_type"] == "déjeuner"
        assert "starter" in result
        assert "main_course" in result
        assert isinstance(result["starter"], dict)
        assert isinstance(result["main_course"], dict)

    def test_validate_and_fix_daily_menu_missing_meals(self):
        """Test fixing daily menu with missing meals."""
        incomplete_menu = {"day": "Mardi", "date": "2025-01-28"}

        result = MenuPlanValidator.validate_and_fix_daily_menu(incomplete_menu)
        assert result["day"] == "Mardi"
        assert result["date"] == "2025-01-28"
        assert "lunch" in result
        assert "dinner" in result
        assert result["lunch"]["meal_type"] == "déjeuner"
        assert result["dinner"]["meal_type"] == "dîner"
