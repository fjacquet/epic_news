"""Menu Designer Service with validation and error recovery."""

from typing import Any

from crewai import CrewOutput
from loguru import logger

from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew
from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.utils.menu_days import DEFAULT_MENU_DAYS
from epic_news.utils.menu_plan_validator import MenuPlanValidator


class MenuDesignerService:
    """Service for generating weekly menu plans with validation and error recovery."""

    def __init__(self):
        """Initialize the menu designer service."""
        self.crew = MenuDesignerCrew()
        self.validator = MenuPlanValidator()
        self.used_fallback = False

    def generate_menu_plan(
        self,
        constraints: str = "",
        preferences: str = "",
        user_context: str = "",
        season: str = "hiver",
        current_date: str = "2025-01-27",
        menu_slug: str = "menu_hebdomadaire",
        num_days: int = DEFAULT_MENU_DAYS,
    ) -> WeeklyMenuPlan | None:
        """
        Generate a weekly menu plan with validation and error recovery.

        Args:
            constraints: Dietary constraints and restrictions
            preferences: Culinary preferences
            user_context: Family context and specific needs
            season: Current season for seasonal ingredients
            current_date: Current date for planning
            menu_slug: Slug for output file naming
            num_days: Number of days the menu must cover (1-7)

        Returns:
            WeeklyMenuPlan: Validated menu plan or None if generation fails
        """
        self.used_fallback = False
        try:
            logger.info("🍽️ Starting menu plan generation...")

            # Prepare inputs for the crew
            inputs = {
                "constraints": constraints,
                "preferences": preferences,
                "user_context": user_context,
                "season": season,
                "current_date": current_date,
                "menu_slug": menu_slug,
                "num_days": num_days,
            }

            # Run the crew
            logger.info("🤖 Running MenuDesigner crew...")
            result = self.crew.crew().kickoff(inputs=inputs)

            # Handle different types of crew output
            menu_plan = self._extract_menu_plan_from_result(result, num_days)

            if menu_plan:
                logger.info("✅ Menu plan generated successfully!")
                return menu_plan
            return self._fallback("no usable menu plan in the crew output", num_days)

        except Exception as e:
            return self._fallback(f"error in menu plan generation: {e}", num_days)

    def _fallback(self, reason: str, num_days: int) -> WeeklyMenuPlan:
        """Build the placeholder plan, flagging it loudly so it is never mistaken for a real one."""
        logger.error(f"menu plan fell back to placeholder dishes: {reason}")
        self.used_fallback = True
        return self.validator.create_fallback_menu_plan(num_days)

    @staticmethod
    def _clamp_days(plan: WeeklyMenuPlan, num_days: int) -> WeeklyMenuPlan:
        """Keep at most num_days days of a typed plan."""
        if len(plan.daily_menus) > num_days:
            logger.warning(f"LLM returned {len(plan.daily_menus)} days, keeping the first {num_days}")
            return plan.model_copy(update={"daily_menus": plan.daily_menus[:num_days]})
        return plan

    def _extract_menu_plan_from_result(
        self, result: Any, num_days: int = DEFAULT_MENU_DAYS
    ) -> WeeklyMenuPlan | None:
        """
        Extract and validate menu plan from crew result.

        Args:
            result: Crew execution result

        Returns:
            WeeklyMenuPlan: Validated menu plan or None
        """
        try:
            # Handle CrewOutput
            if isinstance(result, CrewOutput):
                if hasattr(result, "pydantic") and result.pydantic:
                    # Direct Pydantic model from crew
                    if isinstance(result.pydantic, WeeklyMenuPlan):
                        logger.info("✅ Got valid Pydantic model from crew")
                        return self._clamp_days(result.pydantic, num_days)
                    logger.warning("⚠️ Pydantic model is not WeeklyMenuPlan type")

                # Try to parse raw output
                if hasattr(result, "raw") and result.raw:
                    logger.info("🔍 Parsing raw crew output...")
                    return self.validator.parse_and_validate_ai_output(result.raw, num_days)

                # Try to parse JSON output
                if hasattr(result, "json") and result.json:
                    logger.info("🔍 Parsing JSON crew output...")
                    return self.validator.parse_and_validate_ai_output(result.json, num_days)

                # No valid output found in CrewOutput
                logger.warning("⚠️ No valid output found in CrewOutput")
                return None

            # Handle direct WeeklyMenuPlan
            if isinstance(result, WeeklyMenuPlan):
                logger.info("✅ Got direct WeeklyMenuPlan")
                return self._clamp_days(result, num_days)

            # Handle string output
            if isinstance(result, str):
                logger.info("🔍 Parsing string output...")
                return self.validator.parse_and_validate_ai_output(result, num_days)

            # Handle dict output
            if isinstance(result, dict):
                logger.info("🔍 Validating dict output...")
                fixed_data = self.validator.validate_and_fix_weekly_plan(result, num_days)
                try:
                    return WeeklyMenuPlan.model_validate(fixed_data)
                except Exception as e:
                    logger.error(f"❌ Failed to validate dict as WeeklyMenuPlan: {e}")
                    return None

            else:
                logger.error(f"❌ Unexpected result type: {type(result)}")
                return None

        except Exception as e:
            logger.error(f"❌ Error extracting menu plan from result: {e}")
            return None
