# All-Crews End-to-End Verification Sweep — Runbook

Runs every routable `ReceptionFlow` crew end-to-end on the current stack
(native Gemini `gemini/gemini-3.5-flash` + forced ReAct tool-calling) and confirms
each produces a valid report **and** delivers an email to a test inbox.

Use this after any change to `LLMConfig`, the provider/model, the email path, or a
renderer — the class of bug it catches only surfaces at runtime (pandoc crashes,
markdown leaking into HTML, non-`str` task output, an unset `output_file`).

## How to run

```bash
# One flow by category label:
bash scripts/verify_all_crews.sh MENU

# All flows, cheap -> expensive:
bash scripts/verify_all_crews.sh
```

The driver (`scripts/verify_all_crews.sh`) sets two environment variables per flow:

| Env var | Purpose |
|---|---|
| `MAIL=fred.jacquet@gmail.com` | Forces every sweep email to one test inbox (`content_state.py` `DEFAULT_EMAIL`). |
| `EPIC_NEWS_REQUEST="<request>"` | The per-flow routing request. `kickoff()` honors it: `user_input = user_input or os.getenv("EPIC_NEWS_REQUEST") or None`, falling back to the hardcoded query when unset — so the normal sentinel workflow is unchanged. |

An unknown label now fails loudly (exit 2, prints valid labels) rather than silently
running nothing and exiting 0. **The OSINT label is `OPEN_SOURCE_INTELLIGENCE`**, not `OSINT`.

## Reading the result

Each flow prints `RESULT <LABEL>: exit=X error_log_bytes=Y email_delivered=Z`.

Trust these three signals — **not** the `email_delivered` grep, which greps the
cumulative `logs/epic_news.log` and false-positives on a failed run:

1. `exit=0`
2. `logs/epic_news_error.log` is 0 bytes (truncated before each run)
3. A fresh `📨 Email delivered` line whose `Email payload:` `attachment=` points at the
   flow's real report (not the classify path), plus a non-zero report file on disk.

## Runtime output format: HTML default, DOCX opt-in

Every routable crew (except POEM) now emits **HTML by default** and a **DOCX on
request** through one dispatch helper, `emit_report(state, "KEY", render_html,
assemble_docx=…)` (`src/epic_news/utils/docx_report/dispatch.py`). Format is
resolved per run by `resolve_output_format(state)`:

1. `OUTPUT_FORMAT` env var (`html` | `docx`) — highest precedence
2. `state.output_format` — set by `parse_output_format(request)` from the request text
3. default `html`

Select DOCX for a sweep with `OUTPUT_FORMAT=docx bash scripts/verify_all_crews.sh …`.
`emit_report` runs `assemble_docx()` when the resolved format is `docx` (else
`render_html()`), and always records the produced path in `state.output_file`, so
the emailed attachment is whichever format was selected.

### Two-format verification — 2026-07-13

DOCX runtime wiring landed for all 14 non-POEM crews (commit `0b18881`, plus
`generate_deep_research`/`generate_findaily` wired earlier). Verification was
scaled to the risk — the wiring is mechanical and identical across crews (one
`emit_report` wrap per render site); the only per-crew variable is the
`assemble_*_docx` function, and each of those is unit-tested against its real
Pydantic model with real `pypandoc` producing a valid `.docx`.

| Evidence | Coverage |
|---|---|
| **Live docx kickoff — tabular path** | FINDAILY: real flow, `OUTPUT_FORMAT=docx` → valid `.docx` with `<w:tbl>` tables, empty error log. |
| **Live docx kickoff — prose path** | SAINT: real flow, `OUTPUT_FORMAT=docx` → `report.docx` 19 KB, all French section headings + Swiss content, heading styles, empty error log. |
| **Per-assembler unit tests** | All 14 assemblers: real `pypandoc`, verbatim-fidelity + None-guard + heading-order asserts (part of the 774-test suite). |
| **Static type check** | `mypy` types every assembler against the crew's real model — this is what caught the Task-7 model mismatch before runtime. |
| **Static wire-site review** | The 3 structurally-different wirings confirmed by reading committed code: MENU (dual render site, both set `final_report = output_file`), RSS (async closure + `load_rss_weekly_report`), OSINT (post-parallel, `assemble_osint_docx` reads `output/osint/*.json`). |
| **HTML path** | All 15 flows green in the full HTML sweep below (unchanged by the wiring). |

