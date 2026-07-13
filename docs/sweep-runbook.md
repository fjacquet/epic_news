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
