# Efficiency Wave — Measurements

Numbers from `scripts/bench_flow.py` (wall clock of the whole flow, plus per-crew lines
logged by `kickoff_flow`). Model: value of `MODEL` in `.env` at run time.

## Goals review

- **Goal 1 (2–3× faster on the slowest crews): met for holiday and menu, not for NewsDaily, not demonstrated for PESTEL.**
  - Holiday: the whole run went from 735.9 s to 286.6 s (2.6×). The gain is in DOCX assembly (wall clock minus the crew lines): about 405 s before, about 43 s after. The `HolidayPlannerCrew` change (321 s to 231 s, 304k to 169k tokens) is run-to-run noise: E4 does not touch the crew.
  - Menu: 808.3 s to 175.9 s (4.6×), 28 recipes in both runs (`Recipe 1/28` to `Recipe 28/28` in `logs/epic_news.log` for the baseline).
  - NewsDaily: 389.1 s to 252.3 s (1.5×), one run each. Below the target.
  - PESTEL: not demonstrated. In the 167.6 s run the researchers made one tool call in total and answered from model memory; the run that searched took 672.4 s against 414.1 s for the baseline. The async wiring works (the trace shows the six tasks starting together), but the end-to-end gain is unproven.
- **Goal 2 (fewer tokens):** routing went from 220,225 to 186,691 tokens and from 90 to 60 LLM calls on 30 requests. The menu and holiday token targets were not measured: CrewAI does not count `output_pydantic` calls, and the bench's LiteLLM totals were added after those runs.
- **Goal 3 (same quality):** routing stayed at 30/30. Quality defects seen during the wave, not caused by it, that need follow-up:
  - PESTEL researchers sometimes skip live search and cite 2024 sources from memory.
  - The menu planner returns generic dish names ("Entrée du jour").
  - In the E6 comparison, the OSINT research-mode cross-reference report named the wrong company (Target Global Holdings / Pontus Shipping) for a Logitech request. `detailed_findings` is empty in both modes.

  Fixed on 2026-10-05 (branch `fix/quality-bugs`): PESTEL keeps the request's subject and gets one last-12-months search per dimension before the crew runs (2025–2026 facts in all six dimensions on the check run); the menu keeps the planner's dishes and plans the requested number of days (2-day request: 2 days, 8 recipes, real dish names); the OSINT cross-reference tasks use their YAML prompts with the target and receive the six sub-reports (target Logitech, six `detailed_findings` entries).
- **Goal 4 (measure every change):** every change has a measurement, but each is a single run, with the caveats above.

| Date | Change | Request | Wall clock (s) | Crew | Crew seconds | Total tokens | Requests |
|---|---|---|---|---|---|---|---|
| 2026-10-04 | baseline | pestel | 414.1 | InformationExtractionCrew | 7.11 | 875 | 1 |
| 2026-10-04 | baseline | pestel | 414.1 | ClassifyCrew | 2.96 | 0 | 0 |
| 2026-10-04 | baseline | pestel | 414.1 | PestelCrew | 400.99 | 274458 | 18 |
| 2026-10-04 | baseline | news_daily | 389.1 | InformationExtractionCrew | 5.32 | 688 | 1 |
| 2026-10-04 | baseline | news_daily | 389.1 | ClassifyCrew | 1.78 | 0 | 0 |
| 2026-10-04 | baseline | news_daily | 389.1 | NewsDailyCrew | 381.96 | 202899 | 16 |
| 2026-10-04 | baseline | menu | 808.3 | InformationExtractionCrew | 7.15 | 901 | 1 |
| 2026-10-04 | baseline | menu | 808.3 | ClassifyCrew | 1.79 | 0 | 0 |
| 2026-10-04 | baseline | menu | 808.3 | (MenuDesignerService; no kickoff_flow line) | n/a | n/a | n/a |
| 2026-10-04 | baseline | holiday | 735.9 | InformationExtractionCrew | 7.7 | 942 | 1 |
| 2026-10-04 | baseline | holiday | 735.9 | ClassifyCrew | 2.03 | 0 | 0 |
| 2026-10-04 | baseline | holiday | 735.9 | HolidayPlannerCrew | 320.98 | 303820 | 10 |
| 2026-10-04 | E2 pestel async | pestel | 672.4 | InformationExtractionCrew | 6.11 | 882 | 1 |
| 2026-10-04 | E2 pestel async | pestel | 672.4 | ClassifyCrew | 1.58 | 0 | 0 |
| 2026-10-04 | E2 pestel async | pestel | 672.4 | PestelCrew | 660.96 | 525668 | 13 |
| 2026-10-04 | E2 pestel async (run 2) | pestel | 167.6 | InformationExtractionCrew | 7.36 | 895 | 1 |
| 2026-10-04 | E2 pestel async (run 2) | pestel | 167.6 | ClassifyCrew | 2.07 | 0 | 0 |
| 2026-10-04 | E2 pestel async (run 2) | pestel | 167.6 | PestelCrew | 154.5 | 81338 | 10 |
| 2026-10-04 | E2 news_daily async | news_daily | 252.3 | InformationExtractionCrew | 6.44 | 882 | 1 |
| 2026-10-04 | E2 news_daily async | news_daily | 252.3 | ClassifyCrew | 1.54 | 0 | 0 |
| 2026-10-04 | E2 news_daily async | news_daily | 252.3 | NewsDailyCrew | 241.41 | 158029 | 16 |
| 2026-10-04 | E4 docx parallel + day slices | holiday | 286.6 | InformationExtractionCrew | 10.57 | 1359 | 1 |
| 2026-10-04 | E4 docx parallel + day slices | holiday | 286.6 | ClassifyCrew | 1.83 | 0 | 0 |
| 2026-10-04 | E4 docx parallel + day slices | holiday | 286.6 | HolidayPlannerCrew | 231.31 | 168928 | 10 |
| 2026-10-04 | E3 single-pass recipes + parallel | menu | 175.9 | InformationExtractionCrew | 6.86 | 903 | 1 |
| 2026-10-04 | E3 single-pass recipes + parallel | menu | 175.9 | ClassifyCrew | 2.03 | 0 | 0 |
| 2026-10-04 | E3 single-pass recipes + parallel | menu | 175.9 | CookingCrew ×28 (sum) | 310.86 | 0 (not reported) | 0 (not reported) |

