"""Pydantic model for Paprika recipe format."""

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

    def to_template_data(self) -> dict:
        """Convert to template-friendly dictionary format."""
        # Parse ingredients and directions into lists for better HTML rendering
        ingredients_list = [line.strip() for line in self.ingredients.split("\n") if line.strip()]

        # Try to parse directions into numbered steps
        import re

        directions_text = self.directions
        steps = re.split(r"\s*\d+\.\s+", directions_text)
        if steps and not steps[0].strip():
            steps = steps[1:]  # Remove empty first element

        if len(steps) > 1:  # If we found numbered steps
            directions_list = [step.strip() for step in steps if step.strip()]
        else:  # Otherwise split by newlines
            directions_list = [line.strip() for line in directions_text.split("\n") if line.strip()]

        return {
            "recipe_title": self.name,
            "servings": self.servings or "",
            "prep_time": self.prep_time or "",
            "cook_time": self.cook_time or "",
            "difficulty": self.difficulty or "",
            "rating": self.rating or "",
            "categories": self.categories,
            "ingredients": ingredients_list,
            "instructions": directions_list,
            "notes": self.notes or "",
            "source": self.source or "",
            "source_url": self.source_url or "",
            "nutritional_info": self.nutritional_info or "",
            "author": "Epic News AI",
        }

    @classmethod
    def from_yaml_string(cls, yaml_string: str) -> "PaprikaRecipe":
        """Create PaprikaRecipe instance from YAML string."""
        import yaml

        try:
            data = yaml.safe_load(yaml_string)
            return cls(**data)
        except (yaml.YAMLError, TypeError, ValueError):
            # Return default instance if parsing fails
            return cls(
                name="Recette",
                ingredients="",
                directions="",
            )

    @classmethod
    def from_json_string(cls, json_string: str) -> "PaprikaRecipe":
        """Create PaprikaRecipe instance from JSON string."""
        import json

        try:
            data = json.loads(json_string)
            return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Return default instance if parsing fails
            return cls(
                name="Recette",
                ingredients="",
                directions="",
            )
