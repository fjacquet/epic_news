# ADR-017: DOCX as the Only Report Format

## Status

Accepted (2026-10-05). Supersedes [ADR-005](ADR-005-deterministic-html-rendering.md) and [ADR-011](ADR-011-consolidated-report-css.md).

## Context

Every crew report could be produced in two formats, and HTML was the default:

- HTML went through `render_and_write_html()`, `TemplateManager`, a `RendererFactory` with one `BaseRenderer` subclass per crew, a theme (`config/ui_theme.py`) and a repository-level `templates/` directory with the report CSS. `utils/html/` alone was about 6.3k lines in 31 files.
- DOCX went through one assembler per crew (`utils/docx_report/crews/`), built from the same Pydantic models and converted with pandoc ([ADR-013](ADR-013-docx-system-pandoc-image-allowlist.md)).
- `emit_report()` chose between them from `OUTPUT_FORMAT`, `state.output_format` (parsed from the request) or the HTML default.

The two paths were maintained in parallel and drifted. The S3 survey found renderers reading fields the models no longer had, and assemblers covering data the renderers ignored. Every report change had to be made twice, and every consumer (email, Streamlit app) had to cope with either file type. All crews except the poem already had a DOCX assembler.

## Decision

- Reports are DOCX only. Each report step builds its file through the crew's assembler and `emit_report(state, assemble_docx)` stores the path in `state.output_file`. The poem has a deterministic assembler (no LLM call).
- `OUTPUT_FORMAT`, `state.output_format` and `format_selection.py` are removed, with `render_and_write_html`, `resolve_report_html`, `utils/html/`, `templates/`, `config/ui_theme.py`, the report CSS, the `report.md` PESTEL side file, and the direct dependencies `nh3`, `markdown-it-py` and `beautifulsoup4`.
- Email carries a short body (the request, HTML-escaped) and the DOCX as attachment. If the DOCX is missing, nothing is sent and `email_sent` stays `False`.
- The Streamlit app offers the DOCX bytes with `st.download_button`; it no longer displays the report.
- A report step that cannot build its file raises and stops the run, so nothing partial is emailed. `assemble_fragments` (shared by every assembler) raises `RuntimeError` before writing if any narrated section degrades to a placeholder. A narrated section whose context is empty or blank is dropped from the report, not narrated, and an info log line names it; if no section is left, it raises `ValueError`. Deep research has no exception: it parses its output with `load_or_parse_model`, deletes any stale `report.json` first, and raises `ValueError` on unusable output. The OSINT `global_report.json` is always rewritten from the parsed model, and the OSINT assembler raises if it is missing.
- `build_docx` refuses any path outside `output/` with `ValueError`, taking over the guard `render_and_write_html` enforced for HTML ([ADR-015](ADR-015-output-trust-boundary.md)).
- Pandoc is a runtime requirement for every report (already installed in the Docker image and in CI).

## Consequences

- About 6.3k lines of renderer code, the templates and the theme are gone, with their tests and three direct dependencies. One report path remains to maintain.
- Reports are no longer readable in the email body or in the app; the reader opens the attachment or downloads the file.
- Sections an assembler narrates cost one LLM call each (run in parallel, capped by `DOCX_FRAGMENT_CONCURRENCY`); the HTML path made none for these. Calls per report: deep research 2 plus one per research section (at most 22), PESTEL 8, saint 5, sales prospecting 3, menu designer 3, meeting prep 2, shopping 2, OSINT 2, company news up to 2, book summary 1 plus one per content section, fin daily 1, news daily 1, RSS weekly up to 1, cooking up to 1, poem 0. A section dropped for empty context costs no call.
- There is no HTML theme or print stylesheet. Appearance comes from `reference.docx` (see `scripts/make_reference_docx.py`).
- `utils/extractors/` is deleted (S3): deep research has one `DeepResearchReport` schema and no fallback that produces a canned report.
- Anyone who needs HTML again must add a new path; none is kept as a fallback.
