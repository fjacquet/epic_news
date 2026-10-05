# Simplification S8 — Small Consolidations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three Python consolidations from spec S8:
- `kickoff_flow` and `akickoff_flow` share one retry/trace helper.
- The CrewAI monkeypatches leave `llm_config.py` for `config/crewai_patches.py`. They are applied once by the flow entry point and documented for CrewAI upgrades.
- `observability.py` keeps only what the flow uses.

**Architecture:**
- **`utils/flow_enforcement.py`:** the per-attempt preparation and the retry decision become two shared helpers. The sync and async entry points keep only their kickoff call and their sleep.
- **New `config/crewai_patches.py`:** holds every class patch, the empty-response retry and the LLM slot cap now in `llm_config.py` (lines 29-495), behind an idempotent `apply_crewai_patches()`. `epic_news.main` calls it at import time, and every runtime path (`crewai flow kickoff`, the API, Streamlit, the bench scripts) imports `epic_news.main`. `llm_config.py` keeps `LLMConfig` and its own constants.
- **`utils/observability.py`:** keeps `TraceEvent`, `Tracer` and `trace_task`, and teaches `trace_task` to trace `async def` steps. `Dashboard`, `HallucinationGuard`, `monitor_agent`, `guard_output` and `get_observability_tools` go.

