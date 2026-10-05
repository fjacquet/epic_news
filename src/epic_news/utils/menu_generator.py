"""
Menu generation utilities for MenuDesignerCrew workflow.
Handles recipe parsing, shopping list creation, and report generation.
"""

import datetime
from typing import Any

from loguru import logger

from epic_news.models.crews.menu_designer_report import DishType, MealType, WeeklyMenuPlan

_DAY_CODES = {
    "Lundi": "LUN",
    "Mardi": "MAR",
    "Mercredi": "MER",
    "Jeudi": "JEU",
    "Vendredi": "VEN",
    "Samedi": "SAM",
    "Dimanche": "DIM",
}
_MEAL_CODES = {MealType.DEJEUNER: "L", MealType.DINER: "D"}
_TYPE_CODES = {DishType.ENTREE: "S", DishType.PLAT_PRINCIPAL: "M", DishType.DESSERT: "D"}


class MenuGenerator:
    """Utilities for menu generation and recipe management."""

    @staticmethod
    def calculate_season() -> str:
        """Calculate current season based on date."""
        month = datetime.datetime.now().month
        if month in [12, 1, 2]:
            return "hiver"
        if month in [3, 4, 5]:
            return "printemps"
        if month in [6, 7, 8]:
            return "été"
        # [9, 10, 11]
        return "automne"

    @staticmethod
    def parse_menu_structure(plan: WeeklyMenuPlan) -> list[dict[str, Any]]:
        """One recipe spec per dish of the plan, in menu order.

        Each spec has the dish ``name`` and ``type``, the ``day``, the ``meal``
        ("Déjeuner"/"Dîner") and a short ``code`` such as ``LUN-L-S01``: day, meal,
        dish type and a counter per dish type across the whole menu. The code keeps
        recipe file names distinct when two dishes share a name.
        """
        counters = dict.fromkeys(DishType, 1)
        specs: list[dict[str, Any]] = []
        for day in plan.daily_menus:
            for meal in (day.lunch, day.dinner):
                for dish in (meal.starter, meal.main_course, meal.dessert):
                    if dish is None or not dish.name:
                        continue
                    number = counters[dish.dish_type]
                    counters[dish.dish_type] = number + 1
                    code = f"{_DAY_CODES.get(day.day, 'UNK')}-{_MEAL_CODES[meal.meal_type]}-{_TYPE_CODES[dish.dish_type]}{number:02d}"
                    specs.append(
                        {
                            "name": dish.name,
                            "type": dish.dish_type.value,
                            "code": code,
                            "day": day.day,
                            "meal": meal.meal_type.value.capitalize(),
                        }
                    )
        logger.info("Parsed {} recipe specifications from the menu plan", len(specs))
        return specs
