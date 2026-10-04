# Efficiency Wave Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut wall-clock time and tokens of the slowest epic_news crews (PESTEL, NewsDaily, menu, holiday DOCX, routing, cross-reference) without lowering report quality, and prove every gain with before/after numbers.

**Architecture:** Measure first (per-crew duration and token usage logged by `kickoff_flow`, plus a bench script over fixed requests). Then remove duplicated LLM passes (recipes, routing, cross-reference) and run independent work concurrently (async CrewAI tasks, a bounded thread pool for DOCX sections and menu recipes). One process-wide cap (`LLM_MAX_CONCURRENCY`, default 3) bounds simultaneous LLM calls whatever starts them, because CrewAI's async tasks have no concurrency limit of their own.

**Tech Stack:** Python 3.13, CrewAI 1.15.23 (Flow, `@CrewBase`, async tasks), LiteLLM, Loguru, pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-10-04-efficiency-wave-design.md`

## Global Constraints

- Package manager: `uv` only. In a git worktree prefix every uv command with `env -u VIRTUAL_ENV` (the variable points at the main checkout's venv) and run `env -u VIRTUAL_ENV uv sync --all-extras` once first.
- Logging: Loguru (`from loguru import logger`), never stdlib `logging`.
- All imports at the top of files, never inside functions.
- Never hardcode model names or timeouts; use `LLMConfig` (`get_openrouter_llm(task_type=...)`, `get_max_iter()`, `get_max_rpm()`).
- Never `agent.copy()`: `LLM.__copy__` drops the timeout (ADR-014). Build a new Agent instead.
- Concurrency limits default to **3** (spec decision 1).
- Tool `_run()` methods return JSON strings (use `epic_news.tools._json_utils.ensure_json_str`).
- Agent-facing file access stays inside `output/` (ADR-015).
- The ADR-014 guard tests must stay green: `tests/crews/test_constructor_kwargs.py`, `tests/crews/test_agent_settings_contract.py`.
- Format only Python files: `env -u VIRTUAL_ENV uv run ruff format $(git ls-files '*.py')` — never `ruff format .` (it rewrites Markdown).
- Before each commit: `env -u VIRTUAL_ENV uv run ruff check .` and `env -u VIRTUAL_ENV uv run mypy src/epic_news` must be clean.
- Commit messages: conventional commits, ending with:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_018QNoTDtJL1CBKLZyD8jDzP
  ```
- Live LLM runs cost money. Run them **only** in the steps marked **LIVE**, with exactly the commands given. The user approved about a dozen crew runs for the whole wave.
- Record every live measurement in `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md` (created in Task 2).

## Review Focus

1. **Ctrl+C during a concurrent section or recipe batch** — the run must stop starting new work and abort; a cancelled item must never be swallowed as a per-item failure. Tests in Task 8 (`bounded_map` cancels pending work) and Task 11 (`RunCancelledError` propagates from `_generate_menu_recipe`).
2. **Six PESTEL researchers sharing one Wikipedia MCP adapter at the same time** — tools must still answer and the server must still be stopped. Covered by the Task 6 LIVE run (check the report has all six dimensions and no `wikipedia-mcp` process remains).
3. **Provider rate limits under parallel load, now that a crew is not replayed (`CREW_KICKOFF_ATTEMPTS=1`)** — LiteLLM `num_retries` plus the global cap must absorb 429s. Test in Task 3 (cap never exceeded under 8 threads); LIVE runs in Tasks 7, 9 and 11 watch for 429 failures.
4. **Extraction returns a lowercase, misspelled or unknown category** — normalised when valid, otherwise the `ClassifyCrew` fallback runs; never routed to a wrong crew by substring. Tests in Task 13.
5. **One recipe of a menu fails** — the others are still produced, results keep menu order, the failure is logged. Test in Task 11.

---

## PR 1 — Measurement and cheap fixes (spec E0 + E1)

### Task 1: Log duration and token usage for every crew run

**Files:**
- Modify: `src/epic_news/utils/flow_enforcement.py`
- Test: `tests/utils/test_flow_enforcement_usage.py` (create)