**Tech Stack:** Python 3.13, CrewAI 1.15.23, LiteLLM, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-10-04-simplification-wave-design.md` (S8 Python part; decision 3). The infra part (compose files, Makefile aliases) is a separate PR, out of scope here.

## Facts this plan relies on

Checked on `main` at `3d43cde`.

**`flow_enforcement.py` (248 lines)**
- `kickoff_flow` (lines 112-178) and `akickoff_flow` (181-248) are line-for-line copies, apart from three things: `crew.kickoff` / `await crew.akickoff`, `time.sleep` / `await asyncio.sleep`, and the span and log names (`"kickoff_flow"` / `"akickoff_flow"`, "Kicking off" / "Async kicking off").
- Tests: `tests/utils/test_flow_enforcement_retry.py` covers both entry points.

**`llm_config.py` (700 lines)**
- `LLMConfig` (line 498 to end) uses only `_DEFAULT_MODEL`, `_DEFAULT_OPENROUTER_BASE_URL`, `_LITELLM_NUM_RETRIES` and `_GEMINI3_DEFAULT_REASONING_EFFORT`, plus its own methods.
- Lines 29-495 are the patch machinery:
  - empty-response retry (`_DEFAULT_EMPTY_RETRIES`, `_sleep`, `_async_sleep`, `_call_with_empty_retry`, …);
  - the LLM slot cap (`_llm_slots`, `_holds_slot`, `_with_llm_slot`, `_awith_llm_slot`, `_reset_llm_slots`, …);
  - tool-call coercion (`_coerce_tool_calls_to_react_text`, …);
  - `_patch_anthropic_detection_for_openrouter`;
  - the ReAct patches (`_wrap_call_for_react_safety`, `_apply_react_patches*`, `_force_react_tool_calling`).
- Two calls at import time apply the patches (lines 494-495). Flags marking a patched class: `LLM._openrouter_anthropic_patched`, `BaseLLM/LLM._react_tool_calling_forced`, `BaseLLM/LLM._retry_on_empty_patched`.
- Tests importing these private names:
  - `tests/config/test_llm_concurrency_cap.py`: `llm_config._reset_llm_slots`, `_with_llm_slot`, `_awith_llm_slot`, `_slots`, `_holds_slot`, `_wrap_call_for_react_safety`;
  - `tests/config/test_llm_config_tool_call_coercion.py`;
  - `tests/config/test_llm_config_empty_retry.py`;
  - `tests/config/test_llm_config_tool_calling.py`, which checks the patched behaviour.

**`observability.py` (524 lines)**
- Users: `main.py:95,115-118,226-228` and `crews/company_news/company_news_crew.py:10,15-18,61-63,118,136,154`, both through `get_observability_tools(...)`. They use the tracer only through `@trace_task(tracer)`. `self.dashboard` and `self.hallucination_guard` are assigned and never read.
- `trace_task` is a sync wrapper. On the `async def` flow steps (`generate_rss_weekly`, `generate_osint`) it returns the coroutine at once and records `task_end` with `success=True` and `result_type="coroutine"` before the step has run.
- Tests: `tests/utils/test_observability.py`.

## Global Constraints

- `kickoff_flow` / `akickoff_flow` share one retry/trace helper (spec S8).
- CrewAI monkeypatches move from `llm_config.py` to `config/crewai_patches.py`, applied once at the entry points, with a docstring listing what to re-check on each CrewAI upgrade (spec S8).
- `observability.py`: keep only what the flow uses (`trace_task` or its replacement); delete unused Tracer/Dashboard/HallucinationGuard (not used outside this repo) (spec S8, decision 3). `Tracer` stays, because `trace_task` writes through it.
- Behaviour preserved: the patches, retry policy, log text and trace events stay identical, except that `trace_task` now records async steps correctly (spec Goals 4).
- No helper layer around CrewAI `Agent`/`Task`/`Crew` (decision 5).
- Project rules:
  - `uv` only;
  - imports at the top of the file;
  - Loguru;
  - Python 3.13 union syntax;
  - mypy `warn_unused_ignores`;
  - `ruff check --no-fix`;
  - never commit `ruff format` changes to tracked Markdown, so format only the Python files you change.

## Review Focus

1. A Streamlit, API or `crewai flow kickoff` run must run with the patches applied. Each one imports `epic_news.main`, and a test asserts the patch flags after that import (test in Task 2).
2. Calling `apply_crewai_patches()` twice must not wrap `LLM.call` twice, which would double the empty retries and take two slots (test in Task 2).
3. A non-transient error on attempt 1 of 3 must fail at once with the same error log, in both the sync and async versions (existing tests in `test_flow_enforcement_retry.py`, plus a parity test in Task 1).
4. Ctrl+C between retries must stop the next attempt in both versions (test in Task 1).
5. An `async def` flow step that raises must record `task_error`, and one that succeeds must record `task_end` with `success=True` only after it has finished (test in Task 3).

---

### Task 1: One retry/trace path for `kickoff_flow` and `akickoff_flow`

**Files:**
- Modify: `src/epic_news/utils/flow_enforcement.py`
- Modify: `tests/utils/test_flow_enforcement_retry.py` (add tests)

**Interfaces:**
- Produces: these private helpers in `flow_enforcement.py`. The signatures of `kickoff_flow(crew_or_factory, context)` and `akickoff_flow(crew_or_factory, context)` do not change.
  - `_prepare_attempt(crew_or_factory: Any, crew_name: str, attempt: int, attempts: int, method: str) -> Any` — raises if cancelled, builds the crew and checks that it has `method`.
  - `_retry_delay(exc: Exception, crew_name: str, attempt: int, attempts: int, backoff: float, start: float) -> float | None` — logs the warning and returns the delay for a retry, or logs the error and returns `None`.

- [ ] **Step 1: Write the parity tests**

Add to `tests/utils/test_flow_enforcement_retry.py`, reusing that file's existing crew stand-ins and its `CREW_KICKOFF_ATTEMPTS` / `CREW_KICKOFF_BACKOFF_SECONDS` setup. Read the file first and use its fixture and class names.

```python
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_cancel_between_attempts_stops_the_next_one(monkeypatch, use_async):
    """Ctrl+C after a transient failure stops the retry, sync and async alike."""
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "3")
    monkeypatch.setenv("CREW_KICKOFF_BACKOFF_SECONDS", "0")
    calls: list[int] = []

    def _fail_then_cancel(*_a, **_k):
        calls.append(1)
        request_cancel()  # the user presses Ctrl+C while the first attempt fails
        raise RuntimeError("503 service unavailable")

    crew = _crew_raising(_fail_then_cancel, use_async)
    with pytest.raises(RunCancelledError):
        if use_async:
            asyncio.run(akickoff_flow(crew, {"topic": "x"}))
        else:
            kickoff_flow(crew, {"topic": "x"})
    assert calls == [1]


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_non_transient_error_fails_on_the_first_attempt(monkeypatch, use_async, caplog_loguru):
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "3")
    calls: list[int] = []

    def _bad_config(*_a, **_k):
        calls.append(1)
        raise ValueError("missing template variable")

    crew = _crew_raising(_bad_config, use_async)
    with pytest.raises(ValueError, match="missing template variable"):
        if use_async:
            asyncio.run(akickoff_flow(crew, {"topic": "x"}))
        else:
            kickoff_flow(crew, {"topic": "x"})
    assert calls == [1]
    assert any("failed after" in m and "attempt 1/3" in m for m in caplog_loguru)
