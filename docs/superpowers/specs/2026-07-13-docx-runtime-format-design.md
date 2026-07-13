# DOCX Report Rendering — Runtime Format Selection — Design

- **Status:** Draft for review
- **Date:** 2026-07-13
- **Branch:** `feat/docx-runtime-format`

## 1. Problem & Goal

Holiday reports are delivered as DOCX and read noticeably better than the HTML
reports the other crews produce — partly because DOCX is a cleaner document
format, and largely because holiday's DOCX is **LLM-narrated**: `assemble.py`
re-prompts an LLM to write flowing prose per section, then `docx_builder.py`
assembles the Markdown fragments into a DOCX via Pandoc. Every other crew instead
renders a structured Pydantic model into themed HTML.

**Goal:** make DOCX a first-class, on-demand output for the narrative-heavy crews,
without losing the HTML any crew has today. HTML remains the default; a request can
opt into DOCX at run time; narrative crews gain a holiday-style LLM-narrated DOCX
assembler built on a shared, crew-agnostic framework factored out of holiday.

## 2. Locked decisions (from brainstorming)

1. **HTML stays the default output.** DOCX is opt-in.
2. **Opt-in is at run time, not design time.** Both an HTML renderer and a DOCX
   assembler coexist for a converted crew; the format is chosen per request.
   Nothing is retired — no crew loses its HTML view.
3. **Format trigger: flag overrides parse.** The output format is parsed from the
   request's natural language by default; an explicit flag/env (`OUTPUT_FORMAT`)
   wins when set. Default is HTML.
