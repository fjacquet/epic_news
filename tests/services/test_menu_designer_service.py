"""Tests for MenuDesignerService day clamping and fallback flagging."""

from unittest.mock import MagicMock

from loguru import logger

from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.services.menu_designer_service import MenuDesignerService
from epic_news.utils.menu_plan_validator import MenuPlanValidator


def _service(kickoff) -> MenuDesignerService:
    service = MenuDesignerService()
    service.crew = MagicMock()
    service.crew.crew.return_value.kickoff = kickoff
    return service


def test_typed_plan_clamped_to_num_days():
    plan = MenuPlanValidator.create_fallback_menu_plan(5)
    service = _service(lambda inputs: plan)
    assert len(service._extract_menu_plan_from_result(plan, 2).daily_menus) == 2
    assert len(plan.daily_menus) == 5


def test_clamp_warns():
    messages: list[str] = []
    handler = logger.add(lambda m: messages.append(str(m)), level="WARNING")
    try:
        MenuDesignerService._clamp_days(MenuPlanValidator.create_fallback_menu_plan(4), 2)
    finally:
        logger.remove(handler)
    assert any("keeping the first 2" in m for m in messages)


def test_fallback_is_flagged_and_logged_as_error():
    def boom(inputs):
        raise RuntimeError("llm down")

    messages: list[str] = []
    handler = logger.add(lambda m: messages.append(str(m)), level="ERROR")
    service = _service(boom)
    try:
        plan = service.generate_menu_plan(num_days=2)
    finally:
        logger.remove(handler)
    assert isinstance(plan, WeeklyMenuPlan)
    assert len(plan.daily_menus) == 2
    assert service.used_fallback is True
    assert any("fell back to placeholder dishes" in m for m in messages)


def test_real_plan_not_flagged():
    plan = MenuPlanValidator.create_fallback_menu_plan(2)
    service = _service(lambda inputs: plan)
    service._extract_menu_plan_from_result = lambda result, n: plan  # type: ignore[method-assign]
    service.generate_menu_plan(num_days=2)
    assert service.used_fallback is False


def test_validator_warns_on_injected_placeholder():
    messages: list[str] = []
    handler = logger.add(lambda m: messages.append(str(m)), level="WARNING")
    try:
        MenuPlanValidator.validate_and_fix_daily_meal({}, "déjeuner", "Lundi")
    finally:
        logger.remove(handler)
    assert sum("Lundi déjeuner" in m for m in messages) == 2
