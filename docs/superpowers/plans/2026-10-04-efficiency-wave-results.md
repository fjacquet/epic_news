# Efficiency Wave — Measurements

Numbers from `scripts/bench_flow.py` (wall clock of the whole flow, plus per-crew lines
logged by `kickoff_flow`). Model: value of `MODEL` in `.env` at run time.

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
| 2026-10-04 | E5 baseline routing | 25/25 | none | 265.2 | 75 | 145698 | 35543 | 181241 |

Two-step routing (InformationExtractionCrew then ClassifyCrew) over the 25 requests in `scripts/routing_eval_requests.json`, one at a time: about 10.6 s and 7.2k tokens per request, 3 LLM calls per request. Only the extraction and classification crews ran (25 runs of each in the log); no email was sent. A first run printed `litellm calls=0` because CrewAI resets `litellm.callbacks` each time it builds an LLM; the counter is now registered in `litellm.success_callback`. That first run was also 25/25 (wall 254.6 s). `scripts/bench_flow.py` registers its counter the same way.
