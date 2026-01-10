"""Pydantic models for menu designer output validation."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RecipeFile(BaseModel):
    """Model representing a recipe file on disk with its location and content type."""

    path: str = Field(..., description="Full path to the recipe file")
    recipe_code: str = Field(..., description="Unique recipe code (e.g., S001, M002)")
    content_type: str = Field(..., description="Type of content (yaml or html)")
    exists: bool = Field(False, description="Whether the file exists on disk")

    @field_validator("content_type")
    def content_type_must_be_valid(cls, v):  # noqa: N805
        if v not in ["yaml", "html"]:
            raise ValueError(f"Content type must be 'yaml' or 'html', got {v}")
        return v


class MenuReport(BaseModel):
    """Model representing the final menu report structure."""

    title: str = Field(..., description="Title of the menu report")
    weekly_plan: dict[str, dict[str, list[str]]] = Field(
        ..., description="Weekly meal plan structure: {day: {meal: [courses]}}"
    )
    html_content: str = Field(..., description="Full HTML content of the report")
    recipe_links: list[str] = Field(..., description="Links to individual recipe HTML files")


class ShoppingList(BaseModel):
    """Model representing the aggregated shopping list."""

    categories: dict[str, list[str]] = Field(
        ..., description="Categorized ingredients: {category: [ingredients]}"
    )
    raw_text: str = Field(..., description="Raw text version of shopping list")


class MenuOutputValidation(BaseModel):
    """Complete validation model for menu designer output."""

    recipe_files: list[RecipeFile] = Field(..., description="List of all expected recipe files")
    menu_report: MenuReport | None = Field(None, description="Final menu report structure")
    shopping_list: ShoppingList | None = Field(None, description="Aggregated shopping list")
    validation_success: bool = Field(False, description="Whether validation was successful")
    total_files: int = Field(0, description="Total number of files found")
    expected_files: int = Field(62, description="Expected number of files")
    missing_count: int = Field(0, description="Number of missing files")

    @field_validator("validation_success")
    def validate_file_counts(cls, v, values):  # noqa: N805
        """Ensure the correct number of files are present."""
        if "total_files" in values and "expected_files" in values:
            return values["total_files"] == values["expected_files"]
        return v


# Modèles pour la planification structurée du menu hebdomadaire


class MealType(str, Enum):
    """Type de repas dans la journée."""

    DEJEUNER = "déjeuner"
    DINER = "dîner"


class DishType(str, Enum):
    """Type de plat dans un repas."""

    ENTREE = "entrée"
    PLAT_PRINCIPAL = "plat principal"
    DESSERT = "dessert"


class DishInfo(BaseModel):
    """Information sur un plat individuel."""

    name: str = Field(..., description="Nom complet et attractif du plat")
    dish_type: DishType = Field(..., description="Type de plat (entrée, plat principal, dessert)")
    description: str = Field(
        ..., description="Description courte du plat incluant les ingrédients principaux"
    )
    seasonal_ingredients: list[str] = Field(..., description="Liste des ingrédients de saison utilisés")
    nutritional_highlights: str = Field(..., description="Points forts nutritionnels du plat")


class DailyMeal(BaseModel):
    """Structure d'un repas (déjeuner ou dîner)."""

    meal_type: MealType = Field(..., description="Type de repas (déjeuner ou dîner)")
    starter: DishInfo = Field(..., description="Entrée du repas")
    main_course: DishInfo = Field(..., description="Plat principal du repas")
    dessert: DishInfo | None = Field(
        None, description="Dessert du repas (uniquement pour les déjeuners weekend)"
    )


class DailyMenu(BaseModel):
    """Menu pour une journée complète."""

    day: str = Field(..., description="Jour de la semaine (ex: Lundi, Mardi, etc.)")
    date: str = Field(..., description="Date au format YYYY-MM-DD")
    lunch: DailyMeal = Field(..., description="Repas du déjeuner")
    dinner: DailyMeal = Field(..., description="Repas du dîner")


class WeeklyMenuPlan(BaseModel):
    """Structure complète du menu hebdomadaire."""

    week_start_date: str = Field(..., description="Date de début de la semaine au format YYYY-MM-DD")
    season: str = Field(..., description="Saison actuelle")
    daily_menus: list[DailyMenu] = Field(..., description="Liste des menus quotidiens")
    nutritional_balance: str = Field(
        ..., description="Explication de l'équilibre nutritionnel global du menu"
    )
    gustative_coherence: str = Field(..., description="Explication de la cohérence gustative du menu")
    constraints_adaptation: str = Field(
        ..., description="Comment le menu s'adapte aux contraintes spécifiées"
    )
    preferences_integration: str = Field(
        ..., description="Comment le menu intègre les préférences spécifiées"
    )
