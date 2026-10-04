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

Notes: the menu request runs `MenuDesignerService`, which does not go through `kickoff_flow`, so only wall clock is available for it. An `OpenExchangeRates` HTTP 403 was logged during the holiday run (tool error, run completed).

PESTEL runs vary far more from run to run than the async change moves them: token use goes from 81k to 526k depending on how many tool rounds the researchers take. In the baseline run the economic task returned 389 characters (degraded). Run 2 was traced through CrewAI events: the six dimension tasks all started at t=13 s and finished between 63 s and 118 s (the LLM cap of 3 made them wait 163 s for a slot in total), then the report task took 50 s. Compare PESTEL on several runs, not one.
