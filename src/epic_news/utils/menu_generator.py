"""
Menu generation utilities for MenuDesignerCrew workflow.
Handles recipe parsing, shopping list creation, and report generation.
"""

import datetime
from typing import Any

from loguru import logger

# logger = logging.getLogger(__name__)


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
    def parse_menu_structure(menu_structure: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Parse the *actual* menu structure returned by ``MenuDesignerCrew``.

        The crew is expected to return a JSON document (as a string **or** already
        parsed as a ``dict``) that follows the schema illustrated below::

            {
                "week_start_date": "2025-06-30",
                "season": "été",
                "daily_menus": [
                    {
                        "day": "Lundi",
                        "date": "2025-06-30",
                        "lunch": {
                            "meal_type": "déjeuner",
                            "starter": {"name": "…", "dish_type": "entrée", …},
                            "main_course": {"name": "…", "dish_type": "plat principal", …},
                            "dessert": null
                        },
                        "dinner": { … }
                    },
                    … (other days) …
                ]
            }

        This function **extracts all individual recipes** (starters, mains and
        desserts when present) and returns a list of dictionaries with the
        following keys:
            - ``name``: the *exact* recipe name (e.g. "Salade de tomates anciennes…")
            - ``type``: dish type (entrée / plat principal / dessert)
            - ``code``: deterministic short code (e.g. "LUN-L-S01") useful for
              logging & debugging (but *never* used for filenames)
            - ``day``: Day of the week ("Lundi" … "Dimanche")
            - ``meal``: "Déjeuner" or "Dîner"

        The previous implementation generated placeholder names ("Entrée Lundi…")
        which violated the user requirement for *meaningful* filenames such as
        ``coq-au-vin-de-bourgogne.html``.  By switching to real recipe names we
        guarantee that downstream components (``CookingCrew`` & co.) receive
        human-friendly topics and therefore produce correct slugs / filenames.
        """

        import json  # local import to avoid polluting module namespace at top-level

        # Accept various input forms: CrewOutput, JSON string, or dict
        if isinstance(menu_structure, str):
            try:
                data = json.loads(menu_structure)
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode menu_structure JSON: %s", exc)
                raise
        elif isinstance(menu_structure, dict):
            data = menu_structure
        else:
            # Attempt to extract JSON string from CrewOutput-like objects
            raw_content = None
            for attr in ("result", "raw", "content", "outputs"):
                if hasattr(menu_structure, attr):
                    raw_content = getattr(menu_structure, attr)
                    if raw_content:
                        break
            if raw_content is None:
                logger.error("Unsupported menu_structure type: %s", type(menu_structure))
                raise TypeError("Unsupported menu_structure input type")
            try:
                data = json.loads(raw_content if isinstance(raw_content, str) else str(raw_content))
            except json.JSONDecodeError as exc:
                logger.error("Failed to decode extracted menu_structure JSON: %s", exc)
                raise

        daily_menus = data.get("daily_menus", [])

        # Mapping helpers to build short deterministic codes
        day_codes = {
            "Lundi": "LUN",
            "Mardi": "MAR",
            "Mercredi": "MER",
            "Jeudi": "JEU",
            "Vendredi": "VEN",
            "Samedi": "SAM",
            "Dimanche": "DIM",
        }
        meal_codes = {"déjeuner": "L", "dîner": "D"}
        type_codes = {"entrée": "S", "plat principal": "M", "dessert": "D"}

        recipes: list[dict[str, Any]] = []
        counters = {("entrée",): 1, ("plat principal",): 1, ("dessert",): 1}

        for day_item in daily_menus:
            day_label = day_item.get("day")
            for meal_key in ("lunch", "dinner"):
                meal_obj = day_item.get(meal_key) or {}
                meal_label = meal_obj.get("meal_type") or ("Déjeuner" if meal_key == "lunch" else "Dîner")

                # Handle new 'dishes' array format
                dishes = meal_obj.get("dishes", [])
                if not dishes:
                    # Fallback to old format for backward compatibility
                    for dish_key in ("starter", "main_course", "dessert"):
                        dish_obj = meal_obj.get(dish_key)
                        if dish_obj is not None:
                            dishes.append(dish_obj)

                # Process all dishes in the meal
                for dish_obj in dishes:
                    if not isinstance(dish_obj, dict):
                        continue

                    dish_name: str = dish_obj.get("name", "")
                    dish_type: str = dish_obj.get("dish_type", "").lower()
                    if not dish_name or not dish_type:
                        # Skip malformed entries but warn for visibility
                        logger.warning(
                            "Skipping malformed dish entry in %s %s: %s", day_label, meal_label, dish_obj
                        )
                        continue

                    # Build short deterministic code – independent counters per dish type
                    counter = counters[(dish_type,)]
                    counters[(dish_type,)] = counter + 1
                    code = f"{day_codes.get(day_label, 'UNK')}-{meal_codes.get(meal_label.lower(), '?')}-{type_codes.get(dish_type, '?')}{counter:02d}"

                    recipes.append(
                        {
                            "name": dish_name,
                            "type": dish_type,
                            "code": code,
                            "day": day_label,
                            "meal": meal_label.capitalize(),
                        }
                    )

        logger.info("Parsed %d recipe specifications from menu structure", len(recipes))
        return recipes