```

Wire these to the real helpers:
- `request_cancel`: the function in `src/epic_news/utils/interrupt.py` that sets the cancel flag (`grep -n "^def " src/epic_news/utils/interrupt.py`), with whatever the existing tests use to reset it afterwards.
- `_crew_raising(fn, use_async)`: an object whose `kickoff` (sync) or `akickoff` (async) calls `fn`.
- `caplog_loguru`: a list of Loguru messages, captured the way other tests in the repo do (`logger.add(list.append)` / `logger.remove`).

If one of these does not exist, write it at the top of this test file.

- [ ] **Step 2: Run them**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_flow_enforcement_retry.py -q`
Expected: PASS. These pin today's behaviour before the refactor; if one fails, report it before changing the code.

- [ ] **Step 3: Extract the shared helpers**

In `src/epic_news/utils/flow_enforcement.py`, add these two helpers below `_log_run_usage`:

```python
def _prepare_attempt(crew_or_factory: Any, crew_name: str, attempt: int, attempts: int, method: str) -> Any:
    """Stop if the run was cancelled, then build a fresh crew that supports ``method``.

    A Ctrl+C cannot interrupt a crew already in flight, but it must stop the next
    attempt from starting. The crew is rebuilt each attempt: a Crew carries per-run
    task state that is not safe to replay after a mid-run failure.
    """
    raise_if_cancelled(f"crew {crew_name} (attempt {attempt}/{attempts})")
    crew = _get_crew_instance(crew_or_factory)
    if not hasattr(crew, method):
        raise AttributeError(f"Object {crew!r} does not support {method}()")
    return crew


def _retry_delay(
    exc: Exception, crew_name: str, attempt: int, attempts: int, backoff: float, start: float
) -> float | None:
    """Seconds to wait before retrying ``exc``, or None when the caller must re-raise it."""
    elapsed = time.perf_counter() - start
    if attempt < attempts and _is_transient_error(exc):
        delay = backoff * (2 ** (attempt - 1))
        logger.warning(
            "⚠️ Crew {} hit a transient provider error on attempt {}/{} after {:.2f}s; "
            "retrying in {:.1f}s. Error: {}",
            crew_name,
            attempt,
            attempts,
            elapsed,
            delay,
            exc,
        )
        return delay
    logger.error(
        "❌ Crew {} failed after {:.2f}s on attempt {}/{}: {}", crew_name, elapsed, attempt, attempts, exc
    )
    return None
```

Replace the loop body of `kickoff_flow` (everything inside `for attempt in range(1, attempts + 1):`) with:

```python
            crew = _prepare_attempt(crew_or_factory, crew_name, attempt, attempts, "kickoff")
            try:
                result = crew.kickoff(inputs=context)
            except Exception as exc:
                delay = _retry_delay(exc, crew_name, attempt, attempts, backoff, start)
                if delay is None:
                    raise
                time.sleep(delay)
                continue
            _log_run_usage(crew_name, time.perf_counter() - start, result)
            return result
```

Replace the loop body of `akickoff_flow` with:

```python
            crew = _prepare_attempt(crew_or_factory, crew_name, attempt, attempts, "akickoff")
            try:
                result = await crew.akickoff(inputs=context)
            except Exception as exc:
                delay = _retry_delay(exc, crew_name, attempt, attempts, backoff, start)
                if delay is None:
                    raise
                await asyncio.sleep(delay)
                continue
            _log_run_usage(crew_name, time.perf_counter() - start, result)
            return result
```

Keep both functions' docstrings, their `context` check, their `trace_span(...)` names and their opening log lines exactly as they are.

