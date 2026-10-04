# Utils Directory Context

Helpers used by `ReceptionFlow` (`src/epic_news/main.py`): crew kickoff, output parsing,
HTML/DOCX report generation, diagnostics, logging and cancellation. Everything listed here
exists in the code; check the module before relying on a signature.

## Directory Structure

```
utils/
├── flow_enforcement.py       # kickoff_flow / akickoff_flow (retry + tracing + cancel checks)
├── flow_helpers.py           # load_or_parse_model, render_and_write_html
├── directory_utils.py        # ensure_output_directories (startup), ensure_output_directory
├── diagnostics/              # parse_crewai_output, dump_crewai_state, analyze_crewai_output
├── html/
│   ├── template_manager.py   # TemplateManager.render_report(...)
│   ├── validator.py          # validate_html(html, raise_on_error=True)
│   └── template_renderers/   # BaseRenderer, RendererFactory, *_renderer.py, pestel_markdown.py
├── extractors/               # ContentExtractorFactory + DeepResearchExtractor, GenericExtractor
├── docx_report/              # DOCX pipeline: Section → fragments → Pandoc (build_docx)
│   └── crews/                # assemble_<crew>_docx(model, inputs, output_path, llm=None)
├── holiday_report/           # assemble_holiday_docx (holiday planner is DOCX-only)
├── report_utils.py           # RSS weekly report helpers, resolve_report_html, prepare_email_params
├── email_sender.py           # send_report_email (Composio GMAIL_SEND_EMAIL, deterministic)
├── interrupt.py              # Ctrl+C handling: RunCancelledError, raise_if_cancelled, ...
├── logger.py                 # setup_logging (Loguru)
├── tracing.py                # trace_span context manager (optional Langfuse)
├── observability.py          # Tracer, Dashboard, HallucinationGuard, get_observability_tools
├── tool_logging.py           # configure_tool_logging, apply_tool_silence
├── menu_generator.py         # MenuGenerator (season, menu structure parsing)
├── menu_plan_validator.py    # MenuPlanValidator (fix/validate WeeklyMenuPlan)
├── rss_utils.py              # fetch_articles_from_opml (async)
├── data_normalization.py     # normalize_metric_type, normalize_trend_direction, ...
└── string_utils.py           # create_topic_slug
```

## Flow helpers (how a `generate_*` method is wired)

```python
from epic_news.utils.flow_enforcement import kickoff_flow
from epic_news.utils.flow_helpers import load_or_parse_model, render_and_write_html
from epic_news.utils.docx_report.dispatch import emit_report

output = kickoff_flow(PoemCrew(), inputs)                      # Crew factory or Crew instance
model = load_or_parse_model(self.state.output_file, PoemJSONOutput, output, inputs, "poem")
render_and_write_html("POEM", model, "output/poem/poem.html")  # returns the Path
```

- `kickoff_flow(crew_or_factory, context)`: calls `.crew()` when given a `@CrewBase` class
  instance, rebuilds the crew on every attempt, retries transient provider errors with
  backoff, checks `raise_if_cancelled` before each attempt, wraps the run in `trace_span`.
  `akickoff_flow` is the async twin (uses `crew.akickoff`). `context` must be a dict.
- `load_or_parse_model(json_path, model_cls, fallback_output, inputs=None, label="")`: loads
  and validates the JSON file the task wrote; on a missing/invalid file falls back to
  `parse_crewai_output(fallback_output, model_cls, inputs)`.
- `render_and_write_html(selected_crew, model, html_path)`: `TemplateManager().render_report`
  + write; creates the parent directory itself.
- `emit_report(state, selected_crew, render_html, assemble_docx=None)`: picks DOCX or HTML
  (`OUTPUT_FORMAT` env > `state.output_format` > `"html"`), runs the matching zero-arg
  closure, sets and returns `state.output_file`.

## HTML rendering

Pipeline: Pydantic model → `model_dump()` → `TemplateManager.render_report()` →
`RendererFactory.create_renderer(selected_crew)` → `BaseRenderer.render(data)` → body injected
into `templates/universal_report_template.html`.

```python
from epic_news.utils.html.template_manager import TemplateManager

html = TemplateManager().render_report(selected_crew="POEM", content_data=model.model_dump())
```

- `render_report` is an **instance** method returning a string; it does not write files
  (use `render_and_write_html`). It fills `{{ theme_css_vars }}` (from
  `config/ui_theme.py`), `{{ static_css }}` (`templates/css/report.css`), title, body and date.
