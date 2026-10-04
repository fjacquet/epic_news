"""Pydantic models for menu designer output validation."""

from enum import StrEnum

from pydantic import BaseModel, Field

# Modèles pour la planification structurée du menu hebdomadaire


class MealType(StrEnum):
    """Type de repas dans la journée."""

    DEJEUNER = "déjeuner"
    DINER = "dîner"


class DishType(StrEnum):
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