- [ ] **Step 4: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
wc -l src/epic_news/utils/flow_enforcement.py
```
Expected: everything passes and both checks are clean. Report the line count (it was 248).

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/flow_enforcement.py tests/utils/test_flow_enforcement_retry.py
git commit -m "refactor(flow): kickoff_flow and akickoff_flow share one retry path"
```

---

### Task 2: CrewAI patches in `config/crewai_patches.py`, applied once by the flow

**Files:**
- Create: `src/epic_news/config/crewai_patches.py`
- Modify: `src/epic_news/config/llm_config.py` (remove lines 29-495 and the imports that only they used)
- Modify: `src/epic_news/main.py` (call `apply_crewai_patches()` after the imports)
- Modify: `tests/config/test_llm_concurrency_cap.py`, `tests/config/test_llm_config_tool_call_coercion.py`, `tests/config/test_llm_config_empty_retry.py`, `tests/config/test_llm_config_tool_calling.py` (import from `crewai_patches`; apply the patches where needed)
- Create: `tests/config/test_crewai_patches_applied.py`

**Interfaces:**
- Produces: `epic_news.config.crewai_patches.apply_crewai_patches() -> None`, which is idempotent. The private names that moved keep their names, now in `crewai_patches`. `LLMConfig` and its public methods keep their module and behaviour.

- [ ] **Step 1: Write the failing tests**

Create `tests/config/test_crewai_patches_applied.py`:

```python
"""CrewAI patches live in crewai_patches, are applied by the flow entry point, and apply once."""

import importlib

from crewai import LLM
from crewai.llms.base_llm import BaseLLM

from epic_news.config import crewai_patches


def test_importing_the_flow_applies_the_patches():
    importlib.import_module("epic_news.main")
    assert getattr(LLM, "_openrouter_anthropic_patched", False)
    assert getattr(BaseLLM, "_react_tool_calling_forced", False)
    assert getattr(BaseLLM, "_retry_on_empty_patched", False)


def test_apply_is_idempotent():
    crewai_patches.apply_crewai_patches()
    call_once = LLM.call
    acall_once = getattr(LLM, "acall", None)
    crewai_patches.apply_crewai_patches()
    assert LLM.call is call_once
    assert getattr(LLM, "acall", None) is acall_once


def test_llm_config_no_longer_holds_patches():
    from epic_news.config import llm_config

    for name in ("_with_llm_slot", "_call_with_empty_retry", "_wrap_call_for_react_safety", "_force_react_tool_calling"):
        assert not hasattr(llm_config, name), name
```

In the four existing `tests/config/` files, change the imports and the module references for the moved names to `epic_news.config.crewai_patches` (`llm_config._with_llm_slot` becomes `crewai_patches._with_llm_slot`, and so on). A test that checks patched behaviour (for example `supports_function_calling()` returning False, or a wrapped `call`) must call `crewai_patches.apply_crewai_patches()` first, in a module-level fixture.

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/config -q`
Expected: FAIL with `ImportError: cannot import name 'crewai_patches'`.

- [ ] **Step 3: Move the patch code**

Create `src/epic_news/config/crewai_patches.py`:
1. Start with the module docstring below.
2. Add the imports the moved code needs (`asyncio`, `contextvars`, `json`, `os`, `random`, `threading`, `time`, `Awaitable`, `Callable`, `Any`, `LLM`, `BaseLLM`, `logger`; keep only those used).
3. Move every definition from `llm_config.py` lines 29-495 verbatim. That runs from the `# Re-issues of an identical call...` comment and `_DEFAULT_EMPTY_RETRIES` through the end of `_force_react_tool_calling`. Keep the order and the comments.
4. Do **not** move the two module-level calls (`_patch_anthropic_detection_for_openrouter()` / `_force_react_tool_calling()`). Replace them with:

```python
def apply_crewai_patches() -> None:
    """Install every patch on CrewAI's LLM classes. Safe to call more than once."""
    _patch_anthropic_detection_for_openrouter()
    _force_react_tool_calling()
```

