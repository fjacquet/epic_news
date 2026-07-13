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
   (holiday's exact pattern), fed to a **shared** `build_docx()` engine. **Data-heavy
   crews render their structured data as deterministic Markdown tables** (exact values
   preserved — an LLM must never retype financial figures or grids) and narrate only
   the prose around them; see §3.3.
5. **Scope:** build the reusable framework + refactor holiday onto it + add a DOCX
   assembler for **every routable crew** (14 crews) except POEM.

## 3. Architecture

Three parts: a shared `docx_report` framework, a runtime format resolver, and one
assembler per crew wired into the existing flow render step. An assembler's sections
are **LLM-narrated** where prose helps and **deterministic** where precision matters.

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
  — a thin shared helper. Each entry in `sections` is **either**:
  - a **narrated** spec `Section(heading, instruction, context)` → passed to
    `generate_fragment` (LLM writes the prose), **or**
  - a **deterministic** spec `Section(heading, body=<markdown>)` → the pre-built
    Markdown (e.g. a table rendered from the model) is used verbatim, no LLM call.

  The helper renders each entry accordingly and hands the ordered fragments to
  `build_docx`. This keeps each per-crew assembler tiny while letting data-heavy
  crews preserve exact values in Markdown tables and narrate only their commentary.
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

One module per crew, `src/epic_news/utils/docx_report/crews/{crew}.py`:

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
domain), the `sections` list, and `_extract` (mapping the crew's `crew_result` /
Pydantic model into each section's context). Everything downstream — narration,
placeholder fallback, Pandoc, TOC, branding — is shared.

**Narrative vs data-heavy crews.** Prose-heavy crews (deep_research, OSINT, saint,
book_summary, PESTEL, meeting_prep, sales_prospecting, shopping, company_news) use
mostly narrated sections. Data-heavy crews (fin_daily, menu, rss, news_daily,
cooking) build **deterministic Markdown tables/lists from the model** for their
structured content (exact figures, prices, feed items, ingredients preserved) and
add at most a short narrated intro/commentary. The LLM never re-types the data.

### 3.4 Flow dispatch integration

A shared render helper (used by each crew's `generate_*` method) selects
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
produce DOCX on request." **Every routable crew gets one except POEM.**

| Mostly LLM-narrated (prose) | Deterministic tables + narrated commentary |
|---|---|
| DEEPRESEARCH, OSINT, BOOK_SUMMARY | FINDAILY (numbers/tables) |
| MEETING_PREP, PESTEL, SALES_PROSPECTING | MENU (menu + shopping grid) |
| SAINT (biography), SHOPPING (advice) | RSS (feed-item list) |
| COMPANY_NEWS | NEWSDAILY (news items), COOKING (ingredients/steps) |
| HOLIDAY (refactor onto framework; stays DOCX-default) | — |

**14 new/refactored assemblers** (9 prose-leaning + 5 data-heavy) + HOLIDAY on the
shared framework. POEM (creative text) is excluded. The two groups share the same
framework and contract; they differ only in how many sections are narrated vs
deterministic.

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
- **Data fidelity (data-heavy crews)** — assert exact values (figures, prices, feed
  URLs, ingredient quantities) from the model appear verbatim in the DOCX, and that
  deterministic-table sections make **no** LLM call (the stub LLM is asserted
  uninvoked for those sections).
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
- **Two paths maintained per crew** (HTML renderer + DOCX assembler) — inherent to
  runtime flexibility and the explicit requirement; 14 crews now carry both.
- **Parse false positives/negatives** — mitigated by the deterministic flag override
  and the HTML-safe default.
- **Data fidelity** — LLM narration of precise figures/tables would drop or
  hallucinate values; mitigated by rendering data-heavy content as **deterministic
  Markdown tables** from the model (no LLM in the loop for those sections) and
  asserting verbatim values in tests.

## 8. Out of scope

- A DOCX assembler for POEM (creative text; stays HTML).
- Async/parallel section narration (performance optimization).
- PDF output, an HTML fallback renderer for holiday, or retiring any HTML renderer.
- Changing `send_email`, the classifier routing, or crew logic beyond adding the
  format field and dispatch.

## 9. Success criteria

- A shared `docx_report` framework exists; `holiday_report` is refactored onto it
  with holiday's tests still green.
- HTML remains the default and every existing HTML report is byte-for-byte unchanged
  when no DOCX is requested.
- For each of the 14 crews, a DOCX request (parsed phrase or `OUTPUT_FORMAT=docx`)
  produces a valid, TOC'd `.docx` delivered by email; a normal request still produces
  the HTML. Data-heavy crews' DOCX contains their exact figures/items in tables.
- `resolve_output_format` honours flag > parse > default, verified by tests.
- Every new unit (resolver, parser, framework helpers, each assembler) has tests;
  the full suite is green.
