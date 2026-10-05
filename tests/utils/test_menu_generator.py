"""Tests for menu_generator utility."""

from epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)
from epic_news.utils.menu_generator import MenuGenerator


def test_calculate_season():
    """Test that the season is calculated correctly."""
    # This test is dependent on the current date, so it's not ideal.
    # A better implementation would pass the date to the function.
    # For now, we'll just test that it returns a valid season.
    assert MenuGenerator.calculate_season() in ["hiver", "printemps", "été", "automne"]


def _dish(name: str, dish_type: DishType) -> DishInfo:
    return DishInfo(
        name=name,
        dish_type=dish_type,
        description="x",
        seasonal_ingredients=["x"],
        nutritional_highlights="y",
    )


def _two_day_plan() -> WeeklyMenuPlan:
    return WeeklyMenuPlan(
        week_start_date="2026-01-05",
        season="hiver",
        daily_menus=[
            DailyMenu(
                day="Lundi",
                date="2026-01-05",
                lunch=DailyMeal(
                    meal_type=MealType.DEJEUNER,
                    starter=_dish("Velouté de potiron", DishType.ENTREE),
                    main_course=_dish("Gratin dauphinois", DishType.PLAT_PRINCIPAL),
                    dessert=_dish("Tarte aux pommes", DishType.DESSERT),
                ),
                dinner=DailyMeal(
                    meal_type=MealType.DINER,
                    starter=_dish("Salade d'endives", DishType.ENTREE),
                    main_course=_dish("Pot-au-feu", DishType.PLAT_PRINCIPAL),
                ),
            ),
            DailyMenu(
                day="Mardi",
                date="2026-01-06",
                lunch=DailyMeal(
                    meal_type=MealType.DEJEUNER,
                    starter=_dish("Soupe à l'oignon", DishType.ENTREE),
                    main_course=_dish("Hachis parmentier", DishType.PLAT_PRINCIPAL),
                ),
                dinner=DailyMeal(
                    meal_type=MealType.DINER,
                    starter=_dish("Œufs mimosa", DishType.ENTREE),
                    main_course=_dish("Blanquette de veau", DishType.PLAT_PRINCIPAL),
                    dessert=_dish("Crème brûlée", DishType.DESSERT),
                ),
            ),
        ],
        nutritional_balance="a",
        gustative_coherence="b",
        constraints_adaptation="c",
        preferences_integration="d",
    )


# Recorded from the dict-walking implementation on main d113384 with _two_day_plan().model_dump().
EXPECTED_SPECS = [
    {"name": "Velouté de potiron", "type": "entrée", "code": "LUN-L-S01", "day": "Lundi", "meal": "Déjeuner"},
    {
        "name": "Gratin dauphinois",
        "type": "plat principal",
        "code": "LUN-L-M01",
        "day": "Lundi",
        "meal": "Déjeuner",
    },
    {"name": "Tarte aux pommes", "type": "dessert", "code": "LUN-L-D01", "day": "Lundi", "meal": "Déjeuner"},
    {"name": "Salade d'endives", "type": "entrée", "code": "LUN-D-S02", "day": "Lundi", "meal": "Dîner"},
    {"name": "Pot-au-feu", "type": "plat principal", "code": "LUN-D-M02", "day": "Lundi", "meal": "Dîner"},
    {"name": "Soupe à l'oignon", "type": "entrée", "code": "MAR-L-S03", "day": "Mardi", "meal": "Déjeuner"},
    {
        "name": "Hachis parmentier",
        "type": "plat principal",
        "code": "MAR-L-M03",
        "day": "Mardi",
        "meal": "Déjeuner",
    },
    {"name": "Œufs mimosa", "type": "entrée", "code": "MAR-D-S04", "day": "Mardi", "meal": "Dîner"},
    {
        "name": "Blanquette de veau",
        "type": "plat principal",
        "code": "MAR-D-M04",
        "day": "Mardi",
        "meal": "Dîner",
    },
    {"name": "Crème brûlée", "type": "dessert", "code": "MAR-D-D02", "day": "Mardi", "meal": "Dîner"},
]


def test_specs_from_typed_plan_match_the_recorded_output():
    assert MenuGenerator.parse_menu_structure(_two_day_plan()) == EXPECTED_SPECS


def test_unknown_day_gets_unk_code():
    plan = _two_day_plan()
    plan.daily_menus[0].day = "Funday"
    assert MenuGenerator.parse_menu_structure(plan)[0]["code"] == "UNK-L-S01"


def test_empty_plan_gives_no_specs():
    plan = _two_day_plan().model_copy(update={"daily_menus": []})
    assert MenuGenerator.parse_menu_structure(plan) == []
