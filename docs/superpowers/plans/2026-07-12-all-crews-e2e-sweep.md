# All-Crews End-to-End Verification Sweep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run all 15 routable ReceptionFlow paths end-to-end on the current Gemini+ReAct stack (POEM excluded; holiday already green) and fix every latent output/render/email failure so each delivers a valid report to the test inbox.

**Architecture:** A one-line env override in `kickoff()` lets a bash driver run `crewai flow kickoff` once per flow with the routing request in `EPIC_NEWS_REQUEST` and the recipient forced to the test inbox via the existing `MAIL` env var. Each flow is then verified cheap→expensive; any failure triggers a systematic-debugging → fix → test → re-verify loop, one commit per root cause.

**Tech Stack:** Python 3.13, uv, CrewAI 1.15 (flow kickoff), LiteLLM → native Gemini `gemini/gemini-3.5-flash`, pytest, ruff, mypy, Loguru, bash.

## Global Constraints

- Package manager is **uv only** — `uv run pytest`, `uv add`; never `pip`/`poetry`.
- Crews run **only** via `crewai flow kickoff` — never invoke a crew directly in Python.
- LLM config comes **only** from `LLMConfig`; the stack is native Gemini `gemini/gemini-3.5-flash` with forced ReAct (already global). Never hardcode model/timeouts.
- Sweep env vars: `MAIL=fred.jacquet@gmail.com` (recipient) and `EPIC_NEWS_REQUEST` (routing request).
- Logging via **Loguru** (`from loguru import logger`), not stdlib logging.
- **Never** `git add -A` / `git add .`. Stage files explicitly. Do **not** stage `src/epic_news/main.py` changes beyond the Task 1 override line (it is the user's sentinel file).
- Every fix commit ends with the repo's trailer lines and passes pre-commit (ruff lint, ruff format, yamllint, mypy).
- A Gemini 5xx / rate-limit / timeout is **transient**: retry the flow once before treating it as a bug. A classify **misroute** is fixed by adjusting the request phrasing, not counted as a crew bug.
- Fixes use **superpowers:systematic-debugging**; add a unit test whenever the fix has a testable surface (renderer / extractor / builder / util).

---

## Per-Flow Verification Procedure (applies to Tasks 3–16)

Every flow task below executes this exact procedure with its row's `CATEGORY` and `REQUEST`. It is written once here; each task supplies only its parameters.

1. Truncate the error log so failures are isolated to this run:
   `: > logs/epic_news_error.log`
2. Run the flow (real LLM call; may take from ~30 s to ~15 min):
   `MAIL=fred.jacquet@gmail.com EPIC_NEWS_REQUEST="<REQUEST>" crewai flow kickoff`
   — or `scripts/verify_all_crews.sh <CATEGORY>` once Task 2 exists.
3. **PASS** iff all of:
   - kickoff exit code `0`;
   - `logs/epic_news_error.log` is 0 bytes;
   - the log contains a fresh `📨 Email delivered to fred.jacquet@gmail.com` line;
   - a non-empty report file for this crew was written under `output/` during this run.
4. If **PASS**: record `CATEGORY → PASS` in the results table (Task 17) and move to the next task.
5. If the failure is **transient** (Gemini 5xx / 429 / timeout): re-run step 2 once. Still failing → treat as a real failure.
6. If the failure is a **misroute** (a different crew ran, per the `Selected crew:` log line): adjust `REQUEST` to be unambiguous for `CATEGORY`, update the driver + this task's row, re-run. Not a crew bug.
7. If **real failure**: invoke `superpowers:systematic-debugging`. Find the root cause, implement the minimal fix, add a unit test if the fix has a testable surface, re-run step 2 until PASS, then commit **only the fix files** (never `main.py` beyond Task 1):
   `git add <fix files> && git commit -m "fix(<area>): <root cause>"`
8. Record `CATEGORY → PASS (fix <commit>)` in the results table.

**Known failure classes to expect** (from the holiday journey): markdown leaking into HTML (renderers must call `render_markdown_block/inline`, not `tag.string`); pandoc/DOCX input needing sanitization; a non-`str` value reaching a `str` field (`TaskOutput.raw`, a Pydantic field); LLM anonymizing PII in deterministic tool args; empty/malformed crew JSON breaking an extractor.

---

## Task 1: `EPIC_NEWS_REQUEST` env override in `kickoff()`

**Files:**
- Modify: `src/epic_news/main.py` (inside `def kickoff(...)`, ~line 1494 and ~line 1524)
- Test: `tests/flows/test_kickoff_request_override.py`

**Interfaces:**
- Produces: `kickoff(user_input: str | None = None)` resolves the request as
  `user_input or os.getenv("EPIC_NEWS_REQUEST") or <hardcoded query>`, then constructs
  `ReceptionFlow(user_request=<resolved>)`. Explicit `user_input` still wins over the env var.

- [ ] **Step 1: Write the failing test**

```python
# tests/flows/test_kickoff_request_override.py
"""kickoff() must honor EPIC_NEWS_REQUEST so the sweep can vary the request
without editing main.py, while falling back to the hardcoded query when unset."""
from unittest.mock import patch

import epic_news.main as main


def test_env_request_seeds_the_flow(monkeypatch):
    monkeypatch.setenv("EPIC_NEWS_REQUEST", "get the rss weekly report")
    with patch.object(main, "ReceptionFlow") as MockFlow:
        MockFlow.return_value.kickoff.return_value = None
        main.kickoff()
    assert MockFlow.call_args.kwargs["user_request"] == "get the rss weekly report"


def test_falls_back_to_hardcoded_query_when_env_unset(monkeypatch):
    monkeypatch.delenv("EPIC_NEWS_REQUEST", raising=False)
    with patch.object(main, "ReceptionFlow") as MockFlow:
        MockFlow.return_value.kickoff.return_value = None
        main.kickoff()
    assert MockFlow.call_args.kwargs["user_request"]  # non-empty default


def test_explicit_arg_wins_over_env(monkeypatch):
    monkeypatch.setenv("EPIC_NEWS_REQUEST", "from env")
    with patch.object(main, "ReceptionFlow") as MockFlow:
        MockFlow.return_value.kickoff.return_value = None
        main.kickoff(user_input="explicit arg")
    assert MockFlow.call_args.kwargs["user_request"] == "explicit arg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/flows/test_kickoff_request_override.py -v`
Expected: `test_env_request_seeds_the_flow` FAILS (env var ignored; request is the hardcoded query).

- [ ] **Step 3: Add the override**

In `src/epic_news/main.py`, at the very top of `kickoff()` body (before `query` is built):

```python
def kickoff(user_input: str | None = None):
    # Sweep/automation hook: let EPIC_NEWS_REQUEST drive the request without
    # editing the hardcoded query below. An explicit user_input arg still wins.
    user_input = user_input or os.getenv("EPIC_NEWS_REQUEST") or None
```

Leave the existing `request = (user_input if user_input else query ...)` unchanged.
Confirm `import os` is already present at the top of the file (it is).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/flows/test_kickoff_request_override.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit (test file + the single main.py line)**

```bash
git add tests/flows/test_kickoff_request_override.py src/epic_news/main.py
git commit -m "feat(flow): honor EPIC_NEWS_REQUEST env override in kickoff()"
```

Note: this is the **only** sanctioned `main.py` change in this plan.

---

## Task 2: `scripts/verify_all_crews.sh` sweep driver

**Files:**
- Create: `scripts/verify_all_crews.sh`
- Test: manual smoke (bash script; no unit test framework for shell here)

**Interfaces:**
- Produces: `scripts/verify_all_crews.sh [CATEGORY]` — runs all flows in cheap→expensive
  order, or a single flow when `CATEGORY` (e.g. `COOKING`) is given. Sets `MAIL` and
  `EPIC_NEWS_REQUEST`, runs `crewai flow kickoff`, prints a `RESULT <CATEGORY>:` line.

- [ ] **Step 1: Write the driver**

```bash
#!/usr/bin/env bash
# End-to-end verification driver for ReceptionFlow crews.
#   scripts/verify_all_crews.sh            # all flows, cheap -> expensive
#   scripts/verify_all_crews.sh COOKING    # a single flow by category label
# Requires Task 1 (EPIC_NEWS_REQUEST override) to be in place.
set -uo pipefail
cd "$(dirname "$0")/.."

export MAIL="fred.jacquet@gmail.com"

# "CATEGORY|routing request" — cheap -> expensive (POEM excluded; holiday already green)
FLOWS=(
  "SAINT|Donne moi le saint du jour en français"
  "COOKING|Get me the recipe for Salade César"
  "SHOPPING|Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus éthique"
  "BOOK_SUMMARY|tell me all about the book: Clamser à Tataouine de Raphaël Quenard"
  "NEWSDAILY|get the daily news report"
  "FINDAILY|get the financial daily report"
  "COMPANY_NEWS|get me all news for company JT International SA"
  "RSS|get the rss weekly report"
  "MENU|Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French"
  "MEETING_PREP|Meeting preparation for JT International SA with the CTO to discuss PowerFlex deployment in Switzerland"
  "PESTEL|Fais moi un rapport PESTEL à propos de la société Pictet aujourd'hui en français"
  "SALES_PROSPECTING|let's find a sales prospect at Temenos to sell our product: Dell PowerFlex"
  "DEEPRESEARCH|conduct a deep research study on the progress of quantum computing and applications in cryptography"
  "OPEN_SOURCE_INTELLIGENCE|Complete OSINT analysis of Mistral.AI"
)

run_one() {
  local label="$1" request="$2"
  echo "================ $label ================"
  : > logs/epic_news_error.log 2>/dev/null || true
  EPIC_NEWS_REQUEST="$request" crewai flow kickoff
  local code=$?
  local errbytes
  errbytes=$(wc -c < logs/epic_news_error.log 2>/dev/null | tr -d ' ')
  local delivered="no"
  grep -q "Email delivered to fred.jacquet@gmail.com" logs/epic_news.log 2>/dev/null \
    && delivered="yes"
  echo "RESULT $label: exit=$code error_log_bytes=${errbytes:-?} email_delivered=$delivered"
  echo "---- last 8 log lines ----"
  tail -n 8 logs/epic_news.log 2>/dev/null || true
}

only="${1:-}"
for entry in "${FLOWS[@]}"; do
  label="${entry%%|*}"; request="${entry#*|}"
  [ -n "$only" ] && [ "$only" != "$label" ] && continue
  run_one "$label" "$request"
done
```

- [ ] **Step 2: Make it executable and smoke-test argument parsing (no LLM call)**

```bash
chmod +x scripts/verify_all_crews.sh
bash -n scripts/verify_all_crews.sh   # syntax check only
```
Expected: no output (valid syntax), exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/verify_all_crews.sh
git commit -m "chore(sweep): add verify_all_crews.sh crew verification driver"
```

---

## Tasks 3–16: Verify each flow (cheap → expensive)

Each task runs the **Per-Flow Verification Procedure** with the parameters below. A task's
deliverable is "this flow delivers a valid report to the test inbox" — plus a fix commit if
one was needed. Run with `scripts/verify_all_crews.sh <CATEGORY>`.

- [ ] **Task 3 — SAINT** · `Donne moi le saint du jour en français`
- [ ] **Task 4 — COOKING** · `Get me the recipe for Salade César`
- [ ] **Task 5 — SHOPPING** · `Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus éthique`
- [ ] **Task 6 — BOOK_SUMMARY** · `tell me all about the book: Clamser à Tataouine de Raphaël Quenard`
- [ ] **Task 7 — NEWSDAILY** · `get the daily news report`
- [ ] **Task 8 — FINDAILY** · `get the financial daily report` *(if it misroutes, try `Give me today's financial markets daily report`)*
- [ ] **Task 9 — COMPANY_NEWS** · `get me all news for company JT International SA`
- [ ] **Task 10 — RSS** · `get the rss weekly report`
- [ ] **Task 11 — MENU** · `Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French`
- [ ] **Task 12 — MEETING_PREP** · `Meeting preparation for JT International SA with the CTO to discuss PowerFlex deployment in Switzerland`
- [ ] **Task 13 — PESTEL** · `Fais moi un rapport PESTEL à propos de la société Pictet aujourd'hui en français`
- [ ] **Task 14 — SALES_PROSPECTING** · `let's find a sales prospect at Temenos to sell our product: Dell PowerFlex`
- [ ] **Task 15 — DEEPRESEARCH** · `conduct a deep research study on the progress of quantum computing and applications in cryptography`
- [ ] **Task 16 — OPEN_SOURCE_INTELLIGENCE** · `Complete OSINT analysis of Mistral.AI` *(heaviest — aggregates sub-crews; expect ~10–15 min)*

For each: execute steps 1–8 of the Per-Flow Verification Procedure. If a fix is made, it is
its own commit (`fix(<area>): <root cause>`) with a test where testable, before the task is
marked done.

---

## Task 17: Runbook + results table + PR

**Files:**
- Create: `docs/sweep-runbook.md`
- Modify: none (spec/plan already committed)

**Interfaces:**
- Produces: a runbook documenting how to run the sweep and a results table
  (`CATEGORY → PASS | fix commit`), plus a PR to `main`.

- [ ] **Step 1: Write the runbook**

```markdown
# Crew Verification Sweep — Runbook

Verify every routable ReceptionFlow path end-to-end on the current LLM stack.

## Run

    # all flows, cheap -> expensive:
    scripts/verify_all_crews.sh
    # one flow:
    scripts/verify_all_crews.sh COOKING

Env: `MAIL` sets the recipient (driver forces `fred.jacquet@gmail.com`);
`EPIC_NEWS_REQUEST` sets the routing request (honored by `kickoff()`).

## Pass criteria (per flow)

- kickoff exit 0
- `logs/epic_news_error.log` is 0 bytes
- `📨 Email delivered to fred.jacquet@gmail.com` in `logs/epic_news.log`
- a fresh non-empty report under `output/`

## Results (2026-07-12 sweep)

| Category | Result | Fix |
|---|---|---|
| HOLIDAY_PLANNER | PASS | prior session (508fd74/15c5a80/1cb5dbe) |
| SAINT | _fill_ | _fill_ |
| ... | ... | ... |
```

Fill the results table from Tasks 3–16 as they complete.

- [ ] **Step 2: Commit the runbook**

```bash
git add docs/sweep-runbook.md
git commit -m "docs(sweep): runbook + results table for crew verification"
```

- [ ] **Step 3: Push and open the PR**

```bash
git push -u origin chore/all-crews-e2e-sweep
gh pr create --base main --head chore/all-crews-e2e-sweep \
  --title "chore(sweep): verify all crews end-to-end + fixes" \
  --body "Runs all 15 routable flows end-to-end on Gemini+ReAct; per-flow fixes for latent output/render/email bugs. See docs/superpowers/specs/2026-07-12-all-crews-e2e-verification-sweep-design.md."
```

- [ ] **Step 4: Merge gate**

Wait for the **Run Tests** check to pass and review **CodeRabbit** comments before
`gh pr merge <n> --merge` (never `--admin`; never merge on red).

---

## Self-Review (completed by plan author)

- **Spec coverage:** §3.1 override → Task 1; §3/§5 driver → Task 2; §4 the 14 flows → Tasks 3–16; §6 failure taxonomy → Per-Flow Procedure steps 3/5/6/7; §7 deliverables (green flows, per-fix commits, driver, runbook) → Tasks 3–17; §8 success criteria → Task 17 results table + merge gate. No uncovered spec section.
- **Placeholder scan:** the only `_fill_` markers are the results-table rows that are *meant* to be filled at execution time (data, not undefined code); all code/test/script steps are complete.
- **Type consistency:** `EPIC_NEWS_REQUEST` / `MAIL` env names, `kickoff(user_input=...)`, and the `RESULT <CATEGORY>:` driver contract are used identically across Tasks 1, 2, and 3–16.