Notes: the menu request runs `MenuDesignerService`, which does not go through `kickoff_flow`, so only wall clock is available for it. An `OpenExchangeRates` HTTP 403 was logged during the holiday run (tool error, run completed). CrewAI's per-crew token counts miss structured-output (`output_pydantic`) calls (ClassifyCrew and CookingCrew show 0); from this commit the bench also prints LiteLLM totals for the whole run, which count every call.

PESTEL runs vary far more from run to run than the async change moves them: token use goes from 81k to 526k depending on how many tool rounds the researchers take. In the baseline run the economic task returned 389 characters (degraded). Run 2 was traced through CrewAI events: the six dimension tasks all started at t=13 s and finished between 63 s and 118 s (the LLM cap of 3 made them wait 163 s for a slot in total), then the report task took 50 s. Compare PESTEL on several runs, not one.

E3 menu run: 28/28 recipes generated, wall 175.9 s vs 808.3 s baseline (sequential). Recipes run 3 at a time, so the summed per-crew time (310.9 s) exceeds wall time. CookingCrew usage lines report tokens=0 and requests=0 (usage is not captured for these calls), so no token comparison is possible. The generated menu plan used generic dish names, so the 28 specs mapped to only 2 file names (`entree-du-jour`, `plat-principal-du-jour`) in this run; the file name now includes the menu code (e.g. `lun-l-s02-entree-du-jour`), so every recipe keeps its own files.

### Routing

| Date | Change | Accuracy | BAD lines | Wall (s) | LiteLLM calls | Prompt | Completion | Total |
|---|---|---|---|---|---|---|---|---|
| 2026-10-04 | E5 baseline routing | 30/30 | none | 321.5 | 90 | 174872 | 45353 | 220225 |
| 2026-10-04 | E5 single-call routing | 30/30 | none | 229.1 | 60 | 154870 | 31821 | 186691 |

Two-step routing (InformationExtractionCrew then ClassifyCrew) over the 30 requests in `scripts/routing_eval_requests.json`, one at a time: about 10.7 s and 7.3k tokens per request, 3 LLM calls per request. Only the extraction and classification crews ran; no email was sent. An earlier run printed `litellm calls=0` because CrewAI resets `litellm.callbacks` each time it builds an LLM; the counter is now registered in `success_callback` and `_async_success_callback`.

E5 single-call routing: the extraction crew now also picks the crew (`ExtractedInfo.selected_crew`) and ClassifyCrew runs only when that field is empty or invalid. Accuracy is unchanged at 30/30. The ClassifyCrew fallback was used 0 times (0 `🔁` lines in `logs/epic_news.log` during the run), so each request made 2 LLM calls (enrichment and extraction) instead of 3. Wall clock fell 29% (321.5 s to 229.1 s) and total tokens 15% (220,225 to 186,691). The extraction prompt grew by the routing guide, which is why prompt tokens fall less than the call count.

### OSINT cross-reference (E6)

| Date | Change | Wall (s) | Cross-reference crew | Crew seconds | Crew tokens (CrewAI) | LiteLLM calls | Prompt | Completion | Total |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-04 | E6 research | 1294.0 | CrossReferenceReportCrew | 262.86 | 97462 (5 requests) | 89 | 1808399 | 604439 | 2412838 |
| 2026-10-04 | E6 synthesis | 692.8 | CrossReferenceSynthesisCrew | 17.13 | 0 (not reported; output_pydantic call) | 79 | 1361182 | 421837 | 1783019 |

