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
        assert result["daily_menus"] == []  # no placeholder days are invented

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
        assert len(result["daily_menus"]) == 1  # only the dict entry is usable

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
        assert len(result.daily_menus) == 1  # not padded to 7 days

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

        assert MenuPlanValidator.parse_and_validate_ai_output(json_string) is None

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

        assert MenuPlanValidator.parse_and_validate_ai_output(markdown_json) is None

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


def _dish(name: str, dish_type: str) -> dict:
    return {
        "name": name,
        "dish_type": dish_type,
        "description": "d",
        "seasonal_ingredients": ["x"],
        "nutritional_highlights": "h",
    }


def _plan(lunch: dict, dinner: dict) -> dict:
    return {
        "week_start_date": "2025-01-27",
        "season": "hiver",
        "daily_menus": [{"day": "Lundi", "date": "2025-01-27", "lunch": lunch, "dinner": dinner}],
        "nutritional_balance": "n",
        "gustative_coherence": "g",
        "constraints_adaptation": "c",
        "preferences_integration": "p",
    }


class TestValidatorKeepsRealDishes:
    """The validator must never replace a dish that has a name."""

    def test_typed_plan_names_preserved(self):
        plan = _plan(
            {
                "meal_type": "déjeuner",
                "starter": _dish("Velouté de panais", "entrée"),
                "main_course": _dish("Blanquette de veau", "plat principal"),
            },
            {
                "meal_type": "dîner",
                "starter": _dish("Salade de lentilles", "entrée"),
                "main_course": _dish("Dos de cabillaud", "plat principal"),
            },
        )
        result = MenuPlanValidator.parse_and_validate_ai_output(json.dumps(plan))
        assert result is not None
        names = [
            d.name
            for dm in result.daily_menus[:1]
            for meal in (dm.lunch, dm.dinner)
            for d in (meal.starter, meal.main_course)
        ]
        assert names == ["Velouté de panais", "Blanquette de veau", "Salade de lentilles", "Dos de cabillaud"]

    def test_dishes_list_shape_not_replaced_by_placeholders(self):
        plan = _plan(
            {"dishes": [_dish("Soupe à l'oignon", "entrée"), _dish("Coq au vin", "plat principal")]},
            {"dishes": [_dish("Endives au jambon", "plat principal")]},
        )
        result = MenuPlanValidator.parse_and_validate_ai_output(json.dumps(plan))
        assert result is not None
        lunch = result.daily_menus[0].lunch
        assert lunch.starter.name == "Soupe à l'oignon"
        assert lunch.main_course.name == "Coq au vin"
        assert result.daily_menus[0].dinner.main_course.name == "Endives au jambon"


class TestNumDays:
    def test_plan_truncated_to_num_days(self):
        meal = {
            "meal_type": "déjeuner",
            "starter": _dish("A", "entrée"),
            "main_course": _dish("B", "plat principal"),
        }
        plan = _plan(meal, meal)
        plan["daily_menus"] = plan["daily_menus"] * 5
        assert len(MenuPlanValidator.validate_and_fix_weekly_plan(plan, 2)["daily_menus"]) == 2

    def test_short_plan_not_padded(self):
        meal = {
            "meal_type": "déjeuner",
            "starter": _dish("A", "entrée"),
            "main_course": _dish("B", "plat principal"),
        }
        result = MenuPlanValidator.validate_and_fix_weekly_plan(_plan(meal, meal), 3)
        assert len(result["daily_menus"]) == 1

    def test_fallback_respects_num_days(self):
        assert len(MenuPlanValidator.create_fallback_menu_plan(2).daily_menus) == 2
