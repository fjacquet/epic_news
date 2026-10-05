"""menu_plan_from_output: the crew's plan, clamped, or MenuPlanError (simplification S7)."""

import json
from types import SimpleNamespace

import pytest
from loguru import logger

from epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)
from epic_news.utils.menu_plan_validator import MenuPlanError, menu_plan_from_output

DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _dish(name: str, dish_type: DishType) -> DishInfo:
    return DishInfo(
        name=name,
        dish_type=dish_type,
        description="x",
        seasonal_ingredients=["x"],
        nutritional_highlights="y",
    )


def _meal(meal_type: MealType) -> DailyMeal:
    return DailyMeal(
        meal_type=meal_type,
        starter=_dish("Velouté", DishType.ENTREE),
        main_course=_dish("Gratin", DishType.PLAT_PRINCIPAL),
    )


def _plan(num_days: int) -> WeeklyMenuPlan:
    return WeeklyMenuPlan(
        week_start_date="2026-01-05",
        season="hiver",
        daily_menus=[
            DailyMenu(
                day=day,
                date=f"2026-01-{5 + i:02d}",
                lunch=_meal(MealType.DEJEUNER),
                dinner=_meal(MealType.DINER),
            )
            for i, day in enumerate(DAYS[:num_days])
        ],
        nutritional_balance="a",
        gustative_coherence="b",
        constraints_adaptation="c",
        preferences_integration="d",
    )


def test_typed_plan_is_returned():
    plan = _plan(2)
    assert menu_plan_from_output(SimpleNamespace(pydantic=plan, raw=""), 2) is plan


def test_typed_plan_is_clamped_with_a_warning():
    messages: list[str] = []
    sink = logger.add(messages.append, level="WARNING")
    try:
        plan = menu_plan_from_output(SimpleNamespace(pydantic=_plan(5), raw=""), 2)
    finally:
        logger.remove(sink)
    assert [d.day for d in plan.daily_menus] == ["Lundi", "Mardi"]
    assert any("5 days" in m for m in messages)


def test_raw_json_is_repaired_into_a_plan():
    raw = json.dumps(_plan(2).model_dump(mode="json"))
    plan = menu_plan_from_output(SimpleNamespace(pydantic=None, raw=raw), 2)
    assert [d.day for d in plan.daily_menus] == ["Lundi", "Mardi"]


def test_no_plan_raises():
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        menu_plan_from_output(SimpleNamespace(pydantic=None, raw="désolé, pas de menu"), 2)
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        menu_plan_from_output(SimpleNamespace(pydantic=None, raw=""), 2)
