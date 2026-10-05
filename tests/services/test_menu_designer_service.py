"""Tests for MenuDesignerService: day clamping and stopping instead of a placeholder plan."""

from unittest.mock import MagicMock

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
from epic_news.services.menu_designer_service import MenuDesignerService, MenuPlanError
from epic_news.utils.interrupt import RunCancelledError
from epic_news.utils.menu_plan_validator import MenuPlanValidator


def _dish(name: str, dish_type: DishType) -> DishInfo:
    return DishInfo(
        name=name,
        dish_type=dish_type,
        description=f"Description de {name}",
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
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
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
            for i, day in enumerate(days[:num_days])
        ],
        nutritional_balance="a",
        gustative_coherence="b",
        constraints_adaptation="c",
        preferences_integration="d",
    )


def _service(kickoff) -> MenuDesignerService:
    service = MenuDesignerService()
    service.crew = MagicMock()
    service.crew.crew.return_value.kickoff = kickoff
    return service


def test_typed_plan_clamped_to_num_days():
    plan = _plan(5)
    service = _service(lambda inputs: plan)
    assert len(service._extract_menu_plan_from_result(plan, 2).daily_menus) == 2
    assert len(plan.daily_menus) == 5


def test_clamp_warns():
    messages: list[str] = []
    handler = logger.add(lambda m: messages.append(str(m)), level="WARNING")
    try:
        MenuDesignerService._clamp_days(_plan(4), 2)
    finally:
        logger.remove(handler)
    assert any("keeping the first 2" in m for m in messages)


def test_crew_exception_raises_menu_plan_error_with_cause():
    boom = RuntimeError("llm down")

    def kickoff(inputs):
        raise boom

    with pytest.raises(MenuPlanError, match="llm down") as exc_info:
        _service(kickoff).generate_menu_plan(num_days=2)
    assert exc_info.value.__cause__ is boom


def test_no_usable_output_raises_menu_plan_error():
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        _service(lambda inputs: "not json at all").generate_menu_plan(num_days=2)


def test_run_cancelled_propagates_unchanged():
    def kickoff(inputs):
        raise RunCancelledError("stop")

    with pytest.raises(RunCancelledError):
        _service(kickoff).generate_menu_plan(num_days=2)


def test_real_plan_returned():
    plan = _plan(2)
    assert _service(lambda inputs: plan).generate_menu_plan(num_days=2) is plan


def test_validator_warns_on_injected_placeholder():
    messages: list[str] = []
    handler = logger.add(lambda m: messages.append(str(m)), level="WARNING")
    try:
        MenuPlanValidator.validate_and_fix_daily_meal({}, "déjeuner", "Lundi")
    finally:
        logger.remove(handler)
    assert sum("Lundi déjeuner" in m for m in messages) == 2
