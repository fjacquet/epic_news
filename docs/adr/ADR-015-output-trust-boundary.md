# ADR-015: `output/` as the Trust Boundary for Agent File Access

## Status

Accepted (2026-10-04)

## Context

Agents combine three things that are dangerous together: untrusted input (scraped pages, RSS items, search results, the API request), access to private data (local files such as `.env`), and an exit channel (web requests, emailed reports). A prompt-injected agent could read a secret and leak it through a URL or a generated report. The 2026-10-04 audit found several independent paths: an unscoped `FileReadTool`, an HTML-to-PDF tool whose paths the LLM chose freely, WeasyPrint and pandoc following `file://` and HTTP links, a report path built from an unsanitised topic, and LLM or RSS text inserted into HTML without escaping.

## Decision

The working-directory `output/` folder is the only place agent-driven code may write to, and the default place it may read from. Every component enforces its root with the same rule (`Path(...).resolve().is_relative_to(root.resolve())`):

- `render_and_write_html` (`src/epic_news/utils/flow_helpers.py`) refuses any target outside `output/`.
- Agents that need to read files get `OutputFileReadTool` (`src/epic_news/tools/output_file_read_tool.py`) instead of crewai's unscoped `FileReadTool`. It resolves symlinks, refuses anything outside its `root` (default `output`), caps reads at 200k characters and returns JSON. fin_daily's stock analyst uses `OutputFileReadTool(root="data")` to read the portfolio CSVs, a read-only exception scoped to that directory. An agent that searches or scrapes the web never also holds an unscoped file reader (enforced by `tests/crews/test_agent_settings_contract.py`, ADR-014).
- DOCX images are limited to files under `output/` (ADR-013).
- Report slugs are built with `create_topic_slug()`, never from raw request text.

PDF export (`HtmlToPdfTool` and the WeasyPrint dependency) was removed in #221. The HTML-to-PDF path is gone rather than confined.

Content crossing into HTML is treated as untrusted: TemplateManager escapes titles and error text, RSS summaries are sanitised with `nh3`, and Streamlit shows report HTML through `st.html` (DOMPurify) instead of `unsafe_allow_html`.

## Consequences

- Prompt injection can no longer turn a tool into a local-file reader or a network client through these paths. Removing PDF export also removed WeasyPrint's URL fetching and its system libraries.
- Code that legitimately needs files elsewhere (templates, `reference.docx`, the Lua filter) reads them from Python, not through agent tools.
- Paths are resolved against the working directory, so the flow must run from the project root (`crewai flow kickoff` already does).
- New tools that touch the filesystem must apply the same check; reviewers should reject agent-facing file access outside `output/`.