Read both functions before trusting this. Each one already returns early when its flag (`_openrouter_anthropic_patched`, `_react_tool_calling_forced`) is set. If either does not, add that guard at its top using its existing flag, and say so in your report.

The module docstring:

```python
"""Runtime patches to CrewAI 1.15.23's LLM classes, applied once by ``epic_news.main``.

What they do:
- Anthropic detection: OpenRouter model ids such as ``openrouter/anthropic/...`` are not
  sent down CrewAI's native Anthropic path (``_patch_anthropic_detection_for_openrouter``).
- ReAct tool calling: every ``BaseLLM`` subclass reports no native function calling, so
  agents use the ReAct text protocol; tool-call responses are coerced to ReAct text
  (``_force_react_tool_calling``, ``_wrap_call_for_react_safety``,
  ``_coerce_tool_calls_to_react_text``).
- Empty responses: an identical call that came back empty is re-issued with backoff
  (``LLM_EMPTY_RETRIES``, ``_call_with_empty_retry``).
- Concurrency: every LLM call holds one of ``LLM_MAX_CONCURRENCY`` process-wide slots,
  waiting at most ``LLM_SLOT_WAIT_SECONDS`` (``_with_llm_slot`` / ``_awith_llm_slot``).

Re-check on every CrewAI upgrade:
- ``crewai.LLM`` still has ``call``/``acall`` and the attribute
  ``_patch_anthropic_detection_for_openrouter`` replaces (see that function).
- ``BaseLLM.supports_function_calling`` still decides between native tools and ReAct.
- ``BaseLLM.__init_subclass__`` still runs for provider classes created at import time.
- The tests in ``tests/config/`` (tool calling, coercion, empty retry, concurrency cap)
  still pass against the new version.
"""
```

Read the moved code before writing each bullet. If a name in the docstring differs from the code (for example the env var of the empty retry), use the code's name.

In `llm_config.py`, delete the moved lines and the two calls. Remove the imports that only the moved code used (ruff F401 will tell you). Keep `load_dotenv()`, `_DEFAULT_MODEL`, `_DEFAULT_OPENROUTER_BASE_URL`, `_LITELLM_NUM_RETRIES`, `_GEMINI3_DEFAULT_REASONING_EFFORT` and `LLMConfig`.

- [ ] **Step 4: Apply once in the flow entry module**

In `src/epic_news/main.py`, import `from epic_news.config.crewai_patches import apply_crewai_patches` with the other imports, and call it once at module level, right after `load_dotenv()` (main.py:112):

```python
load_dotenv()
apply_crewai_patches()  # CrewAI LLM patches (see config/crewai_patches.py); every runtime path imports this module
```

Then confirm that every runtime entry imports `epic_news.main`: `grep -n "epic_news.main\|from epic_news import main" src/epic_news/api.py src/epic_news/app.py scripts/*.py pyproject.toml`. The `kickoff` script entry in `pyproject.toml` must point into `epic_news.main`. List each entry in your report. Any runtime entry that does not import `epic_news.main` must call `apply_crewai_patches()` itself; add that call.

- [ ] **Step 5: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
wc -l src/epic_news/config/llm_config.py src/epic_news/config/crewai_patches.py
```
Expected: all tests pass, and ruff and mypy are clean. Report both line counts; `llm_config.py` was 700.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/config/crewai_patches.py src/epic_news/config/llm_config.py src/epic_news/main.py tests/config
git commit -m "refactor(config): CrewAI patches move to crewai_patches, applied once by the flow"
```

---

### Task 3: `observability.py` keeps what the flow uses

**Files:**
- Modify: `src/epic_news/utils/observability.py` (delete `HallucinationGuard`, `Dashboard`, `monitor_agent`, `guard_output`, `get_observability_tools`; make `trace_task` async-aware)
- Modify: `src/epic_news/main.py:95,114-118,226-228`, `src/epic_news/crews/company_news/company_news_crew.py:10,14-18,61-63`
- Modify: `tests/utils/test_observability.py`

**Interfaces:**
- Produces: `epic_news.utils.observability` exports `TraceEvent`, `Tracer` and `trace_task(tracer: Tracer)`. `trace_task` wraps both sync and `async def` functions. Callers build their tracer with `Tracer(f"<name>_{int(time.time())}")`, the trace id `get_observability_tools` used.