**Interfaces:**
- Produces: `_log_run_usage(crew_name: str, elapsed: float, result: Any) -> None` in `flow_enforcement`; log line format `📊 Crew {name} took {s}s — tokens: total=… prompt=… completion=… cached=… requests=…` (Task 2's bench script parses lines starting with `📊 Crew`).

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/test_flow_enforcement_usage.py
from types import SimpleNamespace

from loguru import logger

from epic_news.utils import flow_enforcement


def _capture():
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")
    return messages, sink_id


def _usage(total=10, prompt=7, completion=3, cached=1, requests=2):
    return SimpleNamespace(
        total_tokens=total,
        prompt_tokens=prompt,
        completion_tokens=completion,
        cached_prompt_tokens=cached,
        successful_requests=requests,
    )


def test_log_run_usage_reports_tokens():
    messages, sink_id = _capture()
    try:
        flow_enforcement._log_run_usage("PoemCrew", 1.5, SimpleNamespace(token_usage=_usage()))
    finally:
        logger.remove(sink_id)
    line = next(m for m in messages if m.startswith("📊 Crew PoemCrew"))
    assert "1.50s" in line
    assert "total=10" in line and "prompt=7" in line and "completion=3" in line
    assert "cached=1" in line and "requests=2" in line


def test_log_run_usage_without_usage():
    messages, sink_id = _capture()
    try:
        flow_enforcement._log_run_usage("PoemCrew", 0.25, object())
    finally:
        logger.remove(sink_id)
    assert any(m.startswith("📊 Crew PoemCrew took 0.25s") and "no token usage" in m for m in messages)


class _FakeCrew:
    def kickoff(self, inputs):
        return SimpleNamespace(token_usage=_usage(total=42))


def test_kickoff_flow_logs_usage(monkeypatch):
    monkeypatch.setenv("CREW_KICKOFF_ATTEMPTS", "1")
    messages, sink_id = _capture()
    try:
        flow_enforcement.kickoff_flow(_FakeCrew(), {"topic": "x"})
    finally:
        logger.remove(sink_id)
    assert any(m.startswith("📊 Crew _FakeCrew") and "total=42" in m for m in messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_flow_enforcement_usage.py -v`
Expected: FAIL with `AttributeError: module 'epic_news.utils.flow_enforcement' has no attribute '_log_run_usage'`

- [ ] **Step 3: Implement**

Add after `_get_crew_instance` in `src/epic_news/utils/flow_enforcement.py`:

```python
def _log_run_usage(crew_name: str, elapsed: float, result: Any) -> None:
    """Log wall-clock time and CrewAI token usage for one successful crew run."""
    usage = getattr(result, "token_usage", None)
    if usage is None:
        logger.info("📊 Crew {} took {:.2f}s (no token usage reported)", crew_name, elapsed)
        return
    logger.info(
        "📊 Crew {} took {:.2f}s — tokens: total={} prompt={} completion={} cached={} requests={}",
        crew_name,
        elapsed,
        getattr(usage, "total_tokens", 0),
        getattr(usage, "prompt_tokens", 0),
        getattr(usage, "completion_tokens", 0),
        getattr(usage, "cached_prompt_tokens", 0),
        getattr(usage, "successful_requests", 0),
    )
```

In **both** `kickoff_flow` and `akickoff_flow`, replace the success branch line

```python
                logger.info("✅ Crew {} finished in {:.2f}s", crew_name, elapsed)
```

with

```python
                _log_run_usage(crew_name, elapsed, result)
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_flow_enforcement_usage.py tests/utils/test_flow_enforcement.py tests/utils/test_flow_enforcement_retry.py -v`
Expected: PASS (if an existing test asserts the old `✅ Crew … finished` text, update it to the `📊 Crew … took` line).

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/flow_enforcement.py tests/utils/test_flow_enforcement_usage.py tests/utils/
git commit -m "feat(flow): log duration and token usage for every crew run"
```

### Task 2: Bench script and baseline measurements

**Files:**
- Create: `scripts/bench_flow.py`
- Create: `scripts/bench_requests.json`
- Create: `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md`
- Test: `tests/scripts/test_bench_flow.py` (create; add `tests/scripts/__init__.py` if the directory has none)

**Interfaces:**
- Consumes: the `📊 Crew …` log lines from Task 1.
- Produces: `python scripts/bench_flow.py <name> [<name> ...]` printing one JSON object per request: `{"name", "elapsed_s", "crews": [{"crew", "seconds", "total", "prompt", "completion", "requests"}]}`. Later tasks run it in their LIVE steps.

- [ ] **Step 1: Write the failing test for the log parser**

```python
# tests/scripts/test_bench_flow.py
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("bench_flow", Path("scripts/bench_flow.py"))
bench_flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench_flow)


def test_parse_usage_line():
    line = "📊 Crew PestelCrew took 312.40s — tokens: total=120000 prompt=100000 completion=20000 cached=0 requests=45"
    assert bench_flow.parse_usage_line(line) == {
        "crew": "PestelCrew",
        "seconds": 312.4,
        "total": 120000,
        "prompt": 100000,
        "completion": 20000,
        "requests": 45,
    }


def test_parse_usage_line_ignores_other_lines():
    assert bench_flow.parse_usage_line("🚀 Kicking off crew PestelCrew") is None
    assert bench_flow.parse_usage_line("📊 Crew PoemCrew took 1.00s (no token usage reported)") == {
        "crew": "PoemCrew",
        "seconds": 1.0,
        "total": None,
        "prompt": None,
        "completion": None,
        "requests": None,
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/scripts/test_bench_flow.py -v`
Expected: FAIL (`scripts/bench_flow.py` does not exist).

- [ ] **Step 3: Implement the script and the request set**

```python
# scripts/bench_flow.py
"""Run named benchmark requests through ReceptionFlow and print per-crew cost.

Usage: env -u VIRTUAL_ENV uv run python scripts/bench_flow.py pestel news_daily

LIVE: every request is a full flow run against the configured LLM provider.
"""

import json
import re
import sys
import time
from pathlib import Path

from loguru import logger

import epic_news.main as main_mod

_REQUESTS = Path(__file__).with_name("bench_requests.json")
_LINE = re.compile(
    r"^📊 Crew (?P<crew>\S+) took (?P<seconds>[\d.]+)s"
    r"(?: — tokens: total=(?P<total>\d+) prompt=(?P<prompt>\d+) completion=(?P<completion>\d+)"
    r" cached=\d+ requests=(?P<requests>\d+))?"
)


def parse_usage_line(line: str) -> dict | None:
    match = _LINE.match(line)
    if not match:
        return None

    def _int(key: str) -> int | None:
        value = match.group(key)
        return int(value) if value is not None else None

    return {
        "crew": match.group("crew"),
        "seconds": float(match.group("seconds")),
        "total": _int("total"),
        "prompt": _int("prompt"),
        "completion": _int("completion"),
        "requests": _int("requests"),
    }


def run(name: str, request: str) -> dict:
    crews: list[dict] = []

    def sink(message) -> None:
        parsed = parse_usage_line(message.record["message"])
        if parsed:
            crews.append(parsed)

    # kickoff() calls setup_logging(), which removes every loguru handler; attach the
    # capture sink right after it instead of before the run.
    original_setup = main_mod.setup_logging
    sink_ids: list[int] = []

    def setup_logging_then_capture(*args, **kwargs):
        original_setup(*args, **kwargs)
        sink_ids.append(logger.add(sink, level="INFO"))

    main_mod.setup_logging = setup_logging_then_capture
    start = time.perf_counter()
    try:
        main_mod.kickoff(user_input=request)
    finally:
        main_mod.setup_logging = original_setup
        for sink_id in sink_ids:
            logger.remove(sink_id)
    return {"name": name, "elapsed_s": round(time.perf_counter() - start, 1), "crews": crews}


def main(names: list[str]) -> None:
    requests = json.loads(_REQUESTS.read_text(encoding="utf-8"))
    for name in names:
        print(json.dumps(run(name, requests[name]), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
```

```json
{
  "pestel": "Fais-moi une analyse PESTEL du marché suisse des voitures électriques",
  "news_daily": "Donne-moi les actualités du jour",
  "menu": "Prépare un menu pour 2 jours, déjeuner et dîner, pour 2 personnes, cuisine de saison",
  "holiday": "Planifie un week-end de 3 jours à Florence en famille au départ de Genève",
  "osint": "Fais un rapport OSINT sur l'entreprise Logitech"
}
```

Create `docs/superpowers/plans/2026-10-04-efficiency-wave-results.md`:

```markdown
# Efficiency Wave — Measurements

Numbers from `scripts/bench_flow.py` (wall clock of the whole flow, plus per-crew lines
logged by `kickoff_flow`). Model: value of `MODEL` in `.env` at run time.

| Date | Change | Request | Wall clock (s) | Crew | Crew seconds | Total tokens | Requests |
|---|---|---|---|---|---|---|---|
```

- [ ] **Step 4: Run the parser tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/scripts/test_bench_flow.py -v`
Expected: PASS

- [ ] **Step 5: LIVE — record the baseline (before any optimisation)**

Run from the repository root (main checkout or worktree with a filled `.env`):
`env -u VIRTUAL_ENV uv run python scripts/bench_flow.py pestel news_daily menu holiday`
Add one row per crew line to the results file with Change = `baseline`. Do not run `osint` here (Task 14 measures it).

- [ ] **Step 6: Commit**

```bash
git add scripts/bench_flow.py scripts/bench_requests.json tests/scripts docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "feat(scripts): add flow bench script and record baseline"
```

### Task 3: Cap simultaneous LLM calls process-wide

**Files:**
- Modify: `src/epic_news/config/llm_config.py` (the `call` / `acall` wrappers installed by the class patch, around lines 240-280)
- Modify: `.env.example`
- Test: `tests/config/test_llm_concurrency_cap.py` (create)

**Interfaces:**
- Produces: `_with_llm_slot(call_fn: Callable[[], T]) -> T`, `async _awith_llm_slot(call_fn: Callable[[], Awaitable[T]]) -> T`, `_reset_llm_slots() -> None` in `llm_config`; env `LLM_MAX_CONCURRENCY` (default 3, minimum 1).

- [ ] **Step 1: Write the failing test**

```python
# tests/config/test_llm_concurrency_cap.py
import asyncio
import threading
import time

from epic_news.config import llm_config


def _measure_peak(run_one, workers: int) -> int:
    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    def body():
        with lock:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(0.05)
        with lock:
            state["now"] -= 1
        return "ok"

    threads = [threading.Thread(target=lambda: run_one(body)) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return state["peak"]


def test_sync_calls_never_exceed_cap(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "3")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=8) == 3


def test_cap_of_one_serialises(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=4) == 1


def test_invalid_value_falls_back_to_three(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "zero")
    llm_config._reset_llm_slots()
    assert _measure_peak(llm_config._with_llm_slot, workers=6) == 3


def test_async_calls_share_the_cap(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "2")
    llm_config._reset_llm_slots()
    state = {"now": 0, "peak": 0}

    async def body():
        state["now"] += 1
        state["peak"] = max(state["peak"], state["now"])
        await asyncio.sleep(0.05)
        state["now"] -= 1
        return "ok"

    async def main():
        return await asyncio.gather(*(llm_config._awith_llm_slot(body) for _ in range(6)))

    assert asyncio.run(main()) == ["ok"] * 6
    assert state["peak"] == 2


def test_slot_released_on_error(monkeypatch):
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    llm_config._reset_llm_slots()

    def boom():
        raise RuntimeError("provider down")

    for _ in range(3):
        try:
            llm_config._with_llm_slot(boom)
        except RuntimeError:
            pass
    assert llm_config._with_llm_slot(lambda: "still works") == "still works"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/config/test_llm_concurrency_cap.py -v`
Expected: FAIL with `AttributeError: ... has no attribute '_reset_llm_slots'`

- [ ] **Step 3: Implement**

At the top of `src/epic_news/config/llm_config.py` add `import asyncio` and `import threading` to the imports (keep them sorted), and `from collections.abc import Awaitable, Callable` plus `from typing import TypeVar` if not already imported. Add near the other module-level helpers:

```python
_T = TypeVar("_T")
_llm_slots: threading.BoundedSemaphore | None = None
_llm_slots_lock = threading.Lock()


def _llm_concurrency() -> int:
    """Max simultaneous LLM calls in this process (LLM_MAX_CONCURRENCY, default 3)."""
    try:
        return max(1, int(os.getenv("LLM_MAX_CONCURRENCY", "3")))
    except ValueError:
        return 3


def _slots() -> threading.BoundedSemaphore:
    global _llm_slots
    with _llm_slots_lock:
        if _llm_slots is None:
            _llm_slots = threading.BoundedSemaphore(_llm_concurrency())
        return _llm_slots


def _reset_llm_slots() -> None:
    """Re-read LLM_MAX_CONCURRENCY on next use (tests only)."""
    global _llm_slots
    with _llm_slots_lock:
        _llm_slots = None


def _with_llm_slot(call_fn: Callable[[], _T]) -> _T:
    """Run one LLM call while holding a process-wide concurrency slot.

    CrewAI async tasks, the DOCX section pool, the menu recipe pool and the OSINT
    fan-out all start LLM calls in parallel; this is the single place that bounds them.
    """
    with _slots():
        return call_fn()


async def _awith_llm_slot(call_fn: Callable[[], Awaitable[_T]]) -> _T:
    """Async twin of _with_llm_slot; waits for a slot without blocking the event loop."""
    slots = _slots()
    await asyncio.to_thread(slots.acquire)
    try:
        return await call_fn()
    finally:
        slots.release()
```

In the class patch, wrap the original call inside the slot. Replace

```python
            result = _call_with_empty_retry(
                lambda: original_call(self, *args, **kwargs),
```

with

```python
            result = _call_with_empty_retry(
                lambda: _with_llm_slot(lambda: original_call(self, *args, **kwargs)),
```

and replace

```python
            result = await _acall_with_empty_retry(
                lambda: original_acall(self, *args, **kwargs),
```

with

```python
            result = await _acall_with_empty_retry(
                lambda: _awith_llm_slot(lambda: original_acall(self, *args, **kwargs)),
```

Each retry attempt takes its own slot, so a backoff sleep never holds one.

Add to `.env.example`, next to the other LLM settings:

```bash
# Max simultaneous LLM calls in the whole process (async tasks, DOCX sections,
# menu recipes, OSINT crews). Default 3.
LLM_MAX_CONCURRENCY=3
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/config -v`
Expected: PASS (the existing empty-retry and completion-param tests must still pass).

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/config/llm_config.py .env.example tests/config/test_llm_concurrency_cap.py
git commit -m "feat(llm): cap simultaneous LLM calls process-wide (LLM_MAX_CONCURRENCY=3)"
```

### Task 4: Lazy Composio import and single crew attempt

**Files:**
- Modify: `src/epic_news/config/__init__.py`
- Modify: `src/epic_news/utils/flow_enforcement.py` (`_retry_settings`)
- Modify: `.env.example`
- Test: `tests/config/test_config_package_import.py` (create), `tests/utils/test_flow_enforcement_retry.py` (add one test)

**Interfaces:**
- Produces: `epic_news.config` no longer exports `ComposioConfig` (import it from `epic_news.config.composio_config`); `CREW_KICKOFF_ATTEMPTS` default 1.

- [ ] **Step 1: Write the failing tests**

```python
# tests/config/test_config_package_import.py
import subprocess
import sys


def test_importing_config_does_not_import_composio():
    code = (
        "import sys; import epic_news.config.llm_config; "
        "print('composio' in sys.modules)"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
```

Append to `tests/utils/test_flow_enforcement_retry.py`:

```python
def test_default_is_a_single_attempt(monkeypatch):
    monkeypatch.delenv("CREW_KICKOFF_ATTEMPTS", raising=False)
    from epic_news.utils.flow_enforcement import _retry_settings

    attempts, _ = _retry_settings()
    assert attempts == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/config/test_config_package_import.py tests/utils/test_flow_enforcement_retry.py::test_default_is_a_single_attempt -v`
Expected: both FAIL (`True` printed; attempts == 3).

- [ ] **Step 3: Implement**

`src/epic_news/config/__init__.py`:

```python
"""Configuration package for epic_news.

ComposioConfig is intentionally not re-exported: importing Composio costs ~2 s and
only company_news uses it (import it from epic_news.config.composio_config).
"""

from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig

__all__ = ["LLMConfig", "MCPConfig"]
```

Run `git grep -n "from epic_news.config import" -- src tests scripts` and change any import of `ComposioConfig` from the package to `from epic_news.config.composio_config import ComposioConfig`.

In `src/epic_news/utils/flow_enforcement.py`, `_retry_settings`, change the default:

```python
    attempts = max(1, int(os.getenv("CREW_KICKOFF_ATTEMPTS", "1")))
```

Update the comment above `_TRANSIENT_ERROR_MARKERS` by adding one line at its end:

```python
# Default is a single attempt: LiteLLM already retries the failing call (num_retries=2),
# and replaying a whole crew re-runs every finished task. Raise CREW_KICKOFF_ATTEMPTS to opt in.
```

Add to `.env.example`:

```bash
# Whole-crew replays on transient provider errors (default 1 = no replay;
# LiteLLM already retries the single failing call).
CREW_KICKOFF_ATTEMPTS=1
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/config tests/utils tests/crews -q`
Expected: PASS. Then measure import time:
`env -u VIRTUAL_ENV uv run python -X importtime -c "import epic_news.main" 2>&1 | tail -1`
Expected: total noticeably lower than before (~7 s → ~5 s); note the number in the commit message body.

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/config/__init__.py src/epic_news/utils/flow_enforcement.py .env.example tests/config/test_config_package_import.py tests/utils/test_flow_enforcement_retry.py
git commit -m "perf: import Composio lazily and stop replaying whole crews by default"
```

### Task 5: Cap scraped page size

**Files:**
- Create: `src/epic_news/tools/capped_scrape_tool.py`
- Modify: `src/epic_news/crews/deep_research/deep_research.py:50`, `src/epic_news/crews/pestel/pestel_crew.py:37`, `src/epic_news/crews/sales_prospecting/sales_prospecting_crew.py:24,35,46`, `src/epic_news/tools/web_tools.py:53` (replace `ScrapeWebsiteTool()` with `CappedScrapeWebsiteTool()` and fix imports)
- Modify: `.env.example`
- Test: `tests/tools/test_capped_scrape_tool.py` (create)

**Interfaces:**
- Produces: `CappedScrapeWebsiteTool` (subclass of crewai_tools `ScrapeWebsiteTool`, same `name` "Read website content"), returning JSON `{"url", "content", "truncated"}`; env `SCRAPE_MAX_CHARS` (default 12000).

- [ ] **Step 1: Write the failing test**

```python
# tests/tools/test_capped_scrape_tool.py
import json

from crewai_tools import ScrapeWebsiteTool

from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool


def _fake_page(text):
    def _run(self, **kwargs):
        return text

    return _run


def test_long_page_is_truncated(monkeypatch):
    monkeypatch.setenv("SCRAPE_MAX_CHARS", "100")
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("é" * 500))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert out["url"] == "https://example.com"
    assert out["truncated"] is True
    assert out["content"] == "é" * 100


def test_short_page_is_untouched(monkeypatch):
    monkeypatch.setenv("SCRAPE_MAX_CHARS", "100")
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("short page"))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert out == {"url": "https://example.com", "content": "short page", "truncated": False}


def test_default_cap(monkeypatch):
    monkeypatch.delenv("SCRAPE_MAX_CHARS", raising=False)
    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _fake_page("x" * 20000))
    out = json.loads(CappedScrapeWebsiteTool()._run(website_url="https://example.com"))
    assert len(out["content"]) == 12000 and out["truncated"] is True


def test_scrape_error_becomes_json(monkeypatch):
    def _boom(self, **kwargs):
        raise ValueError("Website URL must be provided.")

    monkeypatch.setattr(ScrapeWebsiteTool, "_run", _boom)
    out = json.loads(CappedScrapeWebsiteTool()._run())
    assert "error" in out


def test_same_tool_name_as_crewai_scraper():
    assert CappedScrapeWebsiteTool().name == ScrapeWebsiteTool().name
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/tools/test_capped_scrape_tool.py -v`
Expected: FAIL (`ModuleNotFoundError: epic_news.tools.capped_scrape_tool`)

- [ ] **Step 3: Implement**

```python
# src/epic_news/tools/capped_scrape_tool.py
"""crewai_tools' ScrapeWebsiteTool with a size cap and a JSON result.

The upstream tool returns the whole page text; one large page can fill the agent's
context window. ScrapeNinja already caps at 20k characters; this keeps the backup
scraper in line (SCRAPE_MAX_CHARS, default 12000).
"""

import os
from typing import Any

from crewai_tools import ScrapeWebsiteTool

from epic_news.tools._json_utils import ensure_json_str

DEFAULT_MAX_CHARS = 12_000


def _max_chars() -> int:
    try:
        return max(1, int(os.getenv("SCRAPE_MAX_CHARS", str(DEFAULT_MAX_CHARS))))
    except ValueError:
        return DEFAULT_MAX_CHARS


class CappedScrapeWebsiteTool(ScrapeWebsiteTool):
    """Read a web page, return at most SCRAPE_MAX_CHARS characters as JSON."""

    def _run(self, **kwargs: Any) -> str:
        url = kwargs.get("website_url", self.website_url)
        try:
            text = str(super()._run(**kwargs))
        except Exception as exc:  # noqa: BLE001 - surface scrape failures to the agent as data
            return ensure_json_str({"url": url, "error": str(exc)})
        limit = _max_chars()
        return ensure_json_str({"url": url, "content": text[:limit], "truncated": len(text) > limit})
```

Replace every `ScrapeWebsiteTool()` listed under **Files** with `CappedScrapeWebsiteTool()`; in each file replace `from crewai_tools import ScrapeWebsiteTool` (or remove `ScrapeWebsiteTool` from a multi-name crewai_tools import) and add `from epic_news.tools.capped_scrape_tool import CappedScrapeWebsiteTool`.

Add to `.env.example`:

```bash
# Max characters returned by the backup web scraper (default 12000).
SCRAPE_MAX_CHARS=12000
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/tools tests/crews -q`
Expected: PASS (the JSON ratchet test and the agent contract test included).

- [ ] **Step 5: Commit and open PR 1**

```bash
git add src/epic_news/tools/capped_scrape_tool.py src/epic_news/crews src/epic_news/tools/web_tools.py .env.example tests/tools/test_capped_scrape_tool.py
git commit -m "perf(tools): cap backup scraper output at SCRAPE_MAX_CHARS"
```

Controller: run the full suite, ruff and mypy, then open PR 1 (Tasks 1–5) with the baseline table and the import-time number in the description.

---

## PR 2 — Parallel independent tasks (spec E2)

### Task 6: PESTEL dimension tasks run in parallel

**Files:**
- Modify: `src/epic_news/crews/pestel/pestel_crew.py` (the six `*_research_task` methods)
- Test: `tests/crews/test_pestel_async_tasks.py` (create)

**Interfaces:**
- Consumes: Task 3's global LLM cap (bounds the six parallel researchers to 3 simultaneous LLM calls).

- [ ] **Step 1: Write the failing test**

```python
# tests/crews/test_pestel_async_tasks.py
from epic_news.crews.pestel import pestel_crew


def test_dimension_tasks_are_async_and_report_waits(monkeypatch):
    # Never spawn the Wikipedia MCP server in unit tests.
    monkeypatch.setattr(pestel_crew, "get_mcp_tools_or_empty", lambda crew: [])
    crew = pestel_crew.PestelCrew().crew()

    research = [t for t in crew.tasks if t.output_pydantic is None]
    report = crew.tasks[-1]

    assert len(research) == 6
    assert all(t.async_execution for t in research)
    assert report.async_execution is False
    assert {id(t) for t in report.context} == {id(t) for t in research}
    # One researcher per dimension: async tasks never share an Agent instance.
    assert len({id(t.agent) for t in research}) == 6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews/test_pestel_async_tasks.py -v`
Expected: FAIL on `assert all(t.async_execution for t in research)`.

- [ ] **Step 3: Implement**

In each of the six methods `political_research_task`, `economic_research_task`, `social_research_task`, `technological_research_task`, `environmental_research_task`, `legal_research_task`, change

```python
            async_execution=False,
```

to

```python
            async_execution=True,
```

Update the module docstring's first paragraph to add: "The six dimension tasks run in parallel (async); the report task waits for all of them through its context."

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews tests/test_generate_pestel_wiring.py -q`
Expected: PASS

- [ ] **Step 5: LIVE — measure and check the report**

Run: `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py pestel`
Check: the run succeeds; the generated PESTEL report (`output/pestel/` HTML or DOCX) has six non-empty dimensions; `pgrep -fl wikipedia-mcp` prints nothing after the run. Add the row (Change = `E2 pestel async`) to the results file.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/crews/pestel/pestel_crew.py tests/crews/test_pestel_async_tasks.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "perf(pestel): run the six dimension tasks in parallel"
```

### Task 7: NewsDaily region tasks run in parallel, each with its own researcher

**Files:**
- Modify: `src/epic_news/crews/news_daily/news_daily.py`
- Test: `tests/crews/test_news_daily_async_tasks.py` (create)

**Interfaces:**
- Produces: `NewsDailyCrew._new_researcher() -> Agent` (plain method, not `@agent`).

- [ ] **Step 1: Write the failing test**

```python
# tests/crews/test_news_daily_async_tasks.py
from epic_news.crews.news_daily.news_daily import NewsDailyCrew

REGION_TASKS = 7


def test_region_tasks_parallel_with_distinct_agents():
    crew = NewsDailyCrew().crew()
    regions = crew.tasks[:REGION_TASKS]
    curation, final = crew.tasks[REGION_TASKS], crew.tasks[REGION_TASKS + 1]

    assert all(t.async_execution for t in regions)
    assert curation.async_execution is False and final.async_execution is False
    assert len({id(t.agent) for t in regions}) == REGION_TASKS
    assert {id(t) for t in curation.context} == {id(t) for t in regions}


def test_every_task_agent_is_registered_in_the_crew():
    crew = NewsDailyCrew().crew()
    registered = {id(a) for a in crew.agents}
    assert all(id(t.agent) in registered for t in crew.tasks if t.agent is not None)


def test_region_researchers_keep_llm_timeout():
    crew = NewsDailyCrew().crew()
    assert all(t.agent.llm.timeout is not None for t in crew.tasks[:REGION_TASKS])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews/test_news_daily_async_tasks.py -v`
Expected: FAIL (`async_execution` is False; all region tasks share one agent).

- [ ] **Step 3: Implement**

Replace the `news_researcher` agent method with:

```python
    def _new_researcher(self) -> Agent:
        """A fresh researcher for one region task.

        Region tasks run in parallel, so they must not share one Agent instance, and
        Agent.copy() would drop the LLM timeout (ADR-014).
        """
        return Agent(
            config=self.agents_config["news_researcher"],
            tools=get_news_tools(),  # get_search_tools() is the same PerplexitySearchTool
            llm=LLMConfig.get_openrouter_llm(),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )

    @agent
    def news_researcher(self) -> Agent:
        # Kept as an @agent so tasks.yaml's `agent: news_researcher` still resolves;
        # region tasks override it with their own instance (explicit agent= wins).
        return self._new_researcher()
```

In each of the seven region task methods (`suisse_romande_news_task` … `economy_news_task`) replace

```python
            agent=self.news_researcher(),  # type: ignore[call-arg]
            async_execution=False,
```

with

```python
            agent=self._new_researcher(),
            async_execution=True,
```

Replace the `crew` method body with:

```python
    @crew
    def crew(self) -> Crew:
        """Creates the NewsDaily crew"""
        agents = list(self.agents)  # type: ignore[attr-defined]
        for task_ in self.tasks:  # type: ignore[attr-defined]
            if task_.agent is not None and all(task_.agent is not known for known in agents):
                agents.append(task_.agent)
        return Crew(
            agents=agents,
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews -q`
Expected: PASS (including `test_agent_settings_contract.py`, which now also sees the seven region researchers).

- [ ] **Step 5: LIVE — measure and check the report**

Run: `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py news_daily`
Check: the run succeeds and the report has content for all seven regions; no 429 failure in the log. Add the row (Change = `E2 news_daily async`).

- [ ] **Step 6: Commit and open PR 2**

```bash
git add src/epic_news/crews/news_daily/news_daily.py tests/crews/test_news_daily_async_tasks.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "perf(news_daily): run region tasks in parallel with one researcher each"
```

Controller: full suite, ruff, mypy; open PR 2 (Tasks 6–7) with the before/after rows.

---

## PR 3 — DOCX assembly (spec E4)

### Task 8: Bounded parallel narration of DOCX sections

**Files:**
- Create: `src/epic_news/utils/concurrency.py`
- Modify: `src/epic_news/utils/docx_report/assemble.py`
- Modify: `.env.example`
- Test: `tests/utils/test_concurrency.py` (create), `tests/utils/docx_report/test_assemble_parallel.py` (create)

**Interfaces:**
- Produces: `concurrency_limit(env_var: str, default: int = 3) -> int` and `bounded_map(func: Callable[[T], R], items: Iterable[T], env_var: str, default: int = 3) -> list[R]` in `epic_news.utils.concurrency` (Task 11 uses `bounded_map`); env `DOCX_FRAGMENT_CONCURRENCY` (default 3).

- [ ] **Step 1: Write the failing tests**

```python
# tests/utils/test_concurrency.py
import threading
import time

import pytest

from epic_news.utils.concurrency import bounded_map, concurrency_limit
from epic_news.utils.interrupt import RunCancelledError


def test_results_keep_input_order(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "3")

    def slow_inverse(n):
        time.sleep(0.01 * (5 - n))
        return n * 10

    assert bounded_map(slow_inverse, [1, 2, 3, 4], "TEST_POOL") == [10, 20, 30, 40]


def test_never_more_workers_than_limit(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "2")
    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    def work(_):
        with lock:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(0.03)
        with lock:
            state["now"] -= 1

    bounded_map(work, range(8), "TEST_POOL")
    assert state["peak"] == 2


def test_limit_parsing(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "nope")
    assert concurrency_limit("TEST_POOL") == 3
    monkeypatch.setenv("TEST_POOL", "0")
    assert concurrency_limit("TEST_POOL") == 1
    monkeypatch.delenv("TEST_POOL")
    assert concurrency_limit("TEST_POOL", default=5) == 5


def test_empty_input():
    assert bounded_map(lambda x: x, [], "TEST_POOL") == []


def test_cancellation_stops_pending_work(monkeypatch):
    monkeypatch.setenv("TEST_POOL", "1")
    started: list[int] = []

    def work(n):
        started.append(n)
        if n == 0:
            raise RunCancelledError("user pressed Ctrl+C")
        time.sleep(0.01)
        return n

    with pytest.raises(RunCancelledError):
        bounded_map(work, range(10), "TEST_POOL")
    assert len(started) < 10
```

```python
# tests/utils/docx_report/test_assemble_parallel.py
import threading
import time

from epic_news.utils.docx_report import assemble as assemble_mod
from epic_news.utils.docx_report.sections import Section


class _SlowLLM:
    def __init__(self):
        self.lock = threading.Lock()
        self.now = 0
        self.peak = 0

    def call(self, messages):
        with self.lock:
            self.now += 1
            self.peak = max(self.peak, self.now)
        time.sleep(0.03)
        with self.lock:
            self.now -= 1
        heading = messages[1]["content"].split("\n", 1)[0]
        return f"Body for {heading}"


def test_sections_narrated_in_parallel_and_in_order(monkeypatch, tmp_path):
    monkeypatch.setenv("DOCX_FRAGMENT_CONCURRENCY", "3")
    captured = {}
    monkeypatch.setattr(
        assemble_mod, "build_docx", lambda fragments, meta, path: captured.setdefault("f", fragments) and path
    )
    llm = _SlowLLM()
    sections = [Section(f"S{i}", instruction="write", context="ctx") for i in range(6)]
    sections.insert(2, Section("Fixed", body="verbatim"))

    assemble_mod.assemble_fragments(sections, {"title": "T"}, str(tmp_path / "x.docx"), llm, "sys")

    assert [h for h, _ in captured["f"]] == [s.heading for s in sections]
    assert dict(captured["f"])["Fixed"] == "verbatim"
    assert dict(captured["f"])["S4"] == "Body for Section: S4"
    assert llm.peak == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_concurrency.py tests/utils/docx_report/test_assemble_parallel.py -v`
Expected: FAIL (`ModuleNotFoundError: epic_news.utils.concurrency`; peak == 1).

- [ ] **Step 3: Implement**

```python
# src/epic_news/utils/concurrency.py
"""Bounded, order-preserving parallel map for blocking work (LLM calls, crew runs)."""

import os
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def concurrency_limit(env_var: str, default: int = 3) -> int:
    """Worker count from env_var (minimum 1; invalid values fall back to default)."""
    try:
        return max(1, int(os.getenv(env_var, str(default))))
    except ValueError:
        return default


def bounded_map(func: Callable[[T], R], items: Iterable[T], env_var: str, default: int = 3) -> list[R]:
    """Apply func to every item with at most concurrency_limit(env_var) threads.

    Results follow input order. The first exception (including RunCancelledError)
    cancels work that has not started yet and is re-raised.
    """
    batch = list(items)
    if not batch:
        return []
    workers = min(concurrency_limit(env_var, default), len(batch))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(func, item) for item in batch]
        try:
            return [future.result() for future in futures]
        except BaseException:
            for future in futures:
                future.cancel()
            raise
```

Replace the body of `assemble_fragments` in `src/epic_news/utils/docx_report/assemble.py` from `fragments: list[tuple[str, str]] = []` down to the line before `if placeholders * 2 > len(sections):` with:

```python
    def _render(section: Section) -> str:
        if section.body is not None:
            return section.body
        return generate_fragment(
            section.heading, section.instruction or "", section.context or "", llm, system
        )

    bodies = bounded_map(_render, sections, "DOCX_FRAGMENT_CONCURRENCY")
    fragments = [(s.heading, body) for s, body in zip(sections, bodies, strict=True)]
    placeholders = sum(
        1
        for s, body in zip(sections, bodies, strict=True)
        if s.body is None and body == placeholder_for(s.heading)
    )
```

Add `from epic_news.utils.concurrency import bounded_map` to the imports, and add to the docstring: "Narrated sections run in parallel (DOCX_FRAGMENT_CONCURRENCY, default 3); output keeps section order."

Add to `.env.example`:

```bash
# Parallel LLM narration of DOCX report sections (default 3).
DOCX_FRAGMENT_CONCURRENCY=3
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils -q`
Expected: PASS. If a test in `tests/utils/docx_report/test_assemble_failure_modes.py` depends on the call order of a fake LLM, make the fake answer by section heading instead of by call count (the order of LLM calls is no longer fixed; the order of sections in the DOCX is).

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/utils/concurrency.py src/epic_news/utils/docx_report/assemble.py .env.example tests/utils
git commit -m "perf(docx): narrate report sections in parallel (DOCX_FRAGMENT_CONCURRENCY=3)"
```

### Task 9: Holiday day sections receive only their day's research

**Files:**
- Modify: `src/epic_news/utils/holiday_report/assemble.py`
- Test: `tests/utils/holiday_report/test_day_slices.py` (create)

**Interfaces:**
- Produces: `_day_slices(itinerary: str, n_days: int) -> list[str] | None` in `holiday_report.assemble`.

- [ ] **Step 1: Write the failing test**

```python
# tests/utils/holiday_report/test_day_slices.py
import json

from epic_news.utils.holiday_report.assemble import _day_slices

_RESEARCH = {
    "itinerary_metadata": {"title": "Florence"},
    "essential_booking_timeline": [{"milestone": "a"}, {"milestone": "b"}],
    "daily_itineraries": [{"day_number": 1, "theme": "Duomo"}, {"day_number": 2, "theme": "Uffizi"}],
}


def test_slices_per_day_from_fenced_json():
    raw = "```json\n" + json.dumps(_RESEARCH) + "\n```"
    slices = _day_slices(raw, 2)
    assert [json.loads(s)["theme"] for s in slices] == ["Duomo", "Uffizi"]


def test_prefers_list_whose_key_mentions_day():
    slices = _day_slices(json.dumps(_RESEARCH), 2)
    assert json.loads(slices[0])["day_number"] == 1


def test_no_match_when_day_count_differs():
    assert _day_slices(json.dumps(_RESEARCH), 3) is None


def test_not_json_returns_none():
    assert _day_slices("Jour 1: Duomo. Jour 2: Uffizi.", 2) is None


def test_nested_day_list_is_found():
    nested = {"plan": {"days": [{"d": 1}, {"d": 2}, {"d": 3}]}}
    assert len(_day_slices(json.dumps(nested), 3)) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/holiday_report/test_day_slices.py -v`
Expected: FAIL (`ImportError: cannot import name '_day_slices'`)

- [ ] **Step 3: Implement**

Add `import json` and `import re` to the imports of `src/epic_news/utils/holiday_report/assemble.py`, then add below `_trip_summary`:

```python
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
# "daily" does not contain "day", so both are listed; "jour" covers French keys.
_DAY_KEY_HINTS = ("day", "daily", "jour")


def _find_day_list(node: Any, n_days: int) -> list[dict] | None:
    """Depth-first search for a list of n_days objects stored under a day-like key."""
    if isinstance(node, dict):
        for key, value in node.items():
            if (
                any(hint in str(key).lower() for hint in _DAY_KEY_HINTS)
                and isinstance(value, list)
                and len(value) == n_days
                and all(isinstance(item, dict) for item in value)
            ):
                return value
        children: list[Any] = list(node.values())
    elif isinstance(node, list):
        children = node
    else:
        return None
    for child in children:
        found = _find_day_list(child, n_days)
        if found:
            return found
    return None


def _day_slices(itinerary: str, n_days: int) -> list[str] | None:
    """One JSON string per day when the itinerary research holds a per-day list, else None."""
    text = itinerary.strip()
    fenced = _FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except ValueError:
        return None
    days = _find_day_list(data, n_days)
    if not days:
        return None
    return [json.dumps(day, ensure_ascii=False) for day in days]
```

In `assemble_holiday_docx`, after the skeleton log line, add:

```python
    day_slices = _day_slices(itinerary, len(skeleton.days))
    if day_slices is None:
        logger.info("🗓️ No per-day research list found; each day gets the full itinerary research")
```

and in the per-day loop replace the context argument

```python
                f"{summary}\n\nRecherche itinéraire:\n{itinerary}",
```

with

```python
                f"{summary}\n\nRecherche itinéraire:\n{day_slices[i - 1] if day_slices else itinerary}",
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/holiday_report tests/flows -q`
Expected: PASS

- [ ] **Step 5: LIVE — measure**

Run: `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py holiday`
Check: `output/holiday/itinerary.docx` has one section per day with day-specific content and no placeholder sections. Add the row (Change = `E4 docx parallel + day slices`).

- [ ] **Step 6: Commit and open PR 3**

```bash
git add src/epic_news/utils/holiday_report/assemble.py tests/utils/holiday_report/test_day_slices.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "perf(holiday): send each day section only its own itinerary research"
```

Controller: full suite, ruff, mypy; open PR 3 (Tasks 8–9).

---

## PR 4 — Menu and recipes (spec E3)

### Task 10: Recipes in one LLM pass; YAML and JSON written in Python

**Files:**
- Modify: `src/epic_news/models/crews/cooking_recipe.py` (add `to_paprika_yaml`)
- Create: `src/epic_news/utils/recipe_export.py`
- Modify: `src/epic_news/crews/cooking/cooking_crew.py` (keep only `cook` / `cook_task`)
- Modify: `src/epic_news/crews/cooking/config/agents.yaml`, `src/epic_news/crews/cooking/config/tasks.yaml` (delete `paprika_renderer`, `json_exporter`, `paprika_yaml_task`, `recipe_state_task`)
- Modify: `src/epic_news/main.py` (`generate_recipe`, lines ~701-720)
- Test: `tests/utils/test_recipe_export.py` (create), `tests/crews/test_cooking_crew_single_task.py` (create)

**Interfaces:**
- Produces: `PaprikaRecipe.to_paprika_yaml() -> str`; `export_recipe(recipe: PaprikaRecipe, yaml_path: str, json_path: str) -> None` (raises `ValueError` for paths outside `output/`); `recipe_from_result(result: Any, inputs: dict[str, Any]) -> PaprikaRecipe` in `epic_news.utils.recipe_export` (Task 11 uses both).

- [ ] **Step 1: Write the failing tests**

```python
# tests/utils/test_recipe_export.py
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
    assert PaprikaRecipe.model_validate(json.loads((tmp_path / "output/cooking/r.json").read_text())) == RECIPE


def test_refuses_paths_outside_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        recipe_export.export_recipe(RECIPE, "../evil.yaml", "output/cooking/r.json")


def test_recipe_from_result_prefers_pydantic():
    assert recipe_export.recipe_from_result(SimpleNamespace(pydantic=RECIPE), {}) is RECIPE


def test_recipe_from_result_falls_back_to_parsing(monkeypatch):
    monkeypatch.setattr(recipe_export, "parse_crewai_output", lambda result, model, inputs: RECIPE)
    assert recipe_export.recipe_from_result(SimpleNamespace(pydantic=None, raw="{}"), {}) is RECIPE
```

```python
# tests/crews/test_cooking_crew_single_task.py
from epic_news.crews.cooking.cooking_crew import CookingCrew
from epic_news.models.crews.cooking_recipe import PaprikaRecipe


def test_cooking_crew_is_one_agent_one_task():
    crew = CookingCrew().crew()
    assert len(crew.agents) == 1 and len(crew.tasks) == 1
    assert crew.tasks[0].output_pydantic is PaprikaRecipe
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils/test_recipe_export.py tests/crews/test_cooking_crew_single_task.py -v`
Expected: FAIL (module missing; crew has 3 agents and 3 tasks).

- [ ] **Step 3: Implement**

Add to `PaprikaRecipe` in `src/epic_news/models/crews/cooking_recipe.py` (after `to_template_data`):

```python
    def to_paprika_yaml(self) -> str:
        """Serialise for Paprika 3 import; non-ASCII text is kept as-is."""
        return yaml.safe_dump(self.model_dump(exclude_none=True), allow_unicode=True, sort_keys=False)
```

```python
# src/epic_news/utils/recipe_export.py
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
```

In `src/epic_news/crews/cooking/cooking_crew.py` delete the `paprika_renderer` and `json_exporter` agent methods and the `paprika_yaml_task` and `recipe_state_task` task methods; update the class docstring to "Cooking crew: one agent produces a PaprikaRecipe; YAML/JSON exports are written in Python (utils.recipe_export)." In `config/agents.yaml` delete the `paprika_renderer` and `json_exporter` entries; in `config/tasks.yaml` delete `paprika_yaml_task` and `recipe_state_task`.

In `src/epic_news/main.py`, `generate_recipe`: replace everything from `# Prefer JSON, then YAML, then fall back to CrewAI output parsing` through the end of the nested `try/except` (the block that ends with `recipe_model = parse_crewai_output(cooking_result, PaprikaRecipe, crew_inputs)`) with:

```python
        recipe_model = recipe_from_result(cooking_result, crew_inputs)
        export_recipe(recipe_model, crew_inputs["patrika_file"], crew_inputs["output_file"])
```

and add `from epic_news.utils.recipe_export import export_recipe, recipe_from_result` to the imports. Remove imports that become unused (ruff reports them).

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/utils tests/crews tests/flows -q`
Expected: PASS (update any test that expects the cooking crew's three tasks or the YAML/JSON fallback chain).

- [ ] **Step 5: Commit**

```bash
git add src/epic_news/models/crews/cooking_recipe.py src/epic_news/utils/recipe_export.py src/epic_news/crews/cooking src/epic_news/main.py tests
git commit -m "perf(cooking): one LLM pass per recipe; write Paprika YAML/JSON in Python"
```

### Task 11: Menu recipes generated in parallel

**Files:**
- Modify: `src/epic_news/main.py` (`generate_menu_designer`, the loop starting at `cooking_crew = CookingCrew().crew()`; add `_generate_menu_recipe`)
- Modify: `.env.example`
- Test: `tests/flows/test_menu_recipes_parallel.py` (create)

**Interfaces:**
- Consumes: `bounded_map` (Task 8), `recipe_from_result`, `export_recipe` (Task 10).
- Produces: `ReceptionFlow._generate_menu_recipe(recipe_spec: dict[str, Any]) -> PaprikaRecipe | None`; env `MENU_RECIPE_CONCURRENCY` (default 3).

- [ ] **Step 1: Write the failing test**

```python
# tests/flows/test_menu_recipes_parallel.py
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
        return SimpleNamespace(
            pydantic=PaprikaRecipe(name=inputs["topic"], ingredients="x", directions="y")
        )

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/flows/test_menu_recipes_parallel.py -v`
Expected: FAIL (`AttributeError: 'ReceptionFlow' object has no attribute '_generate_menu_recipe'`)

- [ ] **Step 3: Implement**

In `src/epic_news/main.py`, add to the imports: `from epic_news.utils.concurrency import bounded_map` and `from epic_news.utils.interrupt import RunCancelledError` (merge with an existing `epic_news.utils.interrupt` import if there is one; ensure `PaprikaRecipe` is imported).

Add these two methods to `ReceptionFlow`, right after `generate_menu_designer`:

```python
    def _generate_menu_recipe(self, recipe_spec: dict[str, Any]) -> PaprikaRecipe | None:
        """Generate and export one menu recipe; log and skip it on a provider failure."""
        recipe_slug = create_topic_slug(recipe_spec["name"])
        request = {
            "topic": recipe_spec["name"],
            "topic_slug": recipe_slug,
            "preferences": (
                f"Type: {recipe_spec['type']}, Day: {recipe_spec['day']}, Meal: {recipe_spec['meal']}"
            ),
            "patrika_file": f"output/cooking/{recipe_slug}.yaml",
            "output_file": f"output/cooking/{recipe_slug}.json",
        }
        try:
            recipe = recipe_from_result(kickoff_flow(CookingCrew(), request), request)
            export_recipe(recipe, request["patrika_file"], request["output_file"])
            return recipe
        except RunCancelledError:
            raise
        except Exception as e:
            self.logger.error(f"  ❌ Error with {recipe_spec['code']}: {e}")
            return None

    def _generate_menu_recipes(self, recipe_specs: list[dict[str, Any]]) -> list[PaprikaRecipe | None]:
        """Generate menu recipes in parallel (MENU_RECIPE_CONCURRENCY, default 3), in menu order."""
        return bounded_map(self._generate_menu_recipe, recipe_specs, "MENU_RECIPE_CONCURRENCY")
```

In `generate_menu_designer`, replace everything from `# Process recipes using direct CrewAI calls` through the end of the `for i, recipe_spec in enumerate(recipe_specs):` loop with:

```python
        recipes = self._generate_menu_recipes(recipe_specs)
        generated = sum(recipe is not None for recipe in recipes)
        self.logger.info(f"🍳 {generated}/{len(recipe_specs)} recipes generated")
```

Add to `.env.example`:

```bash
# Menu designer: recipes generated in parallel (default 3).
MENU_RECIPE_CONCURRENCY=3
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/flows tests/utils -q`
Expected: PASS

- [ ] **Step 5: LIVE — measure**

Run: `env -u VIRTUAL_ENV uv run python scripts/bench_flow.py menu`
Check: one `.yaml` and one `.json` per menu recipe under `output/cooking/`, each loadable (`yaml.safe_load`, `json.load`) and in French. Add the row (Change = `E3 single-pass recipes + parallel`).

- [ ] **Step 6: Commit and open PR 4**

```bash
git add src/epic_news/main.py .env.example tests/flows/test_menu_recipes_parallel.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "perf(menu): generate menu recipes in parallel (MENU_RECIPE_CONCURRENCY=3)"
```

Controller: full suite, ruff, mypy; open PR 4 (Tasks 10–11).

---

## PR 5 — Routing in one call (spec E5)

### Task 12: Routing evaluation set and baseline

**Files:**
- Create: `scripts/eval_routing.py`
- Create: `scripts/routing_eval_requests.json`
- Test: `tests/scripts/test_eval_routing.py` (create)

**Interfaces:**
- Produces: `python scripts/eval_routing.py` printing per-request lines and `accuracy=<correct>/<total>`; `score(results: list[tuple[str, str]]) -> tuple[int, int]` (pairs of expected, actual).

- [ ] **Step 1: Write the failing test**

```python
# tests/scripts/test_eval_routing.py
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location("eval_routing", Path("scripts/eval_routing.py"))
eval_routing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_routing)


def test_score_counts_exact_matches():
    assert eval_routing.score([("POEM", "POEM"), ("MENU", "COOKING"), ("PESTEL", "PESTEL")]) == (2, 3)


def test_dataset_covers_every_category():
    from epic_news.models.content_state import CrewCategories

    data = json.loads(Path("scripts/routing_eval_requests.json").read_text(encoding="utf-8"))
    expected = {row["expected"] for row in data}
    categories = set(CrewCategories.to_dict()) - {"UNKNOWN"}
    assert categories <= expected
    assert len(data) >= 25
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/scripts/test_eval_routing.py -v`
Expected: FAIL (script missing)

- [ ] **Step 3: Implement**

```python
# scripts/eval_routing.py
"""Measure routing accuracy: extraction + classification on a fixed request set.

Usage: env -u VIRTUAL_ENV uv run python scripts/eval_routing.py
LIVE: runs the extraction (and, when needed, classification) crews per request.
"""

import json
from pathlib import Path

from epic_news.main import ReceptionFlow
from epic_news.utils.directory_utils import ensure_output_directories

_DATA = Path(__file__).with_name("routing_eval_requests.json")


def score(results: list[tuple[str, str]]) -> tuple[int, int]:
    return sum(expected == actual for expected, actual in results), len(results)


def route(request: str) -> str:
    flow = ReceptionFlow(user_request=request)
    flow.state.user_request = request
    flow.extract_info()
    flow.classify()
    return flow.state.selected_crew


def main() -> None:
    ensure_output_directories()
    rows = json.loads(_DATA.read_text(encoding="utf-8"))
    results = []
    for row in rows:
        actual = route(row["request"])
        results.append((row["expected"], actual))
        mark = "OK " if actual == row["expected"] else "BAD"
        print(f"{mark} expected={row['expected']:<26} actual={actual:<26} {row['request']}")
    correct, total = score(results)
    print(f"accuracy={correct}/{total}")


if __name__ == "__main__":
    main()
```

```json
[
  {"request": "Écris-moi un poème sur l'automne au bord du Léman", "expected": "POEM"},
  {"request": "Write a short poem about the sea", "expected": "POEM"},
  {"request": "Donne-moi la recette du risotto aux cèpes", "expected": "COOKING"},
  {"request": "How do I make a classic French omelette?", "expected": "COOKING"},
  {"request": "Prépare un menu de la semaine pour 4 personnes avec liste de courses", "expected": "MENU"},
  {"request": "Plan my meals for the next 5 days, vegetarian", "expected": "MENU"},
  {"request": "Quel aspirateur robot acheter pour moins de 400 CHF ?", "expected": "SHOPPING"},
  {"request": "Compare the best noise-cancelling headphones to buy", "expected": "SHOPPING"},
  {"request": "Fais-moi le point financier du jour sur mon portefeuille actions et crypto", "expected": "FINDAILY"},
  {"request": "Donne-moi les actualités générales du jour", "expected": "NEWSDAILY"},
  {"request": "What are today's world headlines?", "expected": "NEWSDAILY"},
  {"request": "Quelles sont les dernières nouvelles de l'entreprise Nestlé ?", "expected": "COMPANY_NEWS"},
  {"request": "Quoi de neuf dans le framework CrewAI cette année ?", "expected": "DEEPRESEARCH"},
  {"request": "Deep dive on the state of the art in solid-state batteries", "expected": "DEEPRESEARCH"},
  {"request": "Planifie un voyage d'une semaine en Sicile en famille", "expected": "HOLIDAY_PLANNER"},
  {"request": "Plan a 3-day trip to Lisbon for two adults", "expected": "HOLIDAY_PLANNER"},
  {"request": "Fais-moi un résumé du livre L'Étranger de Camus", "expected": "BOOK_SUMMARY"},
  {"request": "Prépare ma réunion de demain avec la direction de Swisscom", "expected": "MEETING_PREP"},
  {"request": "Trouve des prospects commerciaux pour notre logiciel RH chez les PME genevoises", "expected": "SALES_PROSPECTING"},
  {"request": "Fais un rapport OSINT sur l'entreprise Logitech", "expected": "OPEN_SOURCE_INTELLIGENCE"},
  {"request": "Analyse PESTEL du secteur bancaire suisse", "expected": "PESTEL"},
  {"request": "PESTLE analysis of the EU electric car market", "expected": "PESTEL"},
  {"request": "Fais-moi le résumé hebdomadaire de mes flux RSS", "expected": "RSS"},
  {"request": "Quel est le saint du jour ?", "expected": "SAINT"},
  {"request": "Daily saint please", "expected": "SAINT"}
]
```

- [ ] **Step 4: Run the tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/scripts/test_eval_routing.py -v`
Expected: PASS. If a category name in the dataset does not exist in `CrewCategories`, fix the dataset (never the categories).

- [ ] **Step 5: LIVE — baseline accuracy (current two-step routing)**

Run: `env -u VIRTUAL_ENV uv run python scripts/eval_routing.py`
Record `accuracy=…` and the list of BAD lines in the results file (Change = `E5 baseline routing`).

- [ ] **Step 6: Commit**

```bash
git add scripts/eval_routing.py scripts/routing_eval_requests.json tests/scripts/test_eval_routing.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "feat(scripts): add routing evaluation set and record baseline accuracy"
```

### Task 13: Extraction selects the crew; ClassifyCrew only as fallback

**Files:**
- Create: `src/epic_news/config/routing_guide.py`
- Modify: `src/epic_news/crews/classify/config/tasks.yaml` (`classification_task.description`)
- Modify: `src/epic_news/crews/information_extraction/config/tasks.yaml` (`comprehensive_information_extraction_task.description`)
- Modify: `src/epic_news/models/extracted_info.py` (add `selected_crew`)
- Modify: `src/epic_news/main.py` (`extract_info`, `classify`, new module function `_category_from_classification`)
- Test: `tests/flows/test_routing_single_call.py` (create)

**Interfaces:**
- Consumes: `ROUTING_GUIDE` from Task 13's new module in both crews.
- Produces: `ROUTING_GUIDE: str`, `routing_categories() -> str` in `epic_news.config.routing_guide`; `ExtractedInfo.selected_crew: str | None`; `_category_from_classification(result: Any, categories: dict[str, str]) -> str` in `epic_news.main`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/flows/test_routing_single_call.py
from types import SimpleNamespace

import epic_news.main as main_mod
from epic_news.models.extracted_info import ExtractedInfo


def _flow_with(selected):
    flow = main_mod.ReceptionFlow(user_request="req")
    flow.state.user_request = "req"
    flow.state.extracted_info = ExtractedInfo(main_subject_or_activity="x", selected_crew=selected)
    return flow


def test_valid_extracted_crew_skips_classify_crew(monkeypatch):
    calls = []
    monkeypatch.setattr(main_mod, "kickoff_flow", lambda crew, inputs: calls.append(crew) or None)
    flow = _flow_with("pestel ")
    flow.classify()
    assert flow.state.selected_crew == "PESTEL"
    assert calls == []


def test_unknown_extracted_crew_falls_back_to_classify_crew(monkeypatch):
    seen = {}

    def fake_kickoff(crew, inputs):
        seen["crew"] = type(crew).__name__
        seen["inputs"] = inputs
        return SimpleNamespace(pydantic=SimpleNamespace(selected_crew="cooking"))

    monkeypatch.setattr(main_mod, "kickoff_flow", fake_kickoff)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = _flow_with("NOT_A_CREW")
    flow.classify()
    assert seen["crew"] == "ClassifyCrew"
    assert "routing_guide" in seen["inputs"]
    assert flow.state.selected_crew == "COOKING"


def test_missing_extraction_falls_back(monkeypatch):
    monkeypatch.setattr(
        main_mod, "kickoff_flow", lambda crew, inputs: SimpleNamespace(pydantic=SimpleNamespace(selected_crew="POEM"))
    )
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = _flow_with(None)
    flow.classify()
    assert flow.state.selected_crew == "POEM"


def test_classification_without_pydantic_is_unknown():
    categories = {"POEM": "POEM", "UNKNOWN": "UNKNOWN"}
    assert main_mod._category_from_classification(SimpleNamespace(pydantic=None, raw="POEM"), categories) == "UNKNOWN"
    assert main_mod._category_from_classification(
        SimpleNamespace(pydantic=SimpleNamespace(selected_crew="poem")), categories
    ) == "POEM"


def test_extraction_receives_categories_and_guide(monkeypatch):
    seen = {}

    def fake_kickoff(crew, inputs):
        seen.update(inputs)
        return SimpleNamespace(tasks_output=[SimpleNamespace(raw="brief")], pydantic=ExtractedInfo())

    monkeypatch.setattr(main_mod, "kickoff_flow", fake_kickoff)
    monkeypatch.setattr(main_mod, "dump_crewai_state", lambda *a, **k: None)
    flow = main_mod.ReceptionFlow(user_request="req")
    flow.state.user_request = "req"
    flow.extract_info()
    assert seen["user_request"] == "req"
    assert "PESTEL" in seen["categories"] and "UNKNOWN" not in seen["categories"]
    assert "IMPORTANT DISTINCTIONS" in seen["routing_guide"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u VIRTUAL_ENV uv run pytest tests/flows/test_routing_single_call.py -v`
Expected: FAIL (`ExtractedInfo` has no `selected_crew`; `_category_from_classification` missing).

- [ ] **Step 3: Implement**

Create `src/epic_news/config/routing_guide.py`. `ROUTING_GUIDE` below is exactly the text the classifier receives today: the part of `classification_task.description` (as loaded by YAML, which folds the lines into one paragraph) from `IMPORTANT DISTINCTIONS:` through `→ PESTEL`. Verify it with
`env -u VIRTUAL_ENV uv run python -c "import yaml; from epic_news.config.routing_guide import ROUTING_GUIDE as g; d=yaml.safe_load(open('src/epic_news/crews/classify/config/tasks.yaml'))['classification_task']['description']; print(g in d)"` → `True` (run it **before** editing the YAML).

```python
"""Routing guide shared by the extraction crew (primary) and ClassifyCrew (fallback).

Single source for the category descriptions and keyword hints used to pick a crew.
"""

from epic_news.models.content_state import CrewCategories

ROUTING_GUIDE = (
    'IMPORTANT DISTINCTIONS: - COOKING: For requests about individual recipes, single '
    'dishes, specific cooking techniques, or ingredient-focused queries - MENU: For '
    'requests about meal planning, weekly menus, menu design, multiple recipes for a '
    'period, shopping lists, or dietary planning over time - SHOPPING: For product '
    'purchase advice, price comparisons, product recommendations, buying guides, or '
    'consumer advice requests - FINDAILY: For financial advice, investment '
    'recommendations, portfolio analysis, stock market insights, crypto analysis, '
    'financial planning, daily financial reports - NEWSDAILY: For GENERAL daily news '
    "digests spanning many topics — world and current events, breaking news, the day's "
    'headlines. NOT for research about one specific subject, technology, product, or '
    'software framework (use DEEPRESEARCH). - COMPANY_NEWS: For company-specific news, '
    'corporate updates, business intelligence about specific companies or organizations -'
    ' DEEPRESEARCH: For in-depth research on ONE specific subject — a technology, '
    'software framework, library, SDK, programming language, scientific concept, method, '
    'or the question "what\'s new / latest developments / state of the art in X". Prefer '
    'this over NEWSDAILY whenever the request targets a specific topic rather than '
    'general current events. - HOLIDAY_PLANNER: For vacation planning, travel '
    'itineraries, destination research - BOOK_SUMMARY: For book summaries, reading '
    'recommendations, literary analysis, book reviews, author information, literature '
    'queries, book analysis, tell me about book, livre, roman, auteur - MEETING_PREP: For'
    ' meeting preparation, agenda creation, research for meetings - PESTEL: For PESTEL / '
    'PESTLE strategic analysis requests covering Political, Economic, Social, '
    'Technological, Environmental, Legal dimensions on any subject (company, sector, '
    'country, product). Triggers: "PESTEL", "PESTLE", "analyse PESTEL", "rapport PESTEL",'
    ' "PESTEL analysis", "macro-environment analysis", "strategic environment". - And so '
    'on for other categories... Pay special attention to keywords like: - "menu", '
    '"weekly", "planner", "planning", "multiple recipes", "shopping list" → MENU - '
    '"recipe", "dish", "cooking technique", "ingredient", "single meal", "risotto" → '
    'COOKING - "achat", "acheter", "conseil", "prix", "comparaison", "recommandation", '
    '"produit" → SHOPPING - "financier", "finance", "investissement", "bourse", "crypto",'
    ' "portefeuille", "conseil financier" → FINDAILY - "actualités générales", "nouvelles'
    ' générales", "general news", "événements", "journal", "information" → NEWSDAILY - '
    '"company news", "corporate news", "news for company", "enterprise news", "business '
    'updates", "company updates" → COMPANY_NEWS - "nouveautés d\'un '
    'framework/langage/librairie", "framework", "librairie", "SDK", "latest features", '
    '"developments in", "state of the art", "deep dive", "veille technologique", '
    '"recherche approfondie", "crewai", "python framework" → DEEPRESEARCH - "book", '
    '"livre", "roman", "auteur", "author", "tell me about",  → BOOK_SUMMARY - "saint", '
    '"saint du jour", "daily saint", "saint daily" → SAINT - "poem", "poème", "poetry", '
    '"poésie" → POEM - "pestel", "pestle", "analyse pestel", "rapport pestel", "pestel '
    'analysis", "macro-environment", "political economic social technological '
    'environmental legal" → PESTEL'
)


def routing_categories() -> str:
    """Comma-separated crew categories offered to the model (UNKNOWN excluded)."""
    return ", ".join(name for name in CrewCategories.to_dict() if name != CrewCategories.UNKNOWN)
```

If importing `CrewCategories` here creates a circular import (check with `env -u VIRTUAL_ENV uv run python -c "import epic_news.config.routing_guide"`), move `routing_categories` into `src/epic_news/main.py` as a module-level function instead and keep `routing_guide.py` free of model imports.

In `src/epic_news/crews/classify/config/tasks.yaml`, replace the moved block in `classification_task.description` with the single line:

```yaml
    {routing_guide}
```

so the description reads: request line, `{categories}`, the two sentences about intent, then `{routing_guide}`, then `Provide your final classification decision along with a brief explanation of your reasoning.`

In `src/epic_news/crews/information_extraction/config/tasks.yaml`, in `comprehensive_information_extraction_task.description`, insert before `Here is the user request you need to analyze:`:

```yaml
    ALSO choose `selected_crew`: the ONE team that should handle the request,
    among exactly these names: {categories}. Use this guide:
    {routing_guide}
    Write the name in capitals exactly as listed. If no team clearly fits,
    leave selected_crew null.
```

In `src/epic_news/models/extracted_info.py`, add as the last field of `ExtractedInfo`:

```python
    selected_crew: str | None = Field(
        default=None,
        description="The single team that should handle the request: one of the category names "
        "listed in the task, in capitals, or null when no team clearly fits.",
    )
```

In `src/epic_news/main.py`:

1. Imports: add `from epic_news.config.routing_guide import ROUTING_GUIDE, routing_categories`.
2. Module level (near `CLASSIFY_DECISION_FILE`):

```python
def _category_from_classification(result: Any, categories: dict[str, str]) -> str:
    """Category chosen by ClassifyCrew's typed output; UNKNOWN when missing or invalid."""
    model = getattr(result, "pydantic", None)
    selected = (getattr(model, "selected_crew", "") or "").strip().upper()
    return selected if selected in categories else CrewCategories.UNKNOWN
```

3. `extract_info`: change the kickoff call to

```python
        extracted_data = kickoff_flow(
            extraction_crew,
            {
                "user_request": self.state.user_request,
                "categories": routing_categories(),
                "routing_guide": ROUTING_GUIDE,
            },
        )
```

4. `classify`: replace everything from `# Prepare input data for classification using the centralized method from ContentState.` through `self.state.selected_crew = parsed_category` with:

```python
        candidate = (getattr(self.state.extracted_info, "selected_crew", None) or "").strip().upper()
        if candidate in self.state.categories and candidate != CrewCategories.UNKNOWN:
            parsed_category = candidate
            self.logger.info(f"✅ Crew selected during extraction: {parsed_category}")
        else:
            self.logger.info("🔁 Extraction gave no usable crew; falling back to ClassifyCrew")
            inputs = {**self.state.to_crew_inputs(), "routing_guide": ROUTING_GUIDE}
            classification_result = kickoff_flow(ClassifyCrew(), inputs)
            dump_crewai_state(classification_result, "CLASSIFICATION")
            parsed_category = _category_from_classification(classification_result, self.state.categories)

        self.state.selected_crew = parsed_category
```

and change the final log line to `self.logger.info(f"✅ Classification complete. Selected crew: {self.state.selected_crew}")` (the `raw_classification` variable no longer exists). Keep the `self.state.output_file = CLASSIFY_DECISION_FILE` line and the `output_format` line unchanged. Confirm `CrewCategories` is imported in `main.py` (add it to the existing `epic_news.models.content_state` import if not).

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/flows tests/crews tests/models -q` (and the full suite once)
Expected: PASS. Update `tests/flows/test_extract_info_enriched_brief.py` or router tests only where they assert the old substring parsing or the exact kickoff inputs.

- [ ] **Step 5: LIVE — accuracy after the change**

Run: `env -u VIRTUAL_ENV uv run python scripts/eval_routing.py`
Acceptance: `accuracy` greater than or equal to the Task 12 baseline. If lower, report the BAD lines to the controller instead of committing; do not tune the dataset to pass. Record the result (Change = `E5 single-call routing`) and how many requests used the ClassifyCrew fallback (count `🔁` log lines).

- [ ] **Step 6: Commit and open PR 5**

```bash
git add src/epic_news/config/routing_guide.py src/epic_news/crews/classify/config/tasks.yaml src/epic_news/crews/information_extraction/config/tasks.yaml src/epic_news/models/extracted_info.py src/epic_news/main.py tests docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "perf(routing): pick the crew during extraction; ClassifyCrew only as fallback"
```

Controller: full suite, ruff, mypy; open PR 5 (Tasks 12–13) with baseline and new accuracy.

---

## PR 6 — Cross-reference synthesis (spec E6)

### Task 14: Synthesis mode behind a flag, compared live

**Files:**
- Create: `src/epic_news/crews/cross_reference_report_crew/synthesis_crew.py`
- Create: `src/epic_news/crews/cross_reference_report_crew/config/synthesis_tasks.yaml`
- Modify: `src/epic_news/main.py` (`_run_cross_reference_report`; new module function `_osint_reports_json`)
- Modify: `.env.example`
- Test: `tests/crews/test_cross_reference_synthesis.py` (create)

**Interfaces:**
- Produces: `CrossReferenceSynthesisCrew` (one agent `osint_reporter`, one task `osint_synthesis`, `output_pydantic=CrossReferenceReport`); `_osint_reports_json(osint_dir: Path) -> str`; env `CROSS_REFERENCE_MODE` = `research` (default, current crew) | `synthesis`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/crews/test_cross_reference_synthesis.py
import json
from pathlib import Path

import epic_news.main as main_mod
from epic_news.crews.cross_reference_report_crew.synthesis_crew import CrossReferenceSynthesisCrew
from epic_news.models.crews.cross_reference_report import CrossReferenceReport


def test_synthesis_crew_is_one_tool_free_task():
    crew = CrossReferenceSynthesisCrew().crew()
    assert len(crew.tasks) == 1 and len(crew.agents) == 1
    assert crew.agents[0].tools == []
    assert crew.tasks[0].output_pydantic is CrossReferenceReport


def test_osint_reports_json_reads_available_reports(tmp_path: Path):
    (tmp_path / "company_profile.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    (tmp_path / "tech_stack.json").write_text("not json", encoding="utf-8")
    payload = json.loads(main_mod._osint_reports_json(tmp_path))
    assert payload["company_profile"] == {"x": 1}
    assert "tech_stack" not in payload
    assert "legal_analysis" not in payload


def test_mode_defaults_to_research(monkeypatch):
    monkeypatch.delenv("CROSS_REFERENCE_MODE", raising=False)
    assert main_mod._cross_reference_mode() == "research"
    monkeypatch.setenv("CROSS_REFERENCE_MODE", " Synthesis ")
    assert main_mod._cross_reference_mode() == "synthesis"
    monkeypatch.setenv("CROSS_REFERENCE_MODE", "other")
    assert main_mod._cross_reference_mode() == "research"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews/test_cross_reference_synthesis.py -v`
Expected: FAIL (module missing)

- [ ] **Step 3: Implement**

`src/epic_news/crews/cross_reference_report_crew/config/synthesis_tasks.yaml`:

```yaml
---
osint_synthesis:
  description: >
    You receive the OSINT reports already produced for {target} as JSON, one
    entry per report (company profile, tech stack, web presence, HR intelligence,
    legal analysis, geospatial analysis; some may be missing). Write ONE integrated
    global intelligence report: an executive summary, cross-cutting findings that
    combine several reports, contradictions between reports, key risks, and the
    information gaps that remain. Use only facts present in these reports; do not
    invent sources or numbers. Reports:
    {osint_reports}
  expected_output: >
    A CrossReferenceReport object synthesising every available report on {target}.
  agent: osint_reporter
  output_file: '{output_file}'
```

```python
# src/epic_news/crews/cross_reference_report_crew/synthesis_crew.py
"""Cross-reference report by synthesis: one tool-free task over the six OSINT reports.

Alternative to CrossReferenceReportCrew (which re-researches the target); selected with
CROSS_REFERENCE_MODE=synthesis while the two are compared (efficiency spec E6).
"""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from epic_news.config.llm_config import LLMConfig
from epic_news.models.crews.cross_reference_report import CrossReferenceReport


@CrewBase
class CrossReferenceSynthesisCrew:
    """Synthesise the OSINT reports into one CrossReferenceReport."""

    agents_config: dict[str, Any] = "config/agents.yaml"  # type: ignore[assignment]
    tasks_config: dict[str, Any] = "config/synthesis_tasks.yaml"  # type: ignore[assignment]

    @agent
    def osint_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["osint_reporter"],
            tools=[],
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
        )

    @task
    def osint_synthesis(self) -> Task:
        return Task(  # type: ignore[call-arg]
            config=self.tasks_config["osint_synthesis"],
            output_pydantic=CrossReferenceReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # type: ignore[attr-defined]
            tasks=self.tasks,  # type: ignore[attr-defined]
            process=Process.sequential,
            verbose=True,
        )
```

If `@CrewBase` fails because `config/agents.yaml` also defines `osint_researcher` (an agent this crew does not declare), copy only the `osint_reporter` entry into `config/synthesis_agents.yaml` and point `agents_config` at it.

In `src/epic_news/main.py`, at module level:

```python
_OSINT_SOURCE_FILES = (
    "company_profile",
    "tech_stack",
    "web_presence",
    "hr_intelligence",
    "legal_analysis",
    "geospatial_analysis",
)


def _cross_reference_mode() -> str:
    """CROSS_REFERENCE_MODE: 'synthesis' or the default 'research'."""
    mode = os.getenv("CROSS_REFERENCE_MODE", "research").strip().lower()
    return mode if mode in {"research", "synthesis"} else "research"


def _osint_reports_json(osint_dir: Path) -> str:
    """Compact JSON of the OSINT reports present in osint_dir (unreadable files skipped)."""
    reports: dict[str, Any] = {}
    for name in _OSINT_SOURCE_FILES:
        path = osint_dir / f"{name}.json"
        try:
            reports[name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.warning(f"⚠️ OSINT report {path} missing or unreadable; left out of the synthesis")
    return json.dumps(reports, ensure_ascii=False, separators=(",", ":"))
```

In `_run_cross_reference_report`, replace

```python
        output = await akickoff_flow(CrossReferenceReportCrew(), crew_inputs)
```

with

```python
        if _cross_reference_mode() == "synthesis":
            crew_inputs["osint_reports"] = _osint_reports_json(Path("output/osint"))
            self.logger.info("🔗 Cross-reference mode: synthesis of the OSINT reports")
            output = await akickoff_flow(CrossReferenceSynthesisCrew(), crew_inputs)
        else:
            output = await akickoff_flow(CrossReferenceReportCrew(), crew_inputs)
```

and add `from epic_news.crews.cross_reference_report_crew.synthesis_crew import CrossReferenceSynthesisCrew` to the imports. `_osint_reports_json` is a module-level function, so it uses Loguru's `logger` (add `from loguru import logger` if `main.py` does not import it yet), not `self.logger`. Check `crew_inputs` contains `target` (the existing tasks use `{target}`); if it does not, set `crew_inputs.setdefault("target", company)`.

Add to `.env.example`:

```bash
# OSINT cross-reference: 'research' (re-researches the target, default) or
# 'synthesis' (one task over the six OSINT reports; under evaluation).
CROSS_REFERENCE_MODE=research
```

- [ ] **Step 4: Run tests**

Run: `env -u VIRTUAL_ENV uv run pytest tests/crews tests/flows -q`
Expected: PASS

- [ ] **Step 5: LIVE — side-by-side comparison for the user**

```bash
env -u VIRTUAL_ENV CROSS_REFERENCE_MODE=research uv run python scripts/bench_flow.py osint
mkdir -p output/osint/compare && cp output/osint/global_report.html output/osint/compare/research.html
env -u VIRTUAL_ENV CROSS_REFERENCE_MODE=synthesis uv run python scripts/bench_flow.py osint
cp output/osint/global_report.html output/osint/compare/synthesis.html
```

Record both cross-reference crew rows (seconds, tokens) in the results file (Change = `E6 research` / `E6 synthesis`). Stop and hand the two HTML files to the controller: **the user decides** (spec decision 5). Do not change the default here.

- [ ] **Step 6: Commit**

```bash
git add src/epic_news/crews/cross_reference_report_crew src/epic_news/main.py .env.example tests/crews/test_cross_reference_synthesis.py docs/superpowers/plans/2026-10-04-efficiency-wave-results.md
git commit -m "feat(osint): add cross-reference synthesis mode for comparison"
```

### Task 15: Apply the user's E6 decision

Run only after the user has compared `output/osint/compare/research.html` and `synthesis.html`.

**If the user approves synthesis:**

**Files:**
- Modify: `src/epic_news/main.py` (`_cross_reference_mode` default → `synthesis`, or remove the flag and always use synthesis — use the user's choice)
- Delete: the four `intelligence_*` tasks, `html_report_generation` and the `osint_researcher` agent from `CrossReferenceReportCrew` if the flag is removed; then delete `cross_reference_report_crew.py`'s research path entirely and rename `CrossReferenceSynthesisCrew` usage accordingly
- Modify: `.env.example`, tests referencing the research crew

- [ ] **Step 1: Update `tests/crews/test_cross_reference_synthesis.py::test_mode_defaults_to_research`** to expect the new default (or delete it with the flag), and run it to see it fail.
- [ ] **Step 2: Apply the change; run `env -u VIRTUAL_ENV uv run pytest -q`; expected PASS.**
- [ ] **Step 3: Commit** `perf(osint): synthesise the cross-reference report from the OSINT reports`.

**If the user keeps research:** delete `synthesis_crew.py`, `synthesis_tasks.yaml`, `_cross_reference_mode`, `_osint_reports_json`, `_OSINT_SOURCE_FILES`, the env entry and the test file; run the suite; commit `revert(osint): keep the research cross-reference report`.

Controller: full suite, ruff, mypy; open PR 6 (Tasks 14–15) with the comparison numbers and the user's decision.