**Deferred (not run):** the full 28-kickoff `OUTPUT_FORMAT=docx` matrix across all
14 crews. Rationale: the two live shapes above (tabular + prose) exercise both
assembler families end-to-end; the remaining 12 differ only in their unit-tested
`assemble_*_docx` body and mypy-checked wire site. Running every heavy crew
(OSINT spawns 6 parallel sub-crews; DEEPRESEARCH/MENU are long) a second time in
docx was judged disproportionate to the residual risk. To run it anyway:
`OUTPUT_FORMAT=docx bash scripts/verify_all_crews.sh` (and per-flow with a label).

**Known cosmetic note (non-blocking):** a few post-render log lines are hardcoded
to "…HTML written" (e.g. `generate_saint_daily`, `generate_shopping_advice`) and
read inaccurately when DOCX was selected — the file on disk is correct; only the
log string is stale. Flagged for the final review to batch-fix.

## Results — 2026-07-13 (all 15 flows green)

Stack: `MODEL=gemini/gemini-3.5-flash` (native, off OpenRouter) + `supports_function_calling=False` (ReAct).

| # | Category | Result | Report (emailed attachment) |
|---|---|---|---|
| 1 | SAINT | PASS | saint report + email |
| 2 | COOKING | PASS | recipe report + email |
| 3 | SHOPPING | PASS | shopping advice + email |
| 4 | BOOK_SUMMARY | PASS | book summary + email |
| 5 | NEWSDAILY | PASS | `final_report.html` 112KB + email |
| 6 | FINDAILY | PASS | financial daily + email |
| 7 | COMPANY_NEWS | PASS | company news + email |
| 8 | RSS | PASS (after fix) | rss weekly + email |
| 9 | MENU | PASS (after fix) | `menu_designer/menu_weekly_menu.html` + email |
| 10 | MEETING_PREP | PASS | `meeting/meeting_preparation.html` 68.5KB + email |
| 11 | PESTEL | PASS | `pestel/report.html` 105KB + email |
| 12 | SALES_PROSPECTING | PASS | `sales_prospecting/report.html` 82KB + email |
| 13 | DEEPRESEARCH | PASS | `deep_research/report.html` 74KB + email |
| 14 | OPEN_SOURCE_INTELLIGENCE | PASS | `osint/global_report.html` 57KB + email |
| ✅ | HOLIDAY_PLANNER | PASS (verified earlier this session) | DOCX travel guide + email |

POEM is excluded per decision.

### Fixes committed during the sweep

| Commit | Fix |
|---|---|
| `fede645` | `kickoff()` returns `None` so a successful run exits 0 (was returning the flow object → `sys.exit()` printed it and exited 1). Global — affected every flow. |
| `f57c5e9` | `generate_rss_weekly` awaits `akickoff_flow` (was calling sync `kickoff_flow` from an async method). |
| `b70bde0` | `generate_menu_designer` sets `state.output_file` so the menu report is the emailed attachment (was stuck on the classify path). |

### Known soft notes (non-blocking, not fixed)

These surfaced in logs but did not fail the taxonomy (exit 0, empty error log, valid
report, email delivered) — they are external or self-healing:

- **PESTEL** — transient ReAct "Action Input is not a valid key, value dictionary"
  parser retries; the agent recovered and the run completed clean.
- **SALES_PROSPECTING** — agents probed non-existent scratchpad `.txt` files
  ("File not found at path"); they recovered from context and no error leaked into the report.
- **DEEPRESEARCH** — the third-party Wikipedia MCP `search` tool returned an external
  `403 Forbidden` (Wikipedia API rate-limit); the agent fell back to other tools.

## Failure taxonomy

A flow fails if any of: uncaught exception / non-zero exit; `epic_news_error.log`
non-empty; report file missing, 0 bytes, or invalid; or the email was not built/sent.
A Gemini rate-limit / 5xx / timeout is retried once before being treated as a bug; a
misrouted classify is fixed by adjusting the request phrasing, not counted as a crew bug.
