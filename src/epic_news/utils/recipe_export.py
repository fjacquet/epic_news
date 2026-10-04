"""Write a PaprikaRecipe as Paprika YAML and JSON (deterministic, no LLM)."""

from pathlib import Path
from typing import Any

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.diagnostics import parse_crewai_output


def recipe_from_result(result: Any, inputs: dict[str, Any]) -> PaprikaRecipe:
    """The crew's PaprikaRecipe output, or a parsed one when output_pydantic is missing."""
    model = getattr(result, "pydantic", None)
    if isinstance(model, PaprikaRecipe):
        return model
    return parse_crewai_output(result, PaprikaRecipe, inputs)


def export_recipe(recipe: PaprikaRecipe, yaml_path: str, json_path: str) -> None:
    """Write both exports; refuse any path outside output/ (ADR-015)."""
    root = Path("output").resolve()
    targets = ((yaml_path, recipe.to_paprika_yaml()), (json_path, recipe.model_dump_json(indent=2)))
    for path, _ in targets:
        if not Path(path).resolve().is_relative_to(root):
            raise ValueError(f"Refusing to write recipe outside output/: {path}")
    for path, text in targets:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
