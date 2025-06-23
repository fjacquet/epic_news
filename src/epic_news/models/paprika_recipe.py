"""Pydantic model for Paprika 3 recipe format."""

from pydantic import BaseModel, Field


class PaprikaRecipe(BaseModel):
    """Defines the structure for a recipe compatible with Paprika 3 YAML format."""

    name: str = Field(..., description="The name of the recipe.")
    servings: str | None = Field(None, description="Number of servings the recipe yields.")
    source: str | None = Field(None, description="The original source of the recipe.")
    source_url: str | None = Field(None, description="URL for the original recipe source.")
    prep_time: str | None = Field(None, description="Preparation time.")
    cook_time: str | None = Field(None, description="Cooking time.")
    on_favorites: bool | None = Field(False, description="Whether the recipe is marked as a favorite.")
    categories: list[str] = Field(default_factory=list, description="A list of categories for the recipe.")
    nutritional_info: str | None = Field(None, description="Nutritional information.")
    difficulty: str | None = Field(None, description="Difficulty level of the recipe.")
    rating: int | None = Field(None, description="Rating of the recipe from 1 to 5.")
    notes: str | None = Field(None, description="Additional notes about the recipe.")
    ingredients: str = Field(..., description="A block of text listing all ingredients.")
    directions: str = Field(..., description="A block of text with step-by-step directions.")
