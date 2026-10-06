# Utils Directory Context

Helpers used by `ReceptionFlow` (`src/epic_news/main.py`): crew kickoff, output parsing,
DOCX report generation, diagnostics, logging and cancellation. Everything listed here
exists in the code; check the module before relying on a signature.

## Directory Structure

```
utils/
├── flow_enforcement.py       # kickoff_flow / akickoff_flow: one shared retry path (opt-in retry + tracing + cancel checks)
├── concurrency.py            # bounded_map (ordered thread pool, limit from an env var, default 3)
├── recipe_export.py          # recipe_from_result, export_recipe (Paprika YAML/JSON under output/)
├── flow_helpers.py           # load_or_parse_model
├── directory_utils.py        # ensure_output_directories (startup), ensure_output_directory
├── diagnostics/              # parse_crewai_output, dump_crewai_state, analyze_crewai_output
├── docx_report/              # DOCX pipeline: Section → fragments → Pandoc (build_docx)
│   └── crews/                # assemble_<crew>_docx(model, inputs, output_path, llm=None)
├── holiday_report/           # assemble_holiday_docx (holiday planner is DOCX-only)
├── report_utils.py           # RSS weekly report helpers, prepare_email_params
├── email_sender.py           # send_report_email (Composio GMAIL_SEND_EMAIL, deterministic)
├── interrupt.py              # Ctrl+C handling: RunCancelledError, raise_if_cancelled, ...
├── logger.py                 # setup_logging (Loguru)
├── observability.py          # TraceEvent, Tracer, trace_task (sync and async flow steps)
├── tool_logging.py           # configure_tool_logging, apply_tool_silence
├── menu_generator.py         # MenuGenerator (season; parse_menu_structure(WeeklyMenuPlan) -> recipe specs)
├── menu_plan_validator.py    # MenuPlanValidator, menu_plan_from_output, MenuPlanError
├── rss_utils.py              # fetch_articles_from_opml (async)
├── data_normalization.py     # normalize_metric_type, normalize_trend_direction, ...
└── string_utils.py           # create_topic_slug
```

## Flow helpers (how a `generate_*` method is wired)

```python
from epic_news.crew_registry import CREW_REGISTRY, CrewKey

@listen("go_generate_poem")
@trace_task(tracer)
def generate_poem(self):
    inputs = self.state.to_crew_inputs()
    self._run_standard(CREW_REGISTRY[CrewKey.POEM], PoemCrew(), inputs)
```

`ReceptionFlow._run_standard(spec, crew, inputs)` deletes a stale JSON, runs `kickoff_flow`
(closing MCP in a `finally`), dumps state, loads the model with `load_or_parse_model` and calls
`emit_report` with the spec's assembler. After the DOCX is built it stores the model in `state.report` and the raw result in `state.raw_output` (OSINT sub-reports go in `state.osint`, keyed by crew name; `to_crew_inputs()` excludes all three). It returns `(output, model)`. Custom steps (RSS, menu,
recipe, shopping, OSINT, holiday) are written out with the helpers below.

- `kickoff_flow(crew_or_factory, context)`: calls `.crew()` when given a `@CrewBase` class
  instance, makes one attempt by default (`CREW_KICKOFF_ATTEMPTS` > 1 retries transient
  provider errors with backoff, rebuilding the crew each time), checks `raise_if_cancelled`
  before each attempt.
  `akickoff_flow` is the async twin (uses `crew.akickoff`). `context` must be a dict.
- `load_or_parse_model(json_path, model_cls, fallback_output, inputs=None, label="")`: loads
  and validates the JSON file the task wrote; on a missing/invalid file falls back to
  `parse_crewai_output(fallback_output, model_cls, inputs)`.
- `emit_report(state, assemble_docx)`: runs the zero-arg assembler closure, sets and returns
  `state.output_file`. DOCX is the only format (ADR-017); an assembler error propagates and
  stops the run.

## DOCX reports

- `docx_report.Section` describes one section: a deterministic `body`, or an
  `instruction` + `context` that `generate_fragment` narrates with the LLM.
- `assemble_fragments(sections, meta, output_path, llm, system)` narrates sections in
  parallel (`DOCX_FRAGMENT_CONCURRENCY`, default 3; output keeps section order), builds the
  DOCX. It first drops narrated sections whose context is empty or blank (info log; `ValueError`
  if no section is left), and raises `RuntimeError` before writing if any narration degraded
  to a placeholder.
- `build_docx(fragments, meta, output_path)` is the deterministic Pandoc step
  (`reference.docx` styles, TOC). It runs two passes (ADR-013): Markdown → JSON with the
  `safe_images.lua` (only images under `output/`) and `strip_rules.lua` (no horizontal rules)
  filters, then JSON → DOCX. System `pandoc` must be on `PATH`.
- Per-crew assemblers live in `docx_report/crews/` (`assemble_cooking_docx`,
  `assemble_news_daily_docx`, ...). Holiday planner: `holiday_report.assemble_holiday_docx`.
- `build_docx` raises `ValueError` for an `output_path` that does not resolve inside `output/`
  (ADR-015). `assemble_poem_docx` is deterministic (no LLM).
- Email: `prepare_email_params` attaches the DOCX with a short, HTML-escaped body; if the file is
  missing the flow sends nothing and leaves `email_sent = False`.

## Diagnostics and parsing

```python
from epic_news.utils.diagnostics import dump_crewai_state, parse_crewai_output

dump_crewai_state(output, "POEM")                      # writes a JSON dump under debug/
model = parse_crewai_output(output, PoemJSONOutput, inputs)
```

`parse_crewai_output` uses a pydantic output when present, else reads the first JSON value
of the raw output (text before it and after it — prose, fences, citations — is ignored),
repairs it with `json_repair` only when it is not valid JSON, and validates. Model-specific
fixes belong on the model as `mode="before"` validators. It raises `ValueError` on
empty/invalid output. Also exported:
`make_serializable`, `analyze_crewai_output`, `log_state_keys`.

## Other helpers

- **Directories**: `ensure_output_directories()` runs once at flow startup. Do not call
  `os.makedirs()` in crew/task logic.
- **Logging**: Loguru only (`from loguru import logger`); `setup_logging(log_level, log_to_file, log_dir, app_name)`.
- **Cancellation**: long loops call `raise_if_cancelled(what)`; `install_force_quit_handler()`
  arms the Ctrl+C watchdog (`EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS`, default 5).
- **Email**: `send_report_email(...)` calls Composio `GMAIL_SEND_EMAIL` directly and raises
  `EmailDeliveryError` unless delivery is confirmed; never delegate sending to an agent.
- **Observability**: `@trace_task(Tracer(...))` records `task_start` / `task_error` / `task_end` for
  each flow step (sync or `async def`) under `traces/` (used by `main.py` and `company_news`).

## Related Documentation

- Root `CLAUDE.md`, `src/epic_news/crews/CLAUDE.md`, `src/epic_news/tools/CLAUDE.md`
- `docs/adr/ADR-017-docx-only-reports.md`