4. **Per-crew bespoke builders**, producing **LLM-narrated** prose sections
   (holiday's exact pattern), fed to a **shared** `build_docx()` engine.
5. **Scope:** build the reusable framework + refactor holiday onto it + add DOCX
   assemblers for all narrative-heavy crews.

## 3. Architecture

Three parts: a shared `docx_report` framework, a runtime format resolver, and one
LLM-narrated assembler per narrative crew wired into the existing flow render step.

### 3.1 Shared framework — `src/epic_news/utils/docx_report/`

Factored from the existing `holiday_report/` package, with travel-specific coupling
removed:

- **`docx_builder.build_docx(fragments, meta, output_path) -> str`** — moved
  verbatim from `holiday_report/docx_builder.py`. Already crew-agnostic: ordered
  `(heading, markdown_body)` fragments → DOCX with a TOC via Pandoc, including the
  `markdown-yaml_metadata_block` fix (a `---` in fragment bodies must stay a
  thematic break, not a YAML block → avoids "Pandoc died with exitcode 64").
- **`fragments.generate_fragment(heading, instruction, context, llm, system) -> str`**
  — factored from `holiday_report/fragments.py`. The **`system` persona is now a
  parameter** (holiday's hard-coded "rédacteur de carnet de voyage" becomes a
  per-crew persona string). Preserves graceful degradation: on empty/failed LLM
  output it returns a `> ⚠️ Section « … » indisponible` placeholder and never raises.
- **`assemble.assemble_fragments(sections, meta, output_path, llm, system) -> str`**
  — a thin shared helper. `sections` is a list of `(heading, instruction, context)`
  specs; it calls `generate_fragment` for each and hands the results to
  `build_docx`. This is what keeps each per-crew assembler tiny.
- **`reference.docx`** — a shared branded Pandoc reference document (fonts, heading
  styles) passed to Pandoc via `--reference-doc`, so every DOCX has consistent Epic
  News styling. Bundled as a package data file; `build_docx` references it when present.

**Holiday is refactored to consume `docx_report`** (Section 3.5): it stops being a
special case and becomes the first framework consumer, keeping only its genuinely
bespoke `skeleton.py` (itinerary day expansion) local. This proves the framework
does not regress an already-working crew.

### 3.2 Runtime format resolution

A single resolver, precedence **flag → parsed intent → default HTML**:

```python
def resolve_output_format(state) -> str:              # "html" | "docx"
    env = os.getenv("OUTPUT_FORMAT")
    if env in ("html", "docx"):
        return env                                    # explicit flag/env wins
    return getattr(state, "output_format", None) or "html"
```

- **Parse:** during classify/extract, request intent is detected (phrases like
  "as a Word document", "en DOCX", "génère un document Word", "format docx") and
  `state.output_format` is set to `"docx"`; otherwise it stays unset (→ HTML).
  Parsing is a small, deterministic keyword/pattern matcher — **not** an extra LLM
  call.
- **Flag override:** `OUTPUT_FORMAT=docx|html` (env var, mirrored by an optional
  `state.output_format` explicit set) wins over the parse. Deterministic, testable,
  and the mechanism the verification sweep / automation uses.

`state` gains an `output_format: str | None = None` field (defaults to None → HTML).

### 3.3 Per-crew assembler contract

One module per narrative crew, `src/epic_news/utils/docx_report/crews/{crew}.py`:

```python
def assemble_{crew}_docx(crew_result, inputs, output_path, llm=None) -> str:
    llm = llm or LLMConfig.get_openrouter_llm()
    ctx = _extract(crew_result, inputs)          # slice the crew's output per section
    sections = [
        ("Executive Summary", "Résume les conclusions clés.", ctx.summary),
        ("Detailed Findings", "Développe chaque constat.",    ctx.findings),
        # ... crew-specific section list ...
    ]
    meta = {"title": ..., "date": inputs.get("current_date", ""), "author": "Epic News"}
    return assemble_fragments(sections, meta, output_path, llm, system=_PERSONA)
```

The **only per-crew work**: `_PERSONA` (a one-line system prompt matching the report
domain), the `sections` list (headings + instructions), and `_extract` (mapping the
crew's `crew_result` / Pydantic model into each section's context). Everything
downstream — narration, placeholder fallback, Pandoc, TOC, branding — is shared.

### 3.4 Flow dispatch integration

A shared render helper (used by each narrative crew's `generate_*` method) selects
the path:

```python
fmt = resolve_output_format(self.state)
if fmt == "docx" and selected_crew in DOCX_ASSEMBLERS:
    self.state.output_file = DOCX_ASSEMBLERS[selected_crew](result, inputs, docx_path)
else:
    render_and_write_html(selected_crew, model, html_path)   # unchanged default
    self.state.output_file = html_path
```

- **`DOCX_ASSEMBLERS`** — a registry mapping crew identifier → `assemble_*` function.
- A DOCX request for a crew **not** in the registry falls back to HTML and logs
  `"DOCX requested but no assembler for <crew>; rendering HTML"`.
- HTML-only crews are unchanged: they never consult the resolver (or consult it and
  always fall back), and keep calling `render_and_write_html` exactly as today.
- **`send_email` needs no change** — it already attaches whatever `state.output_file`
  points at, and already handles `.docx` (holiday proves it).

### 3.5 Crew classification

DOCX assemblers are **additive** (no HTML is lost), so this is "which crews can
produce DOCX on request," not "which crews are converted."

| Gains a DOCX assembler (this effort) | HTML-only (no assembler this effort) |
|---|---|
| DEEPRESEARCH, OSINT, BOOK_SUMMARY | FINDAILY (numbers/tables) |
| MEETING_PREP, PESTEL, SALES_PROSPECTING | MENU (menu + shopping grid) |
| SAINT (biography), SHOPPING (advice) | RSS (feed-item list) |
| COMPANY_NEWS | NEWSDAILY, COOKING (data-heavy; trivial to add later) |
| HOLIDAY (refactor onto framework; stays DOCX-default) | POEM (creative text; out of scope) |

**9 new assemblers + holiday refactored.** NEWSDAILY and COOKING are deliberately
deferred (data-heavy); adding them later is the same recipe and needs no framework
change.

## 4. Data flow

1. Request → classify/extract → sets `state.output_format` if DOCX intent parsed.
2. Route to `generate_{crew}` → run the crew → `crew_result`.
3. `resolve_output_format(state)` → `"html"` or `"docx"`.
4. `docx` + assembler present → `assemble_{crew}_docx` → per-section
   `generate_fragment` (LLM) → `build_docx` (Pandoc + TOC + reference.docx) →
   `report.docx`; else → `render_and_write_html` → `report.html`.
5. `state.output_file` = whichever path; `send_email` attaches it.

## 5. Error handling

- **Per-section LLM failure** → `generate_fragment` returns the placeholder; the
  report still builds (holiday's proven behavior). Never crashes the flow.
- **Pandoc failure** → surfaces as an exception from `build_docx`; caught by the
  flow's existing kickoff try/except and logged (not silently swallowed).
- **DOCX requested, no assembler** → HTML fallback + a warning log (Section 3.4).
- **Format parse ambiguity** → defaults to HTML (safe); the explicit flag is the
  deterministic escape hatch.

## 6. Testing strategy

LLM-narrated prose is non-deterministic, so assemblers are tested with a **stub
LLM** (returns canned Markdown):

- **`resolve_output_format`** — flag wins over parse; parse over default; default is
  HTML; invalid `OUTPUT_FORMAT` ignored.
- **Intent parser** — DOCX phrasings (FR/EN) → `"docx"`; neutral requests → unset;
  case-insensitive.
- **`generate_fragment`** — three paths: content returned; empty → placeholder;
  raises → placeholder.
- **`assemble_fragments`** and **each `assemble_{crew}_docx`** — with a stub LLM,
  assert the correct section headings appear in order, `_extract` pulls the right
  context, and `build_docx` yields a valid, openable `.docx` (verify by unzipping the
  OOXML or round-tripping through Pandoc). Mirrors holiday's existing tests.
- **Dispatch** — `docx` + assembler → `.docx` output_file; `docx` + no assembler →
  HTML fallback; `html` → HTML.
- **Holiday refactor** — its existing tests must stay green against the shared
  framework (regression guard).

## 7. Risks & cost

- **Recurring LLM cost is now opt-in per run.** Narration (~5–8 LLM calls per report,
  serial) runs only when DOCX is requested — HTML default incurs zero narration cost.
  This is strictly better than a design-time (always-DOCX) model.
- **Latency** when DOCX is requested: sections are narrated serially (holiday's
  current behavior). Async-parallel narration is a possible later optimization,
  **out of scope** here.
- **Pandoc** is a hard runtime dependency — already true for holiday, so Docker/CI
  already provide it; converted crews now depend on it too.
- **Two paths maintained per narrative crew** (HTML renderer + DOCX assembler) —
  inherent to runtime flexibility and the explicit requirement.
- **Parse false positives/negatives** — mitigated by the deterministic flag override
  and the HTML-safe default.

## 8. Out of scope

- Converting NEWSDAILY / COOKING / data-heavy crews (deferred; same recipe later).
- Async/parallel section narration (performance optimization).
- PDF output, an HTML fallback renderer for holiday, or retiring any HTML renderer.
- Changing `send_email`, the classifier routing, or crew logic beyond adding the
  format field and dispatch.

## 9. Success criteria

- A shared `docx_report` framework exists; `holiday_report` is refactored onto it
  with holiday's tests still green.
- HTML remains the default and every existing HTML report is byte-for-byte unchanged
  when no DOCX is requested.
- For each of the 9 narrative crews, a DOCX request (parsed phrase or
  `OUTPUT_FORMAT=docx`) produces a valid, LLM-narrated, TOC'd `.docx` delivered by
  email; a normal request still produces the HTML.
- `resolve_output_format` honours flag > parse > default, verified by tests.
- Every new unit (resolver, parser, framework helpers, each assembler) has tests;
  the full suite is green.
