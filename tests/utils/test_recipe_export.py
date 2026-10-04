import json
from types import SimpleNamespace

import pytest
import yaml

from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils import recipe_export

RECIPE = PaprikaRecipe(name="Risotto aux cèpes", ingredients="300 g riz\n200 g cèpes", directions="1. Cuire.")


def test_yaml_round_trips_and_keeps_french(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    recipe_export.export_recipe(RECIPE, "output/cooking/r.yaml", "output/cooking/r.json")
    text = (tmp_path / "output/cooking/r.yaml").read_text(encoding="utf-8")
    assert "Risotto aux cèpes" in text
    assert PaprikaRecipe.model_validate(yaml.safe_load(text)) == RECIPE
    assert (
        PaprikaRecipe.model_validate(json.loads((tmp_path / "output/cooking/r.json").read_text())) == RECIPE
    )


def test_refuses_paths_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        recipe_export.export_recipe(RECIPE, "../evil.yaml", "output/cooking/r.json")


def test_recipe_from_result_prefers_pydantic():
    assert recipe_export.recipe_from_result(SimpleNamespace(pydantic=RECIPE), {}) is RECIPE


def test_recipe_from_result_falls_back_to_parsing(monkeypatch):
    monkeypatch.setattr(recipe_export, "parse_crewai_output", lambda result, model, inputs: RECIPE)
    assert recipe_export.recipe_from_result(SimpleNamespace(pydantic=None, raw="{}"), {}) is RECIPE
