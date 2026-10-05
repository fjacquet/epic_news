# Simplification S7 — Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The menu step reads like the other custom steps.
- `parse_menu_structure` walks the typed `WeeklyMenuPlan` in about 25 lines (complexity 22 today).
- `MenuDesignerService` is folded into the flow, and `src/epic_news/services/` is deleted.

**Architecture:**
- **`MenuGenerator.parse_menu_structure(plan: WeeklyMenuPlan)`** iterates days → meals → dishes on the model. It drops the dict, JSON-string and CrewOutput-sniffing branches; the flow already passes `menu_plan.model_dump()` of a validated plan. The output (names, types, codes, days, meals) stays identical.
- **`menu_plan_from_output(output, num_days)` and `MenuPlanError`** move into `utils/menu_plan_validator.py`. The function returns the crew's typed plan, or the validator-repaired raw output, clamped to `num_days`, and raises `MenuPlanError` when there is no plan.
- **`generate_menu_designer`** runs `kickoff_flow(MenuDesignerCrew(), inputs)`, then `menu_plan_from_output`.

**Tech Stack:** Python 3.13, Pydantic 2, CrewAI 1.15.23, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S7; Goals 2; decisions 2, 4, 5).

Facts this plan relies on (checked on `main` at `d113384`):

- **The fallback branch is already gone.** The spec's "delete the flow's unreachable fallback branch" was done by #232 (emergency menu removed): `generate_menu_designer` re-raises `MenuPlanError`, and `tests/test_generate_menu_designer_stops.py` pins it.
- **`MenuGenerator.parse_menu_structure`** (utils/menu_generator.py:29-162) is radon D (22), the last function in `src` above 20. It:
  - accepts a str, a dict or a CrewOutput-like object;
  - reads a legacy `dishes` list;
  - counts per dish type in a dict that raises `KeyError` on an unknown type;
  - logs with a `%d` that Loguru does not format.

  Its only production caller is main.py:704, with `menu_plan.model_dump()` of a validated `WeeklyMenuPlan`. `MenuGenerator.calculate_season` is also used by `content_state.py:224` and stays.
- **The typed model** (models/crews/menu_designer_report.py): `WeeklyMenuPlan.daily_menus: list[DailyMenu]`. Each `DailyMenu` has `day: str`, `lunch` and `dinner: DailyMeal`. A `DailyMeal` has `meal_type: MealType` ("déjeuner"/"dîner"), `starter: DishInfo`, `main_course: DishInfo` and `dessert: DishInfo | None`. A `DishInfo` has `name: str` and `dish_type: DishType` ("entrée"/"plat principal"/"dessert").
- **Today's output on a typed two-day plan** (recorded on `d113384`, used below as the characterisation): ten specs, with codes `LUN-L-S01, LUN-L-M01, LUN-L-D01, LUN-D-S02, LUN-D-M02, MAR-L-S03, MAR-L-M03, MAR-D-S04, MAR-D-M04, MAR-D-D02`. Counters run per dish type across the whole menu.
- **`MenuDesignerService`** (services/menu_designer_service.py, 155 lines):
  - runs `MenuDesignerCrew().crew().kickoff(inputs=...)` directly, bypassing `kickoff_flow`'s cancel check, tracing and retry setting;
  - wraps any crew exception in `MenuPlanError`;
  - extracts the plan from `CrewOutput.pydantic` (clamped to `num_days`) or from `CrewOutput.raw` through `MenuPlanValidator.parse_and_validate_ai_output`. The str and dict branches are never used: `kickoff` returns a `CrewOutput`.
  - Users: main.py (import + one call), `tests/services/test_menu_designer_service.py`, `tests/test_generate_menu_designer_stops.py`, `tests/flows/test_all_steps_emit_docx.py:57-58`, `src/epic_news/crews/CLAUDE.md:450`.
- **The crew's inputs** are `constraints, preferences, user_context, season, current_date, menu_slug, num_days`, taken from `self.state.to_crew_inputs()` with the defaults in main.py:675-683.

## Global Constraints

