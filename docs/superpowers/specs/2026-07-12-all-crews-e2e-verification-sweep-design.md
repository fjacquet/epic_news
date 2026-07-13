# All-Crews End-to-End Verification Sweep — Design

- **Status:** Draft for review
- **Date:** 2026-07-12
- **Branch target:** new branch off `main` (post PR #158 merge)

## 1. Problem & Goal

The holiday flow just went from broken-in-four-places to working end-to-end on
native Gemini (`gemini/gemini-3.5-flash`) + forced ReAct tool-calling. The LLM-layer
fixes live in `LLMConfig` and apply to **every** crew globally. But no other crew has
been run end-to-end since the provider / tool-calling change, so each may still harbor
latent output / render / email bugs — the kind that only surface at runtime (e.g. the
pandoc `---`→YAML crash, markdown leaking into HTML, non-`str` task output).

**Goal:** run all 15 routable flows end-to-end on the current stack (POEM excluded per
decision), observe the real failures, and fix them — the same treatment holiday received.

## 2. Scope

**In scope:** 15 classifier categories, each backed by one `ReceptionFlow.generate_*`
method (see §4). POEM is excluded per decision. "End-to-end" = classify → extract →
crew → render (HTML/DOCX) → email delivered to the test inbox.

**Exercised transitively (not run standalone):** the sub-crews
`company_profiler`, `geospatial_analysis`, `legal_analysis`, `hr_intelligence`,
`tech_stack`, `web_presence`, `library`, `cross_reference_report` — invoked inside
OSINT / deep-research / book-summary flows.

**Out of scope:** the `UNKNOWN` route; refactors unrelated to an observed failure;
repo-wide docstring coverage; changing crew logic beyond what a failure requires;
performance tuning.

## 3. Approach

Full `crewai flow kickoff` per crew — the only supported execution path — driven by two
environment variables so the sweep is scriptable and side-effect-safe:

| Env var | Purpose | Mechanism |
|---|---|---|
| `EPIC_NEWS_REQUEST` | The per-crew routing request | **New** override in `kickoff()` (see §3.1) |
| `MAIL=fred.jacquet@gmail.com` | Force all sweep emails to one test inbox | **Existing** — `DEFAULT_EMAIL = os.getenv("MAIL") or FALLBACK` (`content_state.py:84`) |

### 3.1 Enabling change (`main.py`, the sentinel file)

Add one line at the top of `kickoff()`:

```python
def kickoff(user_input: str | None = None):
    user_input = user_input or os.getenv("EPIC_NEWS_REQUEST") or None
    ...
    request = user_input if user_input else query
```

Falls back to the hardcoded `query` when unset, so the normal sentinel workflow
(uncommenting a phrase) is unchanged.

## 4. The flows + representative requests

**15 flows total** (POEM excluded per decision); holiday is already green this session,
so **14 remain to verify**, ordered cheap → expensive so systemic bugs surface fast and
cheap. Requests are drawn from the example block already in `main.py`.

| # | Category | `generate_*` | Representative `EPIC_NEWS_REQUEST` |
|---|---|---|---|
| 1 | SAINT | `generate_saint_daily` | Donne moi le saint du jour en français |
| 2 | COOKING | `generate_recipe` | Get me the recipe for Salade César |
| 3 | SHOPPING | `generate_shopping_advice` | Donne moi un conseil d'achat pour remplacer mon sodastream par une marque plus éthique |
| 4 | BOOK_SUMMARY | `generate_book_summary` | tell me all about the book: Clamser à Tataouine de Raphaël Quenard |
| 5 | NEWSDAILY | `generate_news_daily` | get the daily news report |
| 6 | FINDAILY | `generate_findaily` | get the financial daily report *(adjust phrasing if it misroutes)* |
| 7 | COMPANY_NEWS | `generate_news_company` | get me all news for company JT International SA |
| 8 | RSS | `generate_rss_weekly` | get the rss weekly report |
| 9 | MENU | `generate_menu_designer` | Generate a complete weekly menu planner with 30 recipes and shopping list for a family of 3 in French |
| 10 | MEETING_PREP | `generate_meeting_prep` | Meeting preparation for JT International SA with the CTO to discuss PowerFlex deployment in Switzerland |
| 11 | PESTEL | `generate_pestel` | Fais moi un rapport PESTEL à propos de la société Pictet aujourd'hui en français |
| 12 | SALES_PROSPECTING | `generate_sales_prospecting_report` | let's find a sales prospect at Temenos to sell our product: Dell PowerFlex |
| 13 | DEEPRESEARCH | `generate_deep_research` | conduct a deep research study on the progress of quantum computing and applications in cryptography |
| 14 | OPEN_SOURCE_INTELLIGENCE | `generate_osint` | Complete OSINT analysis of Mistral.AI |
| ✅ | HOLIDAY_PLANNER | `generate_holiday_plan` | already verified end-to-end this session |

## 5. Sweep workflow

1. **Driver:** `scripts/verify_all_crews.sh` — for each flow, in cheap→expensive order:
   - `export MAIL=fred.jacquet@gmail.com EPIC_NEWS_REQUEST="<request>"`
   - `crewai flow kickoff`
   - Capture: process exit code, `logs/epic_news_error.log` size, tail of
     `logs/epic_news.log`, and presence + non-zero size of the expected output file.
   - Record a row: `category → pass/fail → note`.
2. **Fix-as-you-go:** on the first failure for a flow, stop, run the
   `superpowers:systematic-debugging` loop, fix the root cause, re-run **that flow**, then
   continue. (The global LLM shims mean remaining failures are crew-specific and
   independent — no benefit to batch-cataloguing.)
3. **Commit discipline:** one logical commit per fix, repo conventions (uv, ruff, mypy,
   Loguru), with a unit test whenever the fix has a testable surface (renderer/extractor/
   builder). Do **not** stage `main.py` beyond the §3.1 override, per the sentinel rule.

## 6. Failure taxonomy

A flow **fails** the sweep if any of:
- Uncaught exception / non-zero kickoff exit.
- `logs/epic_news_error.log` non-empty after the run.
- Expected report file missing, 0 bytes, or invalid (HTML not parseable / DOCX unopenable).
- Email payload not built or SMTP send failed.

**Known bug classes to watch** (from the holiday journey and repo memory):
- Markdown leaking into HTML (renderers must use `render_markdown_block/inline`).
- Pandoc / DOCX input needing sanitization.
- Non-`str` values reaching a `str` field (`TaskOutput.raw`, Pydantic models).
- LLM anonymizing PII in deterministic tool args.
- Provider message-format / tool-calling assumptions (already shimmed globally).

**Transient vs real:** a Gemini rate-limit / 5xx / timeout is retried once before being
treated as a bug; a misrouted classify is fixed by adjusting the request phrasing, not
counted as a crew bug.

## 7. Deliverables

1. All 14 remaining flows green: valid report generated + email delivered to
   `fred.jacquet@gmail.com`; `epic_news_error.log` empty.
2. Fixes committed (one per root cause) with tests where applicable.
3. `scripts/verify_all_crews.sh` — repeatable driver.
4. A results table (category → pass/fail → fix commit) in a short runbook under
   `docs/` describing how to run the sweep and the two env vars.

## 8. Success criteria

Every one of the 15 flows completes end-to-end with a valid report and a delivered email
to the test inbox; the error log is empty; each fix has a test where it has a testable
surface; and the whole sweep is reproducible via the driver script.

## 9. Risks & cost

- **Real LLM cost/time:** heavy flows (`deep_research`, `osint`, `holiday` ~12 min each);
  the full sweep is plausibly 1–3 h of wall-clock + real API spend. Cheap-first ordering
  limits waste by catching systemic issues before the expensive runs.
- **16 real emails** to the test inbox.
- **Rate limits / transients** on Gemini — handled per §6.
- **Misrouting** — some phrases may need tuning to hit the intended category.

## 10. Assumptions

- `MAIL` env cleanly overrides the recipient for every flow (verified on run #1).
- The representative phrases route to their intended category (adjust as needed).
- No crew depends on native function-calling (guaranteed by the global ReAct shim).
