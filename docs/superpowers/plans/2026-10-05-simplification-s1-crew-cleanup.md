# Simplification S1 — CrewAI-Native Crew Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the `type: ignore` noise and the import-time `load_dotenv()` calls from the 24 crew modules while keeping every crew in CrewAI's documented form (`Agent(...)`, `Task(...)`, `Crew(...)` written out inside `@agent` / `@task` / `@crew`), with no change to any crew's settings.

**Architecture:** No helper layer. Each crew class declares the types CrewBase gives its attributes at runtime (`agents_config` / `tasks_config` as `dict[str, Any]`, `agents` / `tasks` as lists), which removes the `index`, `arg-type` and `attr-defined` ignores. The `call-arg` errors come from CrewAI's own typing of `Task(config=...)` and of decorated methods; they are disabled for `epic_news.crews.*` in mypy's config, because the ADR-014 AST guard (`tests/crews/test_constructor_kwargs.py`) already rejects unknown kwargs there. A characterisation snapshot of every built crew is recorded first and must stay identical.

**Tech Stack:** Python 3.13, CrewAI 1.15.23 (`crewai.project` decorators), mypy (`warn_unused_ignores = true`), pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (section S1, revised 2026-10-05: CrewAI-native form, no factory helpers). Context since the spec: efficiency wave merged (#224–#230), quality fixes (#231), menu fallback removed (#232). Survey of the crews (main at 36006ce): 24 crew modules, 57 `Agent(...)` calls, 98 `@task` methods, 344 `type: ignore` lines (call-arg 150, index 46, index+arg-type 69, attr-defined 44, assignment 6, bare 21, others), 12 crew modules call `load_dotenv()` at import.

## Global Constraints

- Every crew keeps CrewAI's documented form: `@CrewBase` class, `@agent` methods returning `Agent(config=self.agents_config[...], ...)`, `@task` methods returning `Task(config=self.tasks_config[...], ...)`, `@crew` returning `Crew(...)`. No wrapper or factory around `Agent`/`Task`/`Crew` (decision 2026-10-05).
- Behaviour preserved: no change to any agent, task or crew setting, prompt, tool or YAML file (spec Goal 4). `verbose` stays as it is today.
- `load_dotenv()` moves to the entry points only (spec S1): no crew module calls it; `main.py` keeps its call (the console scripts `kickoff` and `plot`, `api.py`, `app.py` and `scripts/*` all import `main`).
- ADR-014 guard tests (`tests/crews/test_constructor_kwargs.py`, `tests/crews/test_agent_settings_contract.py`) keep passing unchanged (spec S1).
- Goal: `type: ignore` in crews −80% (344 → at most 68) (spec Goal 3).
- Project rules: `uv` only; imports at top; Loguru; tools in Python, never in YAML; never `Agent.copy()`; never `llm_timeout=`; mypy runs with `warn_unused_ignores = true`, so every ignore your change makes unnecessary must go.
- Out of scope: `load_dotenv()` in `llm_config.py`, `mcp_config.py`, `composio_config.py`, `tools/github_tools.py` (S8); `sales_prospecting`'s literal `description=` / `expected_output=` (kept here; see Review Focus).

## Review Focus

1. A crew silently loses a setting while its lines are edited (`task_type="long"`, `max_iter=30`, `max_rpm` 30/10, `allow_delegation`, `max_retry_limit=3`, poem's `system_template`, menu's `output_file`) → the snapshot test (Task 1) fails; Tasks 2–3 run it.
2. A class-level annotation such as `agents: list[BaseAgent]` shadows what CrewBase sets at runtime and the crew builds with no agents → the snapshot test builds every crew and compares agents and tasks (Task 2).
3. Disabling `call-arg` for `epic_news.crews.*` hides an unknown kwarg on `Agent`/`Task`/`Crew` → `test_constructor_kwargs.py` (AST scan of literal calls) still catches it; Task 2 adds a test proving the scan covers the crew modules after the change.
4. A crew imported on its own (tests, `crewai` CLI) no longer sees `.env` values → every crew imports `LLMConfig`, whose module loads `.env` (S8 moves that later); Task 3 adds a subprocess test importing one crew module alone and reading `MODEL` from a temporary `.env`.
5. `sales_prospecting` passes literal `description=` / `expected_output=` next to `config=`, so its YAML prompts never apply (the defect fixed for OSINT in #231). S1 keeps it byte-for-byte and the snapshot pins it; it is reported to the user as a separate follow-up.

---

## File Structure

- Create `tests/crews/test_crew_settings_snapshot.py` and `tests/crews/snapshots/crew_settings.json` — characterisation snapshot.
- Modify `pyproject.toml` — one `[[tool.mypy.overrides]]` block for `epic_news.crews.*`.
- Modify the 24 crew modules under `src/epic_news/crews/*/` — class annotations, removed ignores, removed `load_dotenv()`.
- Create `tests/crews/test_crew_module_hygiene.py` — no `load_dotenv` in crews, AST guard coverage, standalone import reads `.env`.
- Modify `src/epic_news/crews/CLAUDE.md`, `tests/crews/_registry.py` (stale NOTE).

---

### Task 1: Characterisation snapshot of every crew

**Files:**
- Create: `tests/crews/test_crew_settings_snapshot.py`
- Create: `tests/crews/snapshots/crew_settings.json` (generated)

**Interfaces:**
- Produces: the committed snapshot JSON that Tasks 2–3 must keep identical.

- [ ] **Step 1: Write the snapshot test**

```python
# tests/crews/test_crew_settings_snapshot.py
"""Characterisation snapshot: every crew's agents, tasks and crew settings.

Simplification S1 must not change any of these. Regenerate only on purpose:
    UPDATE_CREW_SNAPSHOT=1 env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

from tests.crews._registry import ALL_CREW_CLASSES

SNAPSHOT = Path(__file__).parent / "snapshots" / "crew_settings.json"
_MCP_MODULES = ("epic_news.crews.pestel.pestel_crew", "epic_news.crews.deep_research.deep_research")


def _digest(text: object) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def _agent_settings(agent, index_of) -> dict:
    llm = agent.llm
    return {
        "id": index_of(agent),
        "role": agent.role,
        "goal": _digest(agent.goal),
        "backstory": _digest(agent.backstory),
        "model": getattr(llm, "model", None),
        "timeout": getattr(llm, "timeout", None),
        "max_iter": agent.max_iter,
        "max_rpm": agent.max_rpm,
        "max_retry_limit": agent.max_retry_limit,
        "allow_delegation": agent.allow_delegation,
        "respect_context_window": agent.respect_context_window,
        "verbose": agent.verbose,
        "system_template": _digest(agent.system_template),
        "tools": sorted(tool.name for tool in agent.tools or []),
    }


def crew_settings(crew_cls, monkeypatch) -> dict:
    # MCP servers must not change the snapshot (their tools depend on the machine).
    for module in _MCP_MODULES:
        monkeypatch.setattr(f"{module}.get_mcp_tools_or_empty", lambda crew: [])
    crew = crew_cls().crew()
    ids: dict[int, int] = {}

    def index_of(agent) -> int:
        return ids.setdefault(id(agent), len(ids))

    agents = [_agent_settings(a, index_of) for a in crew.agents]
    tasks = [
        {
            "name": t.name,
            "description": _digest(t.description),
            "expected_output": _digest(t.expected_output),
            "agent": index_of(t.agent) if t.agent is not None else None,
            "context": [c.name for c in t.context] if isinstance(t.context, list) else None,
            "async_execution": t.async_execution,
            "output_pydantic": t.output_pydantic.__name__ if t.output_pydantic else None,
            "output_file": t.output_file,
        }
        for t in crew.tasks
    ]
    return {
        "process": str(crew.process),
        "max_rpm": crew.max_rpm,
        "verbose": crew.verbose,
        "agents": agents,
        "tasks": tasks,
    }


@pytest.mark.parametrize("crew_cls", ALL_CREW_CLASSES, ids=lambda c: c.__name__)
def test_crew_settings_match_snapshot(crew_cls, monkeypatch):
    current = crew_settings(crew_cls, monkeypatch)
    stored = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if os.getenv("UPDATE_CREW_SNAPSHOT") == "1":
        stored[crew_cls.__name__] = current
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(stored, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return
    assert crew_cls.__name__ in stored, f"No snapshot for {crew_cls.__name__}; run with UPDATE_CREW_SNAPSHOT=1"
    assert current == stored[crew_cls.__name__]
```

If an attribute used above does not exist on CrewAI 1.15.23's `Agent`/`Task`/`Crew` (check with `"x" in Agent.model_fields`), drop that key — do not guess another name. If a monkeypatch target in `_MCP_MODULES` does not exist (the crew imports the helper under another name), point it at the name the module actually uses.

- [ ] **Step 2: Run it without a snapshot — it must fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py -q`
Expected: 24 failed, "No snapshot for …".

- [ ] **Step 3: Generate the snapshot from the current code, then check it is stable**

Run: `UPDATE_CREW_SNAPSHOT=1 env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py -q`
Then twice: `env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py -q` → 24 passed both times.

- [ ] **Step 4: Check the snapshot pins what matters**

In `tests/crews/snapshots/crew_settings.json` confirm: `PestelCrew` agents have the long timeout, `FinDailyCrew` has one agent with `max_iter` 30, `HolidayPlannerCrew` has crew `max_rpm` 30 and `verbose` false, `MeetingPrepCrew`/`SalesProspectingCrew` crew `max_rpm` 10, `GeospatialAnalysisCrew` and `WebPresenceCrew` researchers `max_retry_limit` 3, `NewsDailyCrew` region tasks have seven distinct agent ids, `MenuDesignerCrew` tasks keep their `output_file`. If one is missing, add the attribute to the snapshot.

- [ ] **Step 5: Commit**

```bash
git add tests/crews/test_crew_settings_snapshot.py tests/crews/snapshots/crew_settings.json
git commit -m "test(crews): snapshot every crew's agent, task and crew settings"
```

---

### Task 2: Type the CrewBase attributes; disable CrewAI's untypable call-arg in crews

**Files:**
- Modify: `pyproject.toml` (`[tool.mypy]` section)
- Modify: all 24 crew modules under `src/epic_news/crews/*/` (class header and `type: ignore` comments only)
- Create: `tests/crews/test_crew_module_hygiene.py` (first test)

**Interfaces:**
- Consumes: the snapshot (Task 1).

- [ ] **Step 1: Write the guard-coverage test**

```python
# tests/crews/test_crew_module_hygiene.py
"""Crew modules stay in CrewAI's documented form and are checked by the ADR-014 guard."""

import ast
from pathlib import Path

CREWS = Path("src/epic_news/crews")
CREW_MODULES = sorted(p for p in CREWS.rglob("*.py") if p.name != "__init__.py")


def _literal_calls(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"Agent", "Task", "Crew"}
    }


def test_every_crew_module_builds_agents_tasks_and_crews_literally():
    # mypy's call-arg check is off for epic_news.crews.* (CrewAI's Task(config=...) is untypable);
    # test_constructor_kwargs.py scans these literal calls for unknown kwargs instead.
    crew_files = [p for p in CREW_MODULES if "@CrewBase" in p.read_text(encoding="utf-8")]
    assert len(crew_files) == 24
    for path in crew_files:
        assert {"Agent", "Task", "Crew"} <= _literal_calls(path), path
```

- [ ] **Step 2: Run it** — `env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_module_hygiene.py -q` → PASS (this pins the form before and after the change; if the count is not 24, use the real count of `@CrewBase` modules and say so in the report).

- [ ] **Step 3: Disable `call-arg` for crew modules in `pyproject.toml`**

Add after the `[tool.mypy]` section:

```toml
[[tool.mypy.overrides]]
# CrewAI's documented crew form is untypable: Task(config=...) leaves description /
# expected_output to the YAML, and @agent/@task methods are DecoratedMethod objects.
# tests/crews/test_constructor_kwargs.py rejects unknown Agent/Task/Crew kwargs here instead.
module = ["epic_news.crews.*"]
disable_error_code = ["call-arg"]
```

- [ ] **Step 4: Type the CrewBase attributes in each crew class**

In each of the 24 crew classes, replace the class header

```python
@CrewBase
class TechStackCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
```

with

```python
@CrewBase
class TechStackCrew:
    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]  # CrewBase loads the YAML
    tasks_config: dict[str, Any] = "config/tasks.yaml"  # type: ignore[assignment]
    agents: list[BaseAgent]  # set by CrewBase from the @agent methods
    tasks: list[Task]  # set by CrewBase from the @task methods
```

with `from typing import Any` and `from crewai.agents.agent_builder.base_agent import BaseAgent` at the top (merge with existing imports). Keep the crew's existing config paths. If a crew already declares some of these (e.g. `CrossReferenceReportCrew` once did), keep one declaration. Do not change any `Agent(...)`, `Task(...)` or `Crew(...)` argument.

After the first crew, run `env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_settings_snapshot.py -q -k <CrewClass>` to prove the class annotations do not stop CrewBase from setting `agents` / `tasks` at runtime (Review Focus 2). If it fails, stop and report: the annotation approach does not work on this CrewAI version.

- [ ] **Step 5: Remove the ignores mypy no longer needs**

Run `uv run mypy src/epic_news`. With `warn_unused_ignores`, it lists every `type: ignore` that is now unused ("Unused 'type: ignore' comment") — remove exactly those, and narrow mixed ones (e.g. `# type: ignore[arg-type, index]` → whatever code mypy still reports on that line, or nothing). Bare `# type: ignore` (20 in company_profiler, 1 in menu_designer): remove each; if mypy then reports an error on that line, put back an ignore with the specific code. Repeat until mypy is clean. Never change code to silence mypy in this task.

- [ ] **Step 6: Verify**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews -q` (snapshot, guard tests, hygiene) → PASS.
Run: `uv run mypy src/epic_news`, `uv run ruff check src tests` → clean.
Run: `rg -c "type: ignore" src/epic_news/crews | awk -F: '{s+=$2} END {print s}'` and report the number (before: 344).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml src/epic_news/crews tests/crews/test_crew_module_hygiene.py
git commit -m "refactor(crews): type CrewBase attributes and drop unneeded type ignores"
```

---

### Task 3: Crews stop loading .env at import

**Files:**
- Modify: the 12 crew modules that call `load_dotenv()` (find them with `rg -l "load_dotenv" src/epic_news/crews`)
- Modify: `tests/crews/test_crew_module_hygiene.py` (two more tests)

**Interfaces:**
- Consumes: Task 2's hygiene test file.

- [ ] **Step 1: Add the tests**

Append to `tests/crews/test_crew_module_hygiene.py` (add `import os`, `import subprocess`, `import sys` at the top of the file):

```python
def test_no_crew_module_calls_load_dotenv():
    offenders = [str(p) for p in CREW_MODULES if "load_dotenv" in p.read_text(encoding="utf-8")]
    assert offenders == []


def test_crew_imported_alone_still_sees_dotenv(tmp_path):
    # Entry points load .env; a crew imported on its own gets it through LLMConfig's module.
    (tmp_path / ".env").write_text("MODEL=gemini/probe-model\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "MODEL"}
    code = (
        "import os\n"
        "import epic_news.crews.poem.poem_crew\n"
        "print(os.environ.get('MODEL'))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120, check=True
    )
    assert result.stdout.strip().splitlines()[-1] == "gemini/probe-model"
```

Check first how `llm_config.py` calls `load_dotenv` (it searches `.env` from the current directory upward by default — `find_dotenv` / `usecwd`). If the subprocess test cannot see the temporary `.env` because of how that call locates the file, adapt only the test's way of providing `.env` (e.g. `cwd`), not `llm_config.py`, and say so in the report.

- [ ] **Step 2: Run** — `env -u VIRTUAL_ENV uv run pytest tests/crews/test_crew_module_hygiene.py -q` → `test_no_crew_module_calls_load_dotenv` FAILS listing the 12 modules; the subprocess test passes.

- [ ] **Step 3: Remove `load_dotenv()` and its import from the 12 crew modules.** Nothing else in those files changes.

- [ ] **Step 4: Verify**

Run: `env -u VIRTUAL_ENV uv run pytest -q` (full suite, includes the snapshot), `uv run mypy src/epic_news`, `uv run ruff check .`.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/crews tests/crews/test_crew_module_hygiene.py
git commit -m "refactor(crews): load .env at the entry points, not in crew modules"
```

---

### Task 4: Docs and the numbers

**Files:**
- Modify: `src/epic_news/crews/CLAUDE.md`, `tests/crews/_registry.py` (stale NOTE)

- [ ] **Step 1: `src/epic_news/crews/CLAUDE.md`** — in the crew implementation example, show the class header from Task 2 Step 4 (typed `agents_config` / `tasks_config`, `agents` / `tasks` declarations) and add two lines: mypy's `call-arg` is off for crew modules because CrewAI's `Task(config=...)` is untypable, and `test_constructor_kwargs.py` guards kwargs instead; crew modules never call `load_dotenv()`. Keep every other rule in the file.

- [ ] **Step 2: `tests/crews/_registry.py`** — its NOTE says every crew runs sequentially; replace it with one line pointing at `ASYNC_ALLOWED` in `tests/crews/test_async_agent_isolation.py`.

- [ ] **Step 3: The numbers** — run and paste into the report:
  - `rg -c "type: ignore" src/epic_news/crews | awk -F: '{s+=$2} END {print s}'` (before 344; goal ≤ 68)
  - `rg -c "type: ignore\[call-arg\]" src/epic_news/crews | awk -F: '{s+=$2} END {print s}'` (before 150; expected 0)
  - `rg -l "load_dotenv" src/epic_news/crews | wc -l` (before 12; expected 0)
  If the total is above 68, list the remaining ignores by code and file — do not add helpers or code changes to force the number.

- [ ] **Step 4: Full verification and commit**

Run: `env -u VIRTUAL_ENV uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check src tests scripts` (only the 3 pre-existing CLAUDE.md files may be listed), `uv run mypy src/epic_news`, `uv run yamllint -s .`.

```bash
git add src/epic_news/crews/CLAUDE.md tests/crews/_registry.py
git commit -m "docs(crews): document typed CrewBase attributes and .env loading"
```

Controller: open the S1 PR with the before/after numbers and the sales_prospecting finding (Review Focus 5) as a follow-up for the user. One live run of one crew (`EPIC_ENABLE_EMAIL=false env -u VIRTUAL_ENV uv run python scripts/bench_flow.py news_daily`) before merging, since S1 touches every crew module.