- [ ] **Step 1: Write the failing async tests**

In `tests/utils/test_observability.py`:
1. Delete the tests of the removed classes and functions (`HallucinationGuard`, `Dashboard`, `get_observability_tools`, `monitor_agent`, `guard_output`), and list them in your report.
2. Keep the `Tracer`, `TraceEvent` and sync `trace_task` tests unchanged.
3. Add the tests below, using the same `tmp_path`/`monkeypatch.chdir` setup as the existing `test_trace_task_decorator_success`:

```python
def test_trace_task_records_an_async_step_after_it_finishes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracer = Tracer(trace_id="async_success_test")
    finished: list[bool] = []

    @trace_task(tracer)
    async def step():
        await asyncio.sleep(0)
        finished.append(True)
        return {"ok": True}

    assert asyncio.run(step()) == {"ok": True}
    end = tracer.get_events(event_type="task_end")[-1]
    assert finished == [True]
    assert end.details["success"] is True
    assert end.details["result_type"] == "dict"


def test_trace_task_records_an_async_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracer = Tracer(trace_id="async_error_test")

    @trace_task(tracer)
    async def step():
        raise RuntimeError("osint failed")

    with pytest.raises(RuntimeError, match="osint failed"):
        asyncio.run(step())
    assert tracer.get_events(event_type="task_error")[-1].details["error"] == "osint failed"
    assert tracer.get_events(event_type="task_end")[-1].details["success"] is False


def test_unused_tools_are_gone():
    import epic_news.utils.observability as observability

    for name in ("Dashboard", "HallucinationGuard", "monitor_agent", "guard_output", "get_observability_tools"):
        assert not hasattr(observability, name), name
```

Add `import asyncio` (and `import pytest`, if missing) at the top. Check that `Tracer.get_events` returns `TraceEvent` objects with `.details` (observability.py:129). If it returns dicts, index them as dicts instead.

- [ ] **Step 2: Run them to see them fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_observability.py -q`
Expected: FAIL. The async step's `task_end` has `result_type == "coroutine"`, no `task_error` is recorded, and the removed names still exist.

- [ ] **Step 3: Trim the module and make `trace_task` async-aware**

In `src/epic_news/utils/observability.py`:
- Delete `HallucinationGuard`, `Dashboard`, `monitor_agent`, `guard_output` and `get_observability_tools`, and every import only they used.
- Update the module docstring to describe what remains.
- Replace `trace_task` with:

```python
def trace_task(tracer: Tracer):
    """Record ``task_start`` / ``task_error`` / ``task_end`` events around a flow step.

    Works for plain and ``async def`` steps; an async step is recorded when it
    finishes, not when its coroutine is created.
    """

    def decorator(func):
        task_name = func.__name__

        def _start(args, kwargs) -> float:
            details = {"task_name": task_name, "args": str(args), "kwargs": str(kwargs)}
            tracer.add_event(TraceEvent("task_start", f"task:{task_name}", details))
            return time.time()

        def _end(start: float, result: Any, error: Exception | None) -> None:
            if error is not None:
                details = {"task_name": task_name, "error": str(error)}
                tracer.add_event(TraceEvent("task_error", f"task:{task_name}", details))
            end_details = {
                "task_name": task_name,
                "duration": time.time() - start,
                "success": error is None,
                "result_type": type(result).__name__ if error is None else None,
            }
            tracer.add_event(TraceEvent("task_end", f"task:{task_name}", end_details))

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = _start(args, kwargs)
                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    _end(start, None, e)
                    raise
                _end(start, result, None)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = _start(args, kwargs)
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                _end(start, None, e)
                raise
            _end(start, result, None)
            return result

        return wrapper

    return decorator
```

Add `import inspect` at the top. Then check that CrewAI's `@listen` still sees the async flow steps as coroutines. Run the existing async flow tests (`tests/flows/test_all_steps_emit_docx.py`, `tests/test_osint_parallel_json.py`), and check `inspect.iscoroutinefunction(ReceptionFlow.generate_osint)` in a one-line snippet. If CrewAI wraps the step before `trace_task` sees it, report what you found.

- [ ] **Step 4: Build tracers directly**

In `src/epic_news/main.py`, replace the import with `from epic_news.utils.observability import Tracer, trace_task`. Replace the four lines that start at `# Initialize observability tools at the module level` with:

