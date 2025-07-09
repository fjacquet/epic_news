"""Menu Plan Validator for handling malformed AI output and providing error recovery."""

import json
import logging
from typing import Any, Optional

from pydantic import ValidationError

from src.epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)

logger = logging.getLogger(__name__)


class MenuPlanValidator:
    """Validator and error recovery for WeeklyMenuPlan Pydantic models."""

    @staticmethod
    def validate_and_fix_dish_info(dish_data: dict[str, Any]) -> dict[str, Any]:
        """Validate and fix DishInfo data with error recovery."""
        fixed_dish = dish_data.copy()

        # Fix dish_type enum validation
        dish_type = fixed_dish.get("dish_type", "").strip()
        if dish_type not in ["entrée", "plat principal", "dessert"]:
            # Try to infer from context or use default
            name = fixed_dish.get("name", "").lower()
            if "entrée" in name or "salade" in name or "soupe" in name:
                fixed_dish["dish_type"] = "entrée"
            elif "dessert" in name or "tarte" in name or "gâteau" in name:
                fixed_dish["dish_type"] = "dessert"
            else:
                fixed_dish["dish_type"] = "plat principal"

        # Fix seasonal_ingredients - ensure it's always a list
        if not isinstance(fixed_dish.get("seasonal_ingredients"), list):
            if fixed_dish.get("seasonal_ingredients") is None:
                fixed_dish["seasonal_ingredients"] = ["ingrédients de saison"]
            else:
                # Try to convert string to list
                ingredients_str = str(fixed_dish.get("seasonal_ingredients", ""))
                if ingredients_str:
                    fixed_dish["seasonal_ingredients"] = [ingredients_str]
                else:
                    fixed_dish["seasonal_ingredients"] = ["ingrédients de saison"]

        # Fix nutritional_highlights - ensure it's a non-empty string
        if not isinstance(fixed_dish.get("nutritional_highlights"), str) or not fixed_dish.get(
            "nutritional_highlights"
        ):
            fixed_dish["nutritional_highlights"] = "Équilibré nutritionnellement"

        # Ensure required fields are present
        if not fixed_dish.get("name"):
            fixed_dish["name"] = "Plat traditionnel"
        if not fixed_dish.get("description"):
            fixed_dish["description"] = "Plat préparé avec des ingrédients frais"

        return fixed_dish

    @staticmethod
    def validate_and_fix_daily_meal(meal_data: dict[str, Any], meal_type: str) -> dict[str, Any]:
        """Validate and fix DailyMeal data with error recovery."""
        fixed_meal = meal_data.copy()

        # Ensure meal_type is correct
        fixed_meal["meal_type"] = meal_type

        # Fix starter
        if "starter" not in fixed_meal or not isinstance(fixed_meal["starter"], dict):
            fixed_meal["starter"] = {
                "name": "Entrée du jour",
                "dish_type": "entrée",
                "description": "Entrée fraîche et savoureuse",
                "seasonal_ingredients": ["légumes de saison"],
                "nutritional_highlights": "Riche en vitamines",
            }
        else:
            fixed_meal["starter"] = MenuPlanValidator.validate_and_fix_dish_info(fixed_meal["starter"])

        # Fix main_course
        if "main_course" not in fixed_meal or not isinstance(fixed_meal["main_course"], dict):
            fixed_meal["main_course"] = {
                "name": "Plat principal du jour",
                "dish_type": "plat principal",
                "description": "Plat principal équilibré",
                "seasonal_ingredients": ["protéines", "légumes"],
                "nutritional_highlights": "Source de protéines",
            }
        else:
            fixed_meal["main_course"] = MenuPlanValidator.validate_and_fix_dish_info(
                fixed_meal["main_course"]
            )

        # Fix dessert (optional, only for weekend lunches)
        if "dessert" in fixed_meal and fixed_meal["dessert"] is not None:
            if isinstance(fixed_meal["dessert"], dict):
                fixed_meal["dessert"] = MenuPlanValidator.validate_and_fix_dish_info(fixed_meal["dessert"])
            else:
                # Remove invalid dessert
                fixed_meal["dessert"] = None

        return fixed_meal

    @staticmethod
    def validate_and_fix_daily_menu(menu_data: dict[str, Any]) -> dict[str, Any]:
        """Validate and fix DailyMenu data with error recovery."""
        fixed_menu = menu_data.copy()

        # Ensure required fields
        if not fixed_menu.get("day"):
            fixed_menu["day"] = "Lundi"
        if not fixed_menu.get("date"):
            fixed_menu["date"] = "2025-01-27"

        # Fix lunch
        if "lunch" not in fixed_menu or not isinstance(fixed_menu["lunch"], dict):
            fixed_menu["lunch"] = {}
        fixed_menu["lunch"] = MenuPlanValidator.validate_and_fix_daily_meal(fixed_menu["lunch"], "déjeuner")

        # Fix dinner
        if "dinner" not in fixed_menu or not isinstance(fixed_menu["dinner"], dict):
            fixed_menu["dinner"] = {}
        fixed_menu["dinner"] = MenuPlanValidator.validate_and_fix_daily_meal(fixed_menu["dinner"], "dîner")

        return fixed_menu

    @staticmethod
    def validate_and_fix_weekly_plan(plan_data: dict[str, Any]) -> dict[str, Any]:
        """Validate and fix WeeklyMenuPlan data with comprehensive error recovery."""
        fixed_plan = plan_data.copy()

        # Ensure required top-level fields
        if not fixed_plan.get("week_start_date"):
            fixed_plan["week_start_date"] = "2025-01-27"
        if not fixed_plan.get("season"):
            fixed_plan["season"] = "hiver"

        # Fix daily_menus array
        if not isinstance(fixed_plan.get("daily_menus"), list):
            fixed_plan["daily_menus"] = []

        # Ensure we have exactly 7 daily menus
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        dates = [
            "2025-01-27",
            "2025-01-28",
            "2025-01-29",
            "2025-01-30",
            "2025-01-31",
            "2025-02-01",
            "2025-02-02",
        ]

        valid_menus = []
        for i, day in enumerate(days):
            if i < len(fixed_plan["daily_menus"]) and isinstance(fixed_plan["daily_menus"][i], dict):
                menu_data = fixed_plan["daily_menus"][i]
                menu_data["day"] = day
                menu_data["date"] = dates[i]
                valid_menus.append(MenuPlanValidator.validate_and_fix_daily_menu(menu_data))
            else:
                # Create default menu for missing days
                valid_menus.append(
                    {
                        "day": day,
                        "date": dates[i],
                        "lunch": {
                            "meal_type": "déjeuner",
                            "starter": {
                                "name": f"Entrée du {day}",
                                "dish_type": "entrée",
                                "description": "Entrée fraîche et savoureuse",
                                "seasonal_ingredients": ["légumes de saison"],
                                "nutritional_highlights": "Riche en vitamines",
                            },
                            "main_course": {
                                "name": f"Plat principal du {day}",
                                "dish_type": "plat principal",
                                "description": "Plat principal équilibré",
                                "seasonal_ingredients": ["protéines", "légumes"],
                                "nutritional_highlights": "Source de protéines",
                            },
                        },
                        "dinner": {
                            "meal_type": "dîner",
                            "starter": {
                                "name": f"Entrée du soir - {day}",
                                "dish_type": "entrée",
                                "description": "Entrée légère pour le dîner",
                                "seasonal_ingredients": ["légumes frais"],
                                "nutritional_highlights": "Léger et digestible",
                            },
                            "main_course": {
                                "name": f"Plat du soir - {day}",
                                "dish_type": "plat principal",
                                "description": "Plat principal pour le dîner",
                                "seasonal_ingredients": ["protéines légères"],
                                "nutritional_highlights": "Équilibré pour le soir",
                            },
                        },
                    }
                )

        fixed_plan["daily_menus"] = valid_menus

        # Ensure required summary fields
        if not fixed_plan.get("nutritional_balance"):
            fixed_plan["nutritional_balance"] = "Menu équilibré avec alternance des groupes alimentaires"
        if not fixed_plan.get("gustative_coherence"):
            fixed_plan["gustative_coherence"] = "Harmonie des saveurs et progression culinaire"
        if not fixed_plan.get("constraints_adaptation"):
            fixed_plan["constraints_adaptation"] = "Menu adapté aux contraintes spécifiées"
        if not fixed_plan.get("preferences_integration"):
            fixed_plan["preferences_integration"] = "Intégration des préférences culinaires"

        return fixed_plan

    @staticmethod
    def parse_and_validate_ai_output(ai_output: str) -> Optional[WeeklyMenuPlan]:
        """Parse AI output and validate/fix it to create a valid WeeklyMenuPlan."""
        try:
            # Try to parse as JSON
            if isinstance(ai_output, str):
                # Clean up common AI output issues
                cleaned_output = ai_output.strip()
                if cleaned_output.startswith("```json"):
                    cleaned_output = cleaned_output[7:]
                if cleaned_output.endswith("```"):
                    cleaned_output = cleaned_output[:-3]
                cleaned_output = cleaned_output.strip()

                try:
                    plan_data = json.loads(cleaned_output)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Problematic output: {cleaned_output[:500]}...")
                    return None
            else:
                plan_data = ai_output

            # Validate and fix the data
            fixed_plan_data = MenuPlanValidator.validate_and_fix_weekly_plan(plan_data)

            # Try to create the Pydantic model
            try:
                return WeeklyMenuPlan.model_validate(fixed_plan_data)
            except ValidationError as e:
                logger.error(f"Pydantic validation error after fixing: {e}")
                logger.error(f"Fixed data: {json.dumps(fixed_plan_data, indent=2, ensure_ascii=False)}")
                return None

        except Exception as e:
            logger.error(f"Unexpected error in parse_and_validate_ai_output: {e}")
            return None

    @staticmethod
    def create_fallback_menu_plan() -> WeeklyMenuPlan:
        """Create a valid fallback menu plan when AI output is completely unusable."""
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        dates = [
            "2025-01-27",
            "2025-01-28",
            "2025-01-29",
            "2025-01-30",
            "2025-01-31",
            "2025-02-01",
            "2025-02-02",
        ]

        daily_menus = []
        for i, day in enumerate(days):
            daily_menu = DailyMenu(
                day=day,
                date=dates[i],
                lunch=DailyMeal(
                    meal_type=MealType.DEJEUNER,
                    starter=DishInfo(
                        name=f"Entrée du {day}",
                        dish_type=DishType.ENTREE,
                        description="Entrée fraîche et savoureuse",
                        seasonal_ingredients=["légumes de saison"],
                        nutritional_highlights="Riche en vitamines",
                    ),
                    main_course=DishInfo(
                        name=f"Plat principal du {day}",
                        dish_type=DishType.PLAT_PRINCIPAL,
                        description="Plat principal équilibré",
                        seasonal_ingredients=["protéines", "légumes"],
                        nutritional_highlights="Source de protéines",
                    ),
                ),
                dinner=DailyMeal(
                    meal_type=MealType.DINER,
                    starter=DishInfo(
                        name=f"Entrée du soir - {day}",
                        dish_type=DishType.ENTREE,
                        description="Entrée légère pour le dîner",
                        seasonal_ingredients=["légumes frais"],
                        nutritional_highlights="Léger et digestible",
                    ),
                    main_course=DishInfo(
                        name=f"Plat du soir - {day}",
                        dish_type=DishType.PLAT_PRINCIPAL,
                        description="Plat principal pour le dîner",
                        seasonal_ingredients=["protéines légères"],
                        nutritional_highlights="Équilibré pour le soir",
                    ),
                ),
            )
            daily_menus.append(daily_menu)

        return WeeklyMenuPlan(
            week_start_date="2025-01-27",
            season="hiver",
            daily_menus=daily_menus,
            nutritional_balance="Menu équilibré avec alternance des groupes alimentaires",
            gustative_coherence="Harmonie des saveurs et progression culinaire",
            constraints_adaptation="Menu adapté aux contraintes spécifiées",
            preferences_integration="Intégration des préférences culinaires",
        )
