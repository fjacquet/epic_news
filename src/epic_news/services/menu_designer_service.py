"""Menu Designer Service with validation and error recovery."""

import logging
from typing import Any

from crewai import CrewOutput

from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew
from epic_news.models.crews.menu_designer_report import WeeklyMenuPlan
from epic_news.utils.menu_plan_validator import MenuPlanValidator

logger = logging.getLogger(__name__)


class MenuDesignerService:
    """Service for generating weekly menu plans with validation and error recovery."""

    def __init__(self):
        """Initialize the menu designer service."""
        self.crew = MenuDesignerCrew()
        self.validator = MenuPlanValidator()

    def generate_menu_plan(
        self,
        constraints: str = "",
        preferences: str = "",
        user_context: str = "",
        season: str = "hiver",
        current_date: str = "2025-01-27",
        menu_slug: str = "menu_hebdomadaire",
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

        Returns:
            WeeklyMenuPlan: Validated menu plan or None if generation fails
        """
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
            }

            # Run the crew
            logger.info("🤖 Running MenuDesigner crew...")
            result = self.crew.crew().kickoff(inputs=inputs)

            # Handle different types of crew output
            menu_plan = self._extract_menu_plan_from_result(result)

            if menu_plan:
                logger.info("✅ Menu plan generated successfully!")
                return menu_plan
            logger.warning("⚠️ Menu plan generation failed, creating fallback...")
            return self.validator.create_fallback_menu_plan()

        except Exception as e:
            logger.error(f"❌ Error in menu plan generation: {e}")
            logger.warning("🔄 Creating fallback menu plan...")
            return self.validator.create_fallback_menu_plan()

    def _extract_menu_plan_from_result(self, result: Any) -> WeeklyMenuPlan | None:
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
                        return result.pydantic
                    logger.warning("⚠️ Pydantic model is not WeeklyMenuPlan type")

                # Try to parse raw output
                if hasattr(result, "raw") and result.raw:
                    logger.info("🔍 Parsing raw crew output...")
                    return self.validator.parse_and_validate_ai_output(result.raw)

                # Try to parse JSON output
                if hasattr(result, "json") and result.json:
                    logger.info("🔍 Parsing JSON crew output...")
                    return self.validator.parse_and_validate_ai_output(result.json)

                # No valid output found in CrewOutput
                logger.warning("⚠️ No valid output found in CrewOutput")
                return None

            # Handle direct WeeklyMenuPlan
            if isinstance(result, WeeklyMenuPlan):
                logger.info("✅ Got direct WeeklyMenuPlan")
                return result

            # Handle string output
            if isinstance(result, str):
                logger.info("🔍 Parsing string output...")
                return self.validator.parse_and_validate_ai_output(result)

            # Handle dict output
            if isinstance(result, dict):
                logger.info("🔍 Validating dict output...")
                fixed_data = self.validator.validate_and_fix_weekly_plan(result)
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

    def validate_existing_menu_plan(self, menu_data: dict[str, Any]) -> WeeklyMenuPlan | None:
        """
        Validate and fix an existing menu plan data structure.

        Args:
            menu_data: Dictionary containing menu plan data

        Returns:
            WeeklyMenuPlan: Validated menu plan or None
        """
        try:
            fixed_data = self.validator.validate_and_fix_weekly_plan(menu_data)
            return WeeklyMenuPlan.model_validate(fixed_data)
        except Exception as e:
            logger.error(f"❌ Failed to validate existing menu plan: {e}")
            return None

    def create_sample_menu_plan(self) -> WeeklyMenuPlan:
        """
        Create a sample menu plan for testing purposes.

        Returns:
            WeeklyMenuPlan: Valid sample menu plan
        """
        return self.validator.create_fallback_menu_plan()