Each run executes the six OSINT crews again (target: Logitech), and those vary a lot from run to run (CompanyProfilerCrew: 1,404k tokens in the research run, 440k in the synthesis run), so wall clock and LiteLLM totals mix that noise with the cross-reference step. The cross-reference crew seconds are the clean comparison: 262.9 s (5 requests, 97k tokens) for research versus 17.1 s for synthesis (CrewAI reports 0 tokens because the single call is structured output). Output files: `output/osint/compare/{research,synthesis}.{html,json}`.

Decision (2026-10-04): the user kept the research mode; the synthesis mode was removed.

### DOCX-only reports (S5)

| Date | Change | Request | Wall (s) | Crew | Crew seconds | Crew tokens (CrewAI) | LiteLLM calls | LiteLLM total tokens |
|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | S5 DOCX only | news_daily | 310.6 | NewsDailyCrew | 295.74 | 299864 (19 requests) | 23 | 339755 |
| 2026-10-05 | S5 DOCX only | saint | 276.3 | SaintDailyCrew | 246.88 | 19800 (3 requests) | 11 | 46408 |

Both runs used `EPIC_ENABLE_EMAIL=false`. The report step adds little time: wall clock minus the crew and extraction seconds is about 8 s for news_daily and 22 s for saint. LiteLLM calls not made by the crews or the extraction (3 for news_daily, 7 for saint) are the narrated DOCX sections. The news_daily wall clock (310.6 s, against 252.3 s for E2 with HTML) moves with NewsDailyCrew itself (295.7 s against 241.4 s; 19 against 16 requests); the report step is not the cause. No HTML baseline exists for saint. Both DOCX files hold real content: news_daily has 9 sections and 70 source links, and saint gives the biography, meaning and miracles of the day's saint (Faustina Kowalska, 5 October). Neither contains placeholder text. Narrated sections repeat their section title as a sub-heading (`# Biographie` followed by `## Biographie`); this is a fragment-prompt issue and predates S5.

### Deep research on the standard path (S3)

| Date | Change | Request | Wall (s) | Crew | Crew seconds | Crew tokens (CrewAI) | LiteLLM calls | LiteLLM total tokens |
|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | S3 single schema, no extractor | deep_research | 431.7 | DeepResearchCrew | 371.82 | 143188 (5 requests) | 15 | 228618 |

Run with `EPIC_ENABLE_EMAIL=false`; request: "Fais une recherche approfondie sur l'état de l'art des systèmes de fichiers parallèles en 2026". `report.json` validated against the single `DeepResearchReport` on the first load (no raw-output fallback). The DOCX holds every section title (5), key finding (5) and unique source URL (12 unique of 16 citations) from `report.json`, about 10,200 words, and no placeholder text. LiteLLM calls not made by the crew requests or the extraction: 9, of which 7 are the narrated DOCX sections (executive summary, 5 research sections, methodology); the other 2 were not attributed. Narrated sections still repeat their title as a sub-heading (known, predates S3).

### Crew registry and standard-step helper (S4)

| Date | Change | Request | Wall (s) | Crew | Crew seconds | Crew tokens (CrewAI) | LiteLLM calls | LiteLLM total tokens |
|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | S4 `_run_standard` | saint | 167.2 | SaintDailyCrew | 133.39 | 12013 (1 request) | 9 | 39517 |

Run with `EPIC_ENABLE_EMAIL=false`. The saint step now runs through `_run_standard`; the run wrote `output/saint_daily/report.json` and `report.docx` (about 2,300 words, sections Biographie, Signification, Miracles, Lien avec la Suisse, Prière & Réflexion, Sources) and a debug dump labelled `saint` (registry key). Against the S5 saint run (276.3 s, 11 calls) the difference is the crew itself (1 request against 3); the helper adds no LLM call.

### Flow state (S6)

| Date | Change | Request | Wall (s) | Crew | Crew seconds | Crew tokens (CrewAI) | LiteLLM calls | LiteLLM total tokens |
|---|---|---|---|---|---|---|---|---|
| 2026-10-05 | S6 `report`/`raw_output`/`osint` state, `CrewKey` | saint | 196.4 | SaintDailyCrew | 164.15 | 32532 (2 requests) | 10 | 60059 |

Run with `EPIC_ENABLE_EMAIL=false`. Routing through `CrewKey` and the slimmer state worked end to end: `output/saint_daily/report.json` and `report.docx` (about 2,350 words, the same six sections as the S4 run). Wall clock and calls move with the crew's own request count (2 here, 1 in the S4 run).