- Make `parse_menu_structure` walk the typed `WeeklyMenuPlan` (≈25 lines), fold `MenuDesignerService` into the flow and remove `services/` (spec S7).
- No function above complexity 20 (radon D) in `src` (spec Goals 2).
- The menu step keeps its own `@listen` step; no generic dispatcher (decision 2). No helper layer around CrewAI `Agent`/`Task`/`Crew` (decision 5): the flow calls `kickoff_flow(MenuDesignerCrew(), inputs)`.
- No placeholder menu: when no plan is produced, the run stops (#232, decision 4).
- Recipe specs are unchanged (names, types, codes, days, meals), so recipe file names do not change.
- Project rules:
  - Use `uv` only.
  - Put imports at the top of the file.
  - Log with Loguru, using `{}` placeholders, not `%d`.
  - Use Python 3.13 union syntax.
  - Respect mypy `warn_unused_ignores`.
  - Never commit `ruff format` changes to tracked Markdown files; format only the Python files you change.
  - Use `ruff check --no-fix`.

## Review Focus

1. A day whose meal has no dessert must produce no spec for it and must not shift the dessert counter (test in Task 1, already in the characterisation: Lundi dinner has no dessert).
2. A crew output with a typed plan longer than `num_days` must be cut to `num_days`, with a warning (test in Task 2).
3. A crew output with no plan, typed or raw, must raise `MenuPlanError`, build no DOCX and generate no recipes (test in Task 2, through the flow).
4. Ctrl+C during the menu crew (`RunCancelledError`) must propagate unchanged, not wrapped in `MenuPlanError` (test in Task 2).
5. A crew exception must still stop the run. It now propagates as raised instead of being wrapped in `MenuPlanError` (test in Task 2).

---

### Task 1: `parse_menu_structure` walks the typed plan

**Files:**
- Modify: `src/epic_news/utils/menu_generator.py` (`parse_menu_structure`; module constants)
- Modify: `src/epic_news/main.py` (the call at main.py:698-704)
- Modify: `tests/utils/test_menu_generator.py` (rewrite the parse tests)

**Interfaces:**
- Produces: `MenuGenerator.parse_menu_structure(plan: WeeklyMenuPlan) -> list[dict[str, Any]]`. It returns one dict per dish with the keys `name`, `type`, `code`, `day` and `meal`, the same keys and values as today.

- [ ] **Step 1: Write the characterisation test**

Replace everything in `tests/utils/test_menu_generator.py` after `test_calculate_season` (the `sample_menu_structure` fixture and the five `test_parse_menu_structure_*` tests) with the code below. Keep `test_calculate_season`, and change the file's imports to `import pytest`-free if `pytest` is no longer used.

```python
from epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)


def _dish(name: str, dish_type: DishType) -> DishInfo:
    return DishInfo(
        name=name, dish_type=dish_type, description="x", seasonal_ingredients=["x"], nutritional_highlights="y"
    )


def _two_day_plan() -> WeeklyMenuPlan:
    return WeeklyMenuPlan(
        week_start_date="2026-01-05",
        season="hiver",
        daily_menus=[
            DailyMenu(
                day="Lundi",
                date="2026-01-05",
                lunch=DailyMeal(
                    meal_type=MealType.DEJEUNER,
                    starter=_dish("Velouté de potiron", DishType.ENTREE),
                    main_course=_dish("Gratin dauphinois", DishType.PLAT_PRINCIPAL),
                    dessert=_dish("Tarte aux pommes", DishType.DESSERT),
                ),
                dinner=DailyMeal(
                    meal_type=MealType.DINER,
                    starter=_dish("Salade d'endives", DishType.ENTREE),
                    main_course=_dish("Pot-au-feu", DishType.PLAT_PRINCIPAL),
                ),
            ),
            DailyMenu(
                day="Mardi",
                date="2026-01-06",
                lunch=DailyMeal(
                    meal_type=MealType.DEJEUNER,
                    starter=_dish("Soupe à l'oignon", DishType.ENTREE),
                    main_course=_dish("Hachis parmentier", DishType.PLAT_PRINCIPAL),
                ),
                dinner=DailyMeal(
                    meal_type=MealType.DINER,
                    starter=_dish("Œufs mimosa", DishType.ENTREE),
                    main_course=_dish("Blanquette de veau", DishType.PLAT_PRINCIPAL),
                    dessert=_dish("Crème brûlée", DishType.DESSERT),
                ),
            ),
        ],
        nutritional_balance="a",
        gustative_coherence="b",
        constraints_adaptation="c",
        preferences_integration="d",
    )


# Recorded from the dict-walking implementation on main d113384 with _two_day_plan().model_dump().
EXPECTED_SPECS = [
    {"name": "Velouté de potiron", "type": "entrée", "code": "LUN-L-S01", "day": "Lundi", "meal": "Déjeuner"},
    {"name": "Gratin dauphinois", "type": "plat principal", "code": "LUN-L-M01", "day": "Lundi", "meal": "Déjeuner"},
    {"name": "Tarte aux pommes", "type": "dessert", "code": "LUN-L-D01", "day": "Lundi", "meal": "Déjeuner"},
    {"name": "Salade d'endives", "type": "entrée", "code": "LUN-D-S02", "day": "Lundi", "meal": "Dîner"},
    {"name": "Pot-au-feu", "type": "plat principal", "code": "LUN-D-M02", "day": "Lundi", "meal": "Dîner"},
    {"name": "Soupe à l'oignon", "type": "entrée", "code": "MAR-L-S03", "day": "Mardi", "meal": "Déjeuner"},
    {"name": "Hachis parmentier", "type": "plat principal", "code": "MAR-L-M03", "day": "Mardi", "meal": "Déjeuner"},
    {"name": "Œufs mimosa", "type": "entrée", "code": "MAR-D-S04", "day": "Mardi", "meal": "Dîner"},
    {"name": "Blanquette de veau", "type": "plat principal", "code": "MAR-D-M04", "day": "Mardi", "meal": "Dîner"},
    {"name": "Crème brûlée", "type": "dessert", "code": "MAR-D-D02", "day": "Mardi", "meal": "Dîner"},
]


def test_specs_from_typed_plan_match_the_recorded_output():
    assert MenuGenerator.parse_menu_structure(_two_day_plan()) == EXPECTED_SPECS


def test_unknown_day_gets_unk_code():
    plan = _two_day_plan()
    plan.daily_menus[0].day = "Funday"
    assert MenuGenerator.parse_menu_structure(plan)[0]["code"] == "UNK-L-S01"


def test_empty_plan_gives_no_specs():
    plan = _two_day_plan().model_copy(update={"daily_menus": []})
    assert MenuGenerator.parse_menu_structure(plan) == []
```

`ruff format` will wrap the long dict lines; accept its output.

- [ ] **Step 2: Run them to see the typed call fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_menu_generator.py -q`
Expected: FAIL. Passing a `WeeklyMenuPlan` hits the "Unsupported menu_structure input type" / `TypeError` branch or `json.loads` on a non-string.

- [ ] **Step 3: Rewrite `parse_menu_structure`**

In `src/epic_news/utils/menu_generator.py`:
- add `from epic_news.models.crews.menu_designer_report import DishType, MealType, WeeklyMenuPlan` at the top;
- add the three module constants below the imports;
- replace the whole `parse_menu_structure` method with the one below.

```python
_DAY_CODES = {
    "Lundi": "LUN",
    "Mardi": "MAR",
    "Mercredi": "MER",
    "Jeudi": "JEU",
    "Vendredi": "VEN",
    "Samedi": "SAM",
    "Dimanche": "DIM",
}
_MEAL_CODES = {MealType.DEJEUNER: "L", MealType.DINER: "D"}
_TYPE_CODES = {DishType.ENTREE: "S", DishType.PLAT_PRINCIPAL: "M", DishType.DESSERT: "D"}
```

```python
    @staticmethod
    def parse_menu_structure(plan: WeeklyMenuPlan) -> list[dict[str, Any]]:
        """One recipe spec per dish of the plan, in menu order.

        Each spec has the dish ``name`` and ``type``, the ``day``, the ``meal``
        ("Déjeuner"/"Dîner") and a short ``code`` such as ``LUN-L-S01``: day, meal,
        dish type and a counter per dish type across the whole menu. The code keeps
        recipe file names distinct when two dishes share a name.
        """
        counters = dict.fromkeys(DishType, 1)
        specs: list[dict[str, Any]] = []
        for day in plan.daily_menus:
            for meal in (day.lunch, day.dinner):
                for dish in (meal.starter, meal.main_course, meal.dessert):
                    if dish is None or not dish.name:
                        continue
                    number = counters[dish.dish_type]
                    counters[dish.dish_type] = number + 1
                    code = f"{_DAY_CODES.get(day.day, 'UNK')}-{_MEAL_CODES[meal.meal_type]}-{_TYPE_CODES[dish.dish_type]}{number:02d}"
                    specs.append(
                        {
                            "name": dish.name,
                            "type": dish.dish_type.value,
                            "code": code,
                            "day": day.day,
                            "meal": meal.meal_type.value.capitalize(),
                        }
                    )
        logger.info("Parsed {} recipe specifications from the menu plan", len(specs))
        return specs
```

Remove the `json` local import and any import this leaves unused. Check that `menu_designer_report` does not import `menu_generator` (`grep -n "menu_generator" src/epic_news/models/crews/menu_designer_report.py` must print nothing), so there is no import cycle.

- [ ] **Step 4: Pass the model from the flow**

In `src/epic_news/main.py`, in `generate_menu_designer`, delete the `menu_structure_result = menu_plan.model_dump()` line and its comment, and change the call to:

```python
        recipe_specs = menu_generator.parse_menu_structure(menu_plan)
```

- [ ] **Step 5: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
uvx radon cc -s -n D src/epic_news
```
Expected: all tests pass, and ruff and mypy are clean. radon prints nothing, so no function in `src` is at D or worse (above 20). If it prints anything, report it.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/utils/menu_generator.py src/epic_news/main.py tests/utils/test_menu_generator.py
git commit -m "refactor(menu): parse_menu_structure walks the typed WeeklyMenuPlan"
```

---

### Task 2: Fold `MenuDesignerService` into the flow

**Files:**
- Modify: `src/epic_news/utils/menu_plan_validator.py` (add `MenuPlanError`, `menu_plan_from_output`)
- Modify: `src/epic_news/main.py` (`generate_menu_designer`; imports)
- Delete: `src/epic_news/services/` (whole package), `tests/services/` (whole package)
- Create: `tests/utils/test_menu_plan_from_output.py`
- Modify: `tests/test_generate_menu_designer_stops.py`, `tests/flows/test_all_steps_emit_docx.py:57-58`

**Interfaces:**
- Consumes: Task 1's `parse_menu_structure(plan: WeeklyMenuPlan)`.
- Produces:
  - `epic_news.utils.menu_plan_validator.MenuPlanError(RuntimeError)`
  - `epic_news.utils.menu_plan_validator.menu_plan_from_output(output: Any, num_days: int) -> WeeklyMenuPlan`

- [ ] **Step 1: Write the failing extraction tests**

Create `tests/utils/test_menu_plan_from_output.py`:

```python
"""menu_plan_from_output: the crew's plan, clamped, or MenuPlanError (simplification S7)."""

import json
from types import SimpleNamespace

import pytest
from loguru import logger

from epic_news.models.crews.menu_designer_report import (
    DailyMeal,
    DailyMenu,
    DishInfo,
    DishType,
    MealType,
    WeeklyMenuPlan,
)
from epic_news.utils.menu_plan_validator import MenuPlanError, menu_plan_from_output

DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _dish(name: str, dish_type: DishType) -> DishInfo:
    return DishInfo(
        name=name, dish_type=dish_type, description="x", seasonal_ingredients=["x"], nutritional_highlights="y"
    )


def _meal(meal_type: MealType) -> DailyMeal:
    return DailyMeal(
        meal_type=meal_type,
        starter=_dish("Velouté", DishType.ENTREE),
        main_course=_dish("Gratin", DishType.PLAT_PRINCIPAL),
    )


def _plan(num_days: int) -> WeeklyMenuPlan:
    return WeeklyMenuPlan(
        week_start_date="2026-01-05",
        season="hiver",
        daily_menus=[
            DailyMenu(
                day=day, date=f"2026-01-{5 + i:02d}", lunch=_meal(MealType.DEJEUNER), dinner=_meal(MealType.DINER)
            )
            for i, day in enumerate(DAYS[:num_days])
        ],
        nutritional_balance="a",
        gustative_coherence="b",
        constraints_adaptation="c",
        preferences_integration="d",
    )


def test_typed_plan_is_returned():
    plan = _plan(2)
    assert menu_plan_from_output(SimpleNamespace(pydantic=plan, raw=""), 2) is plan


def test_typed_plan_is_clamped_with_a_warning():
    messages: list[str] = []
    sink = logger.add(messages.append, level="WARNING")
    try:
        plan = menu_plan_from_output(SimpleNamespace(pydantic=_plan(5), raw=""), 2)
    finally:
        logger.remove(sink)
    assert [d.day for d in plan.daily_menus] == ["Lundi", "Mardi"]
    assert any("5 days" in m for m in messages)


def test_raw_json_is_repaired_into_a_plan():
    raw = json.dumps(_plan(2).model_dump(mode="json"))
    plan = menu_plan_from_output(SimpleNamespace(pydantic=None, raw=raw), 2)
    assert [d.day for d in plan.daily_menus] == ["Lundi", "Mardi"]


def test_no_plan_raises():
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        menu_plan_from_output(SimpleNamespace(pydantic=None, raw="désolé, pas de menu"), 2)
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        menu_plan_from_output(SimpleNamespace(pydantic=None, raw=""), 2)
```

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_menu_plan_from_output.py -q`
Expected: FAIL with `ImportError: cannot import name 'MenuPlanError' from 'epic_news.utils.menu_plan_validator'`.

- [ ] **Step 3: Add the extraction to the validator module**

Add to the end of `src/epic_news/utils/menu_plan_validator.py`, with any missing imports (`Any`, `WeeklyMenuPlan`, `logger`) at the top:

```python
class MenuPlanError(RuntimeError):
    """No real menu plan could be produced; the run must stop rather than ship placeholder dishes."""


def menu_plan_from_output(output: Any, num_days: int) -> WeeklyMenuPlan:
    """The menu crew's plan, at most ``num_days`` days long.

    Uses the crew's typed ``WeeklyMenuPlan`` when present, else repairs the raw text
    through ``MenuPlanValidator.parse_and_validate_ai_output``. Raises ``MenuPlanError``
    when neither gives a plan.
    """
    plan = getattr(output, "pydantic", None)
    if not isinstance(plan, WeeklyMenuPlan):
        raw = getattr(output, "raw", "") or ""
        plan = MenuPlanValidator.parse_and_validate_ai_output(raw, num_days) if raw else None
    if plan is None:
        raise MenuPlanError("no usable menu plan in the crew output")
    if len(plan.daily_menus) > num_days:
        logger.warning(f"LLM returned {len(plan.daily_menus)} days, keeping the first {num_days}")
        plan = plan.model_copy(update={"daily_menus": plan.daily_menus[:num_days]})
    return plan
```

Run the Step 1 tests: they PASS.

- [ ] **Step 4: Write the failing flow tests**

Replace the body of `tests/test_generate_menu_designer_stops.py` with:

```python
"""generate_menu_designer runs the menu crew through kickoff_flow and stops when it gives no plan."""

from types import SimpleNamespace

import pytest

from epic_news import main as main_module
from epic_news.main import ReceptionFlow
from epic_news.utils.interrupt import RunCancelledError
from epic_news.utils.menu_plan_validator import MenuPlanError


def _flow_with(monkeypatch, kickoff) -> tuple[ReceptionFlow, list[str]]:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "kickoff_flow", kickoff)
    monkeypatch.setattr(main_module, "emit_report", lambda *a, **k: calls.append("emit_report"))
    monkeypatch.setattr(main_module, "assemble_menu_docx", lambda *a, **k: calls.append("docx"))
    monkeypatch.setattr(
        ReceptionFlow, "_generate_menu_recipes", lambda self, specs: calls.append("recipes") or []
    )
    return ReceptionFlow(user_request="menu de la semaine"), calls


def test_no_plan_stops_the_run_and_produces_nothing(monkeypatch):
    flow, calls = _flow_with(monkeypatch, lambda crew, inputs: SimpleNamespace(pydantic=None, raw="rien"))
    with pytest.raises(MenuPlanError, match="no usable menu plan"):
        flow.generate_menu_designer()
    assert calls == []
    assert flow.state.report is None


def test_crew_error_propagates_and_produces_nothing(monkeypatch):
    def _boom(crew, inputs):
        raise RuntimeError("llm down")

    flow, calls = _flow_with(monkeypatch, _boom)
    with pytest.raises(RuntimeError, match="llm down"):
        flow.generate_menu_designer()
    assert calls == []


def test_cancel_propagates_unchanged(monkeypatch):
    def _cancel(crew, inputs):
        raise RunCancelledError("menu")

    flow, calls = _flow_with(monkeypatch, _cancel)
    with pytest.raises(RunCancelledError):
        flow.generate_menu_designer()
    assert calls == []


def test_menu_crew_runs_through_kickoff_flow_with_its_inputs(monkeypatch):
    seen: dict = {}

    def _kickoff(crew, inputs):
        seen["crew"] = type(crew).__name__
        seen["inputs"] = inputs
        return SimpleNamespace(pydantic=None, raw="")

    flow, _ = _flow_with(monkeypatch, _kickoff)
    with pytest.raises(MenuPlanError):
        flow.generate_menu_designer()
    assert seen["crew"] == "MenuDesignerCrew"
    assert set(seen["inputs"]) == {
        "constraints", "preferences", "user_context", "season", "current_date", "menu_slug", "num_days",
    }
```

If `RunCancelledError` takes no argument, construct it the way `src/epic_news/utils/interrupt.py` defines it.

In `tests/flows/test_all_steps_emit_docx.py`, replace the two `MenuDesignerService` lines (57-58) with a patch that makes the menu step get a plan:

```python
    monkeypatch.setattr(main_mod, "menu_plan_from_output", lambda output, num_days: MagicMock())
```

Keep the `MenuGenerator` patch and every assertion. The fixture's `kickoff_flow` stub already returns an output.

- [ ] **Step 5: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/test_generate_menu_designer_stops.py tests/flows/test_all_steps_emit_docx.py -q`
Expected: FAIL. The flow still calls `MenuDesignerService`, which never calls the patched `kickoff_flow`, and `main` has no `menu_plan_from_output`.

- [ ] **Step 6: Fold the service into the step**

In `src/epic_news/main.py`:
- Imports: replace `from epic_news.services.menu_designer_service import MenuDesignerService, MenuPlanError` with `from epic_news.crews.menu_designer.menu_designer import MenuDesignerCrew` (if not already imported) and `from epic_news.utils.menu_plan_validator import MenuPlanError, menu_plan_from_output`.
- In `generate_menu_designer`, replace the `try: menu_plan = MenuDesignerService().generate_menu_plan(...) except MenuPlanError ...` block with:

```python
        menu_inputs = {
            "constraints": crew_inputs.get("constraints", ""),
            "preferences": crew_inputs.get("preferences", ""),
            "user_context": crew_inputs.get("user_context", ""),
            "season": crew_inputs.get("season", "hiver"),
            "current_date": crew_inputs.get("current_date", "2025-01-27"),
            "menu_slug": crew_inputs.get("menu_slug", "menu_hebdomadaire"),
            "num_days": crew_inputs.get("num_days", DEFAULT_MENU_DAYS),
        }
        output = kickoff_flow(MenuDesignerCrew(), menu_inputs)
        try:
            menu_plan = menu_plan_from_output(output, menu_inputs["num_days"])
        except MenuPlanError as e:
            # No placeholder menu: stop the run so no report, recipes or email go out.
            self.logger.error(f"❌ Menu plan could not be produced, stopping the run: {e}")
            raise
```

Keep the rest of the step unchanged: the docx, `state.report`, recipe generation and `output_file` restore.

- [ ] **Step 7: Delete the service and its tests**

```bash
git rm -r src/epic_news/services tests/services
grep -rnE "services\.menu_designer_service|MenuDesignerService" src tests scripts
```

Expected: the grep prints nothing. The deleted `tests/services/test_menu_designer_service.py` covered:
- clamp: now `test_typed_plan_is_clamped_with_a_warning`;
- exception: now `test_crew_error_propagates...`;
- no plan: now `test_no_plan_raises` and `test_no_plan_stops_the_run...`;
- cancel: now `test_cancel_propagates_unchanged`;
- real plan: now `test_typed_plan_is_returned`;
- the validator placeholder check.

If that last test (`test_validator_warns_on_injected_placeholder`, which calls `MenuPlanValidator.validate_and_fix_daily_meal`) has no equivalent in `tests/utils/test_menu_plan_validator.py`, move it there unchanged and say so.

- [ ] **Step 8: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
uvx radon cc -s -n D src/epic_news
wc -l src/epic_news/main.py
```
Expected: all tests pass, ruff and mypy are clean, and radon prints nothing. Report the `main.py` line count (it was 1,340).

- [ ] **Step 9: Commit**

```bash
git add -A src/epic_news tests
git commit -m "refactor(menu): fold MenuDesignerService into the flow; remove services/"
```

---

### Task 3: Docs

**Files:**
- Modify: `src/epic_news/crews/CLAUDE.md:450` (it names `services/menu_designer_service.py`)
- Modify: `src/epic_news/utils/CLAUDE.md` (the `menu_generator.py` / `menu_plan_validator.py` tree lines: add `menu_plan_from_output`, `MenuPlanError`)
- Modify: `docs/explanations/architecture.md` and root `CLAUDE.md` only where they name `services/` or `MenuDesignerService`

**Interfaces:**
- Consumes: Tasks 1-2 (`parse_menu_structure(plan)`, `menu_plan_from_output`, `MenuPlanError` in `utils/menu_plan_validator.py`; the menu crew runs through `kickoff_flow`; `services/` gone).

- [ ] **Step 1: Find stale statements**

```bash
grep -rnE "services/|MenuDesignerService|menu_designer_service|parse_menu_structure" CLAUDE.md src/epic_news/*/CLAUDE.md docs/explanations docs/reference docs/how-to docs/tutorials README.md
```

List the hits in your report. Leave historical docs (`docs/superpowers/`, `docs/archive/`, `TODO.md`, `CHANGELOG.md`) alone.

- [ ] **Step 2: Rewrite each hit** to say what is true after Tasks 1-2. The menu step runs `MenuDesignerCrew` through `kickoff_flow`, gets the plan from `menu_plan_from_output` (which raises `MenuPlanError` when there is none), builds the DOCX, then turns `parse_menu_structure(plan)` into one `CookingCrew` run per dish. Edit only the wrong sentences.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md src/epic_news docs
git commit -m "docs: menu step without MenuDesignerService (S7)"
```

Do not stage `docs/audits/` (untracked, must stay out of git). Do not run `ruff format .`.

---

Controller, before the PR: live menu run with `EPIC_ENABLE_EMAIL=false` (`env -u VIRTUAL_ENV uv run python scripts/bench_flow.py menu`). Compare it with the E3 menu run (175.9 s, 28/28 recipes, in `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md`): the plan DOCX opens, the recipe count matches the plan's dishes, and the recipe file names carry real dish names with their codes. Report the radon result (nothing at D or worse in `src`) against spec Goal 2.