- `RendererFactory` (classmethods): `create_renderer(crew_type)`,
  `has_specialized_renderer(crew_type)`, `get_supported_crew_types()`. Keys are upper-case
  crew identifiers (`POEM`, `COOKING`, `FINDAILY`, `NEWSDAILY`, `DEEPRESEARCH`, `PESTEL`, ...);
  unknown types fall back to `GenericRenderer`. Register a new renderer in `_RENDERER_MAP`.
- `pestel_markdown.py` renders a `PestelReport` as Markdown (no BaseRenderer).

### BaseRenderer rules

`BaseRenderer` (ABC) declares both `__init__` and `render(data) -> str` abstract, so
subclasses must define `__init__` even if empty. Helpers: `create_soup(tag, **attrs)`,
`add_section`, `add_report_header`, `add_section_title`, `create_section`,
`render_dict_as_cards`, `render_list_as_cards`, `render_text_section`,
`render_markdown_block`, `render_markdown_inline`, `append_prose`, `add_raw_json_section`,
`escape_html`.

```python
class MyCrewRenderer(BaseRenderer):
    def __init__(self):
        pass

    def render(self, data: dict[str, Any]) -> str:
        soup = self.create_soup("div")
        root = soup.find("div")
        if not data.get("items"):
            empty = soup.new_tag("p")
            empty.attrs["class"] = ["empty-state"]
            empty.string = "Aucun élément"
            root.append(empty)
            return str(soup)
        section = soup.new_tag("section")
        section.attrs["class"] = ["card"]          # NOT new_tag(..., class_="...")
        section["style"] = "color: var(--text-color, #343a40);"
        root.append(section)
        return str(soup)
```

- Use `tag.attrs["class"] = [...]`, CSS variables with fallbacks, and handle empty states.

## DOCX reports

- `docx_report.Section` describes one section: a deterministic `body`, or an
  `instruction` + `context` that `generate_fragment` narrates with the LLM.
- `assemble_fragments(sections, meta, output_path, llm, system)` builds the DOCX and refuses
  to write when more than half the sections degraded to placeholders.
- `build_docx(fragments, meta, output_path)` is the deterministic Pandoc step
  (`reference.docx` styles, TOC).
- Per-crew assemblers live in `docx_report/crews/` (`assemble_cooking_docx`,
  `assemble_news_daily_docx`, ...). Holiday planner: `holiday_report.assemble_holiday_docx`.

## Diagnostics and parsing

```python
from epic_news.utils.diagnostics import dump_crewai_state, parse_crewai_output

dump_crewai_state(output, "POEM")                      # writes a JSON dump under debug/
model = parse_crewai_output(output, PoemJSONOutput, inputs)
```

`parse_crewai_output` uses a pydantic output when present, else strips code fences and
preamble text from `.raw`, repairs the JSON and validates; it raises `ValueError` on empty/invalid output. Also exported:
`make_serializable`, `analyze_crewai_output`, `log_state_keys`.

`ContentExtractorFactory.extract_content(state_data, crew_type)` /
`get_extractor(crew_type)`: only `DEEPRESEARCH` has a dedicated extractor; everything else
gets `GenericExtractor`.

## Other helpers

- **Directories**: `ensure_output_directories()` runs once at flow startup. Do not call
  `os.makedirs()` in crew/task logic.
- **Logging**: Loguru only (`from loguru import logger`); `setup_logging(log_level, log_to_file, log_dir, app_name)`.
- **Cancellation**: long loops call `raise_if_cancelled(what)`; `install_force_quit_handler()`
  arms the Ctrl+C watchdog (`EPIC_NEWS_FORCE_QUIT_GRACE_SECONDS`, default 5).
- **Email**: `send_report_email(...)` calls Composio `GMAIL_SEND_EMAIL` directly and raises
  `EmailDeliveryError` unless delivery is confirmed; never delegate sending to an agent.
- **Observability**: `get_observability_tools(crew_name)` returns tracer/dashboard/guard
  (used by `company_news`); `trace_span(name, attrs)` is a no-op without Langfuse keys.

## Related Documentation

- Root `CLAUDE.md`, `src/epic_news/crews/CLAUDE.md`, `src/epic_news/tools/CLAUDE.md`
- `docs/reference/RENDERING_ARCHITECTURE.md`, `docs/adr/ADR-005-deterministic-html-rendering.md`
