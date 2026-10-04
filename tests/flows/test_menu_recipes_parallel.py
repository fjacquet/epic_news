from types import SimpleNamespace

import pytest

import epic_news.main as main_mod
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.utils.interrupt import RunCancelledError


def _spec(name):
    return {"name": name, "code": name[:3].upper(), "type": "plat", "day": "lundi", "meal": "dîner"}


def _flow():
    return main_mod.ReceptionFlow(user_request="menu")


def test_one_failing_recipe_does_not_stop_the_others(monkeypatch):
    def fake_kickoff(crew, inputs):
        if inputs["topic"] == "Soupe":
            raise RuntimeError("provider error")
        return SimpleNamespace(pydantic=PaprikaRecipe(name=inputs["topic"], ingredients="x", directions="y"))

    written = []
    monkeypatch.setattr(main_mod, "kickoff_flow", fake_kickoff)
    monkeypatch.setattr(main_mod, "export_recipe", lambda r, y, j: written.append((r.name, y, j)))
    flow = _flow()

    results = [flow._generate_menu_recipe(_spec(n)) for n in ("Risotto", "Soupe", "Tarte")]

    assert [r.name if r else None for r in results] == ["Risotto", None, "Tarte"]
    assert ("Risotto", "output/cooking/risotto.yaml", "output/cooking/risotto.json") in written


def test_cancellation_is_not_swallowed(monkeypatch):
    def cancelled(crew, inputs):
        raise RunCancelledError("Ctrl+C")

    monkeypatch.setattr(main_mod, "kickoff_flow", cancelled)
    with pytest.raises(RunCancelledError):
        _flow()._generate_menu_recipe(_spec("Risotto"))


def test_menu_recipes_use_bounded_map(monkeypatch):
    calls = {}

    def fake_bounded_map(func, items, env_var, default=3):
        calls["env_var"] = env_var
        return [func(item) for item in items]

    monkeypatch.setattr(main_mod, "bounded_map", fake_bounded_map)
    flow = _flow()
    monkeypatch.setattr(flow, "_generate_menu_recipe", lambda spec: spec["name"])
    assert flow._generate_menu_recipes([_spec("A"), _spec("B")]) == ["A", "B"]
    assert calls["env_var"] == "MENU_RECIPE_CONCURRENCY"