```python
# Trace events (task_start / task_error / task_end) for every flow step, written under traces/.
tracer = Tracer(f"reception_flow_{int(time.time())}")
```

Delete `self.tracer = tracer`, `self.dashboard = dashboard` and `self.hallucination_guard = hallucination_guard` in `ReceptionFlow.__init__` (main.py:226-228). Keep `self.tracer` only if something reads it: `grep -rn "\.tracer\b" src tests`.

In `src/epic_news/crews/company_news/company_news_crew.py`, make the same change: build `tracer = Tracer(f"company_news_crew_{int(time.time())}")`, drop the `dashboard`/`hallucination_guard` module variables and their `self.` assignments, and keep every `@trace_task(tracer)`.

- [ ] **Step 5: Run everything**

Run:
```bash
env -u VIRTUAL_ENV uv run pytest -q
uv run ruff check --no-fix . && uv run mypy src/epic_news
grep -rnE "get_observability_tools|HallucinationGuard|Dashboard\b|monitor_agent|guard_output|hallucination_guard|self\.dashboard" src tests scripts
wc -l src/epic_news/utils/observability.py
```
Expected: all pass, ruff and mypy clean, the grep prints nothing. Report the line count (was 524).

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/utils/observability.py src/epic_news/main.py src/epic_news/crews/company_news/company_news_crew.py tests/utils/test_observability.py
git commit -m "refactor(observability): keep Tracer and trace_task (async-aware); drop unused tools"
```

---

### Task 4: Docs

**Files:**
- Modify: root `CLAUDE.md` (LLM Configuration section: where the patches live, plus an upgrade note), `src/epic_news/utils/CLAUDE.md` (the `flow_enforcement.py`, `observability.py` tree lines and the "Observability" bullet), and `docs/explanations/architecture.md` / `docs/reference/*.md`, only where they name a removed tool or say the patches are in `llm_config.py`

**Interfaces:**
- Consumes: Task 1 (shared retry path), Task 2 (`config/crewai_patches.py`, `apply_crewai_patches()` called by `epic_news.main`), Task 3 (`Tracer` + async-aware `trace_task`; the other tools gone).

- [ ] **Step 1: Find stale statements**

```bash
grep -rnE "get_observability_tools|HallucinationGuard|Dashboard|monitor_agent|guard_output|monkeypatch|monkey-patch|llm_config\.py.*(patch|ReAct|empty)" CLAUDE.md src/epic_news/*/CLAUDE.md docs/explanations docs/reference docs/how-to README.md
```

List the hits in your report. Leave historical docs (`docs/superpowers/`, `docs/archive/`, `docs/adr/`, `TODO.md`, `CHANGELOG.md`) alone.

- [ ] **Step 2: Rewrite each hit**

Say what is true after Tasks 1-3:
- The CrewAI patches live in `src/epic_news/config/crewai_patches.py`. They are applied by `epic_news.main` through `apply_crewai_patches()`, and its docstring lists what to re-check on each CrewAI upgrade.
- `observability.py` provides `Tracer` and `trace_task`, which records sync and async flow steps under `traces/`.

Edit only the sentences that are wrong.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md src/epic_news docs
git commit -m "docs: crewai_patches and the trimmed observability module (S8)"
```

Do not stage `docs/audits/`, which is untracked and must stay out of git. Do not run `ruff format .`.

---

Controller, before the PR: run one live check with `EPIC_ENABLE_EMAIL=false`, `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py saint`. It confirms that the patches applied from `main` still drive the LLM calls: the LiteLLM call count stays in the usual range and the DOCX is complete. Then check that `traces/` holds `task_start`/`task_end` events for `generate_saint_daily` and `send_email`. In the PR, report the line counts of `flow_enforcement.py`, `llm_config.py`, `crewai_patches.py` and `observability.py` before and after.
