# Changelog

All notable changes to Epic News are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [3.5.0] — 2026-07-13

A readability release. DOCX reports read better than HTML for most crews, so every routable `ReceptionFlow` crew now emits **HTML by default and a DOCX on request** — a runtime choice rather than a per-crew rewrite. Precise data (prices, figures, quantities, ingredient amounts, URLs, citations) is rendered deterministically from the model and never re-typed by the LLM; only prose sections are narrated. A whole-branch review verified that invariant across all 14 assemblers.

### Added
- **Runtime output-format selection.** `OUTPUT_FORMAT=docx` (or DOCX intent parsed from the request) switches any crew's report to a Word document; HTML stays the default. Precedence: `OUTPUT_FORMAT` env → parsed request intent → HTML. A single dispatch helper (`emit_report`) runs the selected renderer and records the produced path as the emailed attachment.
- **Shared `docx_report` framework** — `Section` + `assemble_fragments` (Pandoc) + `md_table`, splitting each section between deterministic verbatim Markdown (`body=`) and single-call LLM narration (`instruction` + `context`).
- **DOCX assemblers for 14 crews** (every routable crew except POEM), each rendering data deterministically and narrating only prose.
- **`docs/sweep-runbook.md`** documenting the format mechanics and the two-format verification.

### Changed
- **Holiday crew refactored onto the shared `docx_report` framework**, dropping its bespoke local DOCX modules.
- **Post-render log lines report the actual `output_file` path** (SAINT / SHOPPING / NEWSDAILY) instead of a hardcoded "HTML written", so logs match what was written under `OUTPUT_FORMAT=docx`.

## [3.4.1] — 2026-07-13

A reliability release. Every routable `ReceptionFlow` crew was run end-to-end on the current native-Gemini + ReAct stack and the runtime failures that only surface at execution time were fixed — the kind a "report exists + email sent" check can't catch.

### Fixed
- **Cooking report rendered one letter per line.** `CookingRenderer` received `PaprikaRecipe.model_dump()`, where `ingredients`/`directions` are single text blocks (`str`), and iterated the string — emitting one `<li>` per character. It now coerces a `str` field into line/step lists and falls back from `instructions` to the `directions` key, so the Instructions section renders too.
- **Successful `crewai flow kickoff` exited 1.** `kickoff()` returned the `ReceptionFlow` object, which the `sys.exit(kickoff())` console entry printed and treated as a non-zero exit. It now returns `None`.
- **RSS weekly flow called a sync kickoff from an async method.** `generate_rss_weekly` now awaits `akickoff_flow`.
- **Menu report generated but never emailed.** `generate_menu_designer` now sets `state.output_file` so the menu report is the emailed attachment instead of the classify path.

### Changed
- **`EPIC_NEWS_REQUEST` override is no longer silent.** The sweep/automation hook in `kickoff()` only fires when no explicit request is passed and logs a warning naming the forced request, so a leaked or stale environment variable can't silently reroute a real request.

### Added
- **`scripts/verify_all_crews.sh`** — a repeatable end-to-end verification driver (one flow or all, via `EPIC_NEWS_REQUEST` + `MAIL`), and **`docs/sweep-runbook.md`** documenting how to run it and read the results.

### Housekeeping
- Removed stale stray root artifacts (`curl.txt`, `changes.md`, `crewai_flow.html`, `crewai-rag-tool.lock`) and expanded `.gitignore` to cover local runtime clutter (`.cache/`, `logs/*.out`, `.DS_Store`, `.composio.lock`, `docker-compose.override.yml`).

## [3.4.0] — 2026-07-12

A prompt-enrichment release. The raw user request is now rewritten into a clean, complete brief **before** structured extraction, and that brief becomes the working `context` every downstream crew sees — with deterministic length caps so a degenerate LLM rewrite can no longer bloat a crew's prompt. Ships alongside a batch of flow and extraction reliability fixes.

### Added
- **Prompt enrichment in `InformationExtractionCrew`**: the user request is enriched into a clean rewrite (`enriched_brief`) before fields are extracted, captured into flow state during extraction, and surfaced as the downstream `context` for every crew. A clean, complete rewrite of the whole request is a better working context than the raw message.

### Fixed
- **Free-text crew inputs are now length-capped deterministically** (`MAX_FREETEXT_CHARS = 1500`): a real extraction run looped `user_preferences_and_constraints` into an ~8 KB block of the same sentences repeated dozens of times, bloating the downstream crew's prompt and starving its planner. Both `user_preferences_and_constraints` and the enriched brief handed to crews via `context` now pass through the same cap (#156).
- **Multi-stop trips are parsed correctly**, and the extraction no longer repeats the user's preferences back into its own output.
- **The holiday reporter agent no longer carries tools** — it only renders its report, so no action traces leak into the output (two-agent researcher/reporter split).
- **The classifier's routing decision is no longer emailed as a holiday report** — a misrouted flow branch was shipping the classifier's output as the final report.
- **CrewAI agent `reasoning` disabled across 15 crews**, and **CrewAI `Memory` removed from `ReceptionFlow`** — the flow was configured with a LanceDB memory store but no embedder, which crashed `crewai flow kickoff` with a generic `exit status 1`. The project uses real-time retrieval, not RAG/memory (#156).

### Changed
- Refreshed locked dependencies: langfuse 4.14.0, litellm 1.92.0, pyarrow 25.0.0, and related transitive pins.

## [3.3.5] — 2026-07-10

A deep-research reliability fix. A single omitted field from the report-writing LLM no longer discards the entire (~9-minute) research run.

### Fixed
- **A ~9-minute deep-research run died at the final step** (#154) with `3 validation errors for DeepResearchReport: methodology / sources_count / confidence_level — Field required`. The crew validates the LLM's one-shot JSON against `deep_research_report.py`'s `DeepResearchReport`, which marked those three strictly required — but the task instructions didn't list two of them as mandatory and required a phantom `conclusions` field this model never had, and the example JSON described the *other* class also named `DeepResearchReport`. The model was told one contract and validated against another. `methodology` and `confidence_level` now default (the renderer already treats both as optional), as do `key_findings` / `research_sections` / section `sources` (same failure class); genuinely load-bearing fields (`title`, `topic`, `executive_summary`) stay required.
- **`sources_count` is now computed from the sections**, not trusted from the LLM — counting is deterministic, not a reasoning task. An explicit count is kept only when no section carries sources.
- **`report_writing_task` instructions rewritten** to match the actual model exactly (no `conclusions` / `credibility_score` / `extraction_date`) and to tell the model not to emit `sources_count`.

## [3.3.4] — 2026-07-10

A bug-fix and hardening release covering the HTML report body and email delivery. Renders agent-authored Markdown correctly across the whole renderer suite, and replaces the LLM-driven email step with a deterministic sender after a production run showed the model corrupting the recipient and body.

### Fixed
- **Agent Markdown leaked as literal text across the renderer suite** (#151): crews return structured JSON, but the model writes Markdown (`**bold**`, `-` bullets, links) *inside* the JSON string fields. Renderers assigned those strings with `tag.string = …`, which escapes them, so readers saw literal `**bold**`. `BaseRenderer` now renders inline/block Markdown in safe mode (`html=False`), and `render_text_section` defaults to `as_markdown=True`; 20 renderers were converted. `poem` is deliberately excluded — whitespace and literal characters are the content of a poem — and is pinned as a negative-control test.
- **Deep-research email reported failure and shipped nothing** (#152): the flow handed a valid recipient to an email agent, which called `GMAIL_SEND_EMAIL` with the placeholder `[EMAIL]`, invented a `from_email`, and rewrote the French article *la* as `[ADDRESS]` — the model was anonymising PII it had been asked to reproduce. Delivery is now deterministic: `send_email()` calls Gmail directly with the validated recipient and the rendered report, and `email_sent` reflects only a delivery the API confirmed (never an agent's self-report).
- **Email attached the wrong file and 404'd**: `prepare_email_params` used the crew's JSON *write target* (`report.json`) as both body and attachment, so the rendered `report.html` was never sent (`html_preserved: false`). Composio also treats a local `attachment` path as an already-uploaded storage key, so it 404'd. The body/attachment now resolve to the rendered HTML report, and attachments upload from an allowlist confined to the output directory.

### Security
- Every renderer now interprets agent text as Markdown, so raw HTML in crew output is a boundary: markdown-it runs with `html=False` and link validation, so `<script>`/`<img onerror>`/`<svg onload>`/`<iframe>` stay escaped and `[x](javascript:…)` is refused. Verified against 7 payloads across every renderer.
- Composio auto-upload is scoped via `file_upload_dirs` to the output directory, so it can never read files outside our generated reports.

## [3.3.3] — 2026-07-05

A bug-fix, security-hardening, and test-coverage release. Fixes HTML renderers that produced broken or blank reports, a JSON-repair correctness bug, and two stored-XSS vectors; removes legacy dead code; and lands a large test-coverage increase (63% → 82%).

### Fixed
- **Systemic `class_=` broken CSS across 6 renderers** (menu, cooking, generic, shopping, poem, financial): `soup.new_tag(..., class_="X")` emitted a literal `class_="X"` attribute instead of `class="X"`, so those reports rendered **unstyled**. 85 call sites corrected to `attrs={"class": "X"}` (BeautifulSoup's `new_tag` does not special-case the trailing underscore, unlike `create_soup`).
- **SHOPPING report rendered blank in production**: `ShoppingRenderer` read flat keys the `ShoppingAdviceOutput` model never produces (`product_name`, `price_comparison`, `recommendation`, `alternatives`, top-level `pros`/`cons`), so every section guard failed silently and the report was an empty wrapper. Rewrote the renderer to consume the real model contract (product overview, CH/FR price tables, competitors, best deals, recommendations); the report `<title>` now reads `product_info.name`; removed the unused `ShoppingExtractor`; added an empty-state for degenerate payloads.
- **Saint's name never displayed**: `SaintRenderer` read `data["name"]`, but the model field is `saint_name` → always the generic "✨ Saint" fallback. Now resolves `saint_name` (with a legacy `name` fallback).
- **OSINT table of contents never linked the geospatial section**: the TOC derived `geospatial` from the section id while the data key is `geospatial_analysis`. Fixed via a targeted key mapping.
- **`FinancialRenderer` ignored the report `title`** (header was hardcoded) and could silently drop metric/analysis sections on unusable input; also removed a large legacy dead-code surface (fields the current `FinancialReport` model doesn't provide).
- **JSON-repair mangled Python literals**: `diagnostics.parsing._attempt_json_repair` turned `True`/`False`/`None` into quoted strings with a stray trailing `", "` (e.g. `{"a": True}` → `{"a": "true, "}`), because a later bare-string-quoting pass re-wrapped the lowercased tokens. A negative lookahead now preserves them as JSON `true`/`false`/`null`.
- **Holiday planner crashed at runtime** with `ValidationError for TaskOutput / raw: Input should be a valid string [input_value=[ChatCompletionMessageToolCall(...)]]`: CrewAI 1.15's concurrent-async path leaked a tool-calling agent's final turn into `TaskOutput.raw` (which must be a `str`). The two `async_execution=True` tasks now run sequentially.
- **`news_daily` final report showed raw Markdown** and tech-topic research requests misrouted to `NEWSDAILY` instead of `DEEPRESEARCH`; the email recipient path is hardened against empty/malformed `MAIL` values.

### Security
- **Stored-XSS in `cross_reference_report_renderer`**: data-derived fields (`target`, `executive_summary`, findings, gaps, …) were interpolated into raw f-string HTML without escaping. All seven interpolation sites now go through `html.escape`.
- **Stored-XSS in `shopping_renderer` retailer links**: an unvalidated `javascript:`/`data:` retailer URL from crew output became a clickable vector (HTML-escaping does not neutralise the scheme). Retailer links are now restricted to `http(s)://`; other schemes render as plain text.

### Changed / Internal
- **Test coverage 63% → 82%** (+206 tests, ~2,200 lines newly covered) across 16 renderer / parsing / observability modules, authored via parallel subagents.
- Removed the unused `ShoppingExtractor` and the `FinancialRenderer` legacy dead-code branches.

## [3.3.2] — 2026-07-04

A crew-execution hotfix release. Crews were unable to run against OpenRouter because CrewAI 1.15's native provider sent strict schemas that upstream models reject; routing now goes through LiteLLM. Also fixes the book-summary report never displaying in the UI and a Loguru crash in the Streamlit error handler.

### Fixed
- **CrewAI 1.15 native-provider strict-schema rejection** (`LLMConfig`): CrewAI 1.15's native `OpenAICompatibleCompletion` provider (auto-selected for `openrouter/…` models) sends tool **and** response-format schemas with OpenAI strict-mode (`strict: true`), generated from our Pydantic models. Those schemas aren't strict-compliant (`title`/`default`/`anyOf`, no `additionalProperties:false`), so OpenRouter's upstream providers reject them — Mistral with `400 "Invalid structured output syntax"` (code 3051), OpenAI with `Invalid schema for function 'render_report_tool'`. `LLMConfig.get_openrouter_llm()` now passes `is_litellm=True`, routing through LiteLLM which sends the same schemas **without** strict-mode; verified that `mistral-small-2603` accepts the identical tool schema this way. Proven it was never a model-capability issue.
- **`reasoning_effort` normalization** (`LLMConfig`): the LiteLLM `LLM` class validates `reasoning_effort` against a lowercase `Literal['none','low','medium','high']`; the value is now stripped/lowercased (so `LLM_REASONING_EFFORT=LOW` works) and normalized to `None` when empty/`none` — the old native provider silently tolerated `""`.
- **Reports not displayed in the UI (7 flows)**: several `generate_*` flow methods left `self.state.output_file` pointing at the intermediate **JSON** path (or never set it) while rendering the report to **HTML** — `generate_book_summary`, `generate_poem`, `generate_news_company`, `generate_findaily`, `generate_saint_daily`, `generate_meeting_prep`, and `generate_holiday_plan`. Since the Streamlit UI / API locate the report via `flow.state.output_file`, they showed raw JSON or failed the existence check. All now set `output_file` to the rendered HTML path after `render_and_write_html`.
- **Loguru crash in Streamlit error handler** (`app.py`): the crew-thread error handler f-string-interpolated an exception whose message contained `{...}`, which Loguru re-parsed as format fields and raised `KeyError`. Switched to `logger.opt(exception=True).error("…: {}", e)`.
- **Book-summary report rendered raw Markdown**: `BookSummaryRenderer` inserted section content, the summary, and chapter focus as literal text (`tag.string = …`), so Markdown headings/lists/bold/tables showed as raw `##` / `|…|` markup instead of formatted HTML. These now go through `render_markdown_block`, and the shared safe Markdown parser (`base_renderer._get_markdown_parser`) gains GFM table support — raw HTML stays disabled for XSS safety.

### Tests
- `test_agent_llm_contract.py` now also accepts `is_litellm is True` as a copy-stable LLMConfig signal: the `configured_via_llmconfig` sentinel is a non-field attribute that Pydantic `model_copy` drops when CrewAI copies agents during crew assembly.

## [3.3.1] — 2026-07-04

### Fixed
- **api/streamlit Docker images crash-looped as non-root**: the Dockerfiles used a Python **3.11** base while the project requires **3.13**, so `uv` installed a managed 3.13 interpreter under `/root/.local`. The venv's `python3` symlinked into `/root` (mode `0700`), which the non-root `myuser` runtime user couldn't traverse — every start failed with `failed to canonicalize path '/app/.venv/bin/python3': Permission denied` and the container restart-looped. (`combined` was unaffected; it runs as root.) Fixed by switching all three image Dockerfiles to `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`, so the venv uses the world-readable system interpreter at `/usr/local`, which also drops the redundant second interpreter from the image.

## [3.3.0] — 2026-07-04

A correctness-and-confidence release. Request classification and flow routing get real bug fixes, every crew now builds its agents through `LLMConfig` (no more drifting or hardcoded LLM wiring), CrewAI 1.15's concurrent async tasks each receive an isolated agent copy, and the test suite is substantially hardened with deterministic end-to-end flow coverage and contract-freezing ratchet tests. No public API or breaking changes.

### Fixed
- **Flow routing cleanup** (`flow_enforcement` / `ReceptionFlow`): removed dead listeners and unroutable categories, with a new wiring contract test so orphaned routes can't silently reappear.
- **`SHOPPING` classification**: the classifier now offers the routable `SHOPPING` category instead of the orphan `SHOPPING_ADVISOR`, so shopping requests actually reach a crew. Added word-boundary category matching in the prompt guard to stop substring false-positives.
- **CrewAI 1.15 concurrent async isolation**: concurrent async tasks each receive their own isolated agent copy (`.copy()`), fixing shared-state contention under CrewAI 1.15.
- **Crews routed through `LLMConfig`**: `hr_reporter` plus five other crews now build their agents via `LLMConfig` instead of hardcoded/drifting configuration; added an LLM contract test and dropped the contract `xfail`.
- **`LLMConfig` contract sentinel** (refactor): repaired dead `field_mapping` keys and a `fin_daily` wiring gap, guarded by a contract sentinel.
- **Loguru in `flow_enforcement`**: switched from stdlib `logging` to Loguru and repaired malformed log placeholders.

### Security
- **OSV allowlist**: allowlisted `PYSEC-2026-597`, a duplicate OSV record of the already-accepted nltk advisory (`GHSA-p4gq-832x-fm9v`).

### Tests
- Deterministic end-to-end `ReceptionFlow` tests with stubbed `kickoff`.
- Ratchet test freezing the JSON-contract violation list; characterization of `to_crew_inputs()` with full `field_mapping` coverage.
- Deduplicated crew registry & e2e fixtures, cached scans, added a stacked-listen guard, and replaced debug prints with logger calls.

### Changed
- **Multi-arch Docker images** (`linux/amd64` + `linux/arm64`): the four image-publish workflows now build each architecture on a native runner (`ubuntu-latest` / `ubuntu-24.04-arm`, no QEMU emulation) and merge them into a single manifest list per tag, pushed to both Docker Hub and GHCR. Images now run natively on Apple Silicon instead of failing with `no matching manifest for linux/arm64/v8`.
- **Compose pulls from GHCR**: `docker-compose.yml` and `docker-compose.combined.yml` now reference `ghcr.io/fjacquet/…` images instead of Docker Hub, and the combined compose moves off the stale `:master` tag to `:latest`.
- **Dependencies**: updated `crewai-tools[mcp]` (#126, #128), two `python-minor-patch` groups of 9 updates each (#125, #127), and `actions/checkout` (#124); dropped unused `pytest-datadir`.
- **Dependabot auto-merge workflow** (#123): grouped minor/patch dependency PRs auto-merge once checks pass.

## [3.2.2] — 2026-06-19

### Security
- Waived the unfixable nltk advisory (`GHSA-p4gq-832x-fm9v`) in the `osv-scanner` allowlist.

### Fixed
- Dropped 4 unused `# type: ignore` comments. (#122)

## [3.2.1] — 2026-06-19

### Changed
- Maintenance release: merged Dependabot dependency and security updates — `python-multipart`, `cryptography`, `starlette`, `aiohttp`, a `python-minor-patch` group of 8, and a `github-actions` group of 2. (#115, #117–#121)

## [3.2.0] — 2026-06-07

Official secured SBOM and a leaner dependency set. No runtime API change.

### Added
- **Official secured SBOM**: `make sbom` generates a CycloneDX 1.6 SBOM from `uv.lock` (via `uv export` + pinned `cyclonedx-bom==7.3.0`). New `.github/workflows/security.yml` generates the SBOM, runs `deptry`, and scans with a checksum-verified `osv-scanner` v2.3.8 (blocking, allowlist-gated) on PR/push/weekly; the SBOM is attached to the release.
- **`deptry` dependency guardrail** (`make deps-audit`) to catch dependency drift.

### Changed
- Replaced the deprecated `safety` with `osv-scanner`; allowlist documented in `osv-scanner.toml`.
- Leaner dependencies: pruned the `chromadb` direct pin, `langsmith`, `pendulum`, and `vulture`; declared previously-undeclared-but-imported `urllib3`, `python-dateutil`, and `tabulate`.
- Dependabot now groups minor/patch updates into single weekly PRs (majors stay individual) and covers the `github-actions` ecosystem. (#114)

### Security
- Accepted risk: `chromadb` carries an unfixable upstream Critical (GHSA-f4j7-r4q5-qw2c), allowlisted in `osv-scanner.toml` — embedded use only, the vulnerable server endpoint is never exposed. Re-evaluate by 2026-09-07.

## [3.1.2] — 2026-05-03

Patch release restoring `make all` and clearing mypy noise after dependency bumps.

### Fixed
- **`make all` provisions a real dev environment**: the target now depends on `dev` (`--all-extras`) instead of production-only `install`, fixing ~90 `ModuleNotFoundError` collection failures caused by a stray Python 3.12 runtime.
- **Removed 17 obsolete `# type: ignore` directives** after `beautifulsoup4 4.14.x` shipped its own type stubs; fixed a real type error in `rss_weekly_renderer.py`.
- **Resurrected `rss_weekly_converter.py`**: corrected the import path (`epic_news.models.crews.rss_weekly_report`) and added test coverage. (#91)

### Compatibility
- No public API or behavior changes; renderer HTML output is unchanged.

## [3.1.1] — 2026-05-03

### Fixed
- **CI green again on `main`**: the v3.1.0 CSS additions (`.opportunity-card`, `.threat-card`, `.recommendation-card`, `.pestel-report` scope) drifted three `pytest-regressions` HTML snapshots — `FINDAILY`, `NEWSDAILY`, `SHOPPING` — because `TemplateManager` inlines the consolidated stylesheet into every report at render time. Snapshots regenerated with `--force-regen`; diffs are CSS-only, no HTML body changes. Full suite back to 554 passed / 5 skipped.

## [3.1.0] — 2026-05-03

A focused readability upgrade for PESTEL reports. The "Impact" subsection of each dimension is now classified into three side-by-side cards (Opportunités / Risques & Menaces / Recommandations) when the LLM emits the conventional French numbered-bold structure, with a graceful fallback to flat Markdown rendering when it doesn't. Sources collapse into a `<details>` block to recover vertical space.

### Added
- **Markdown rendering in renderers** (`base_renderer.py::render_markdown_block`): safe-by-default `MarkdownIt("commonmark", html=False)` parser, cached via `functools.lru_cache`. `render_text_section()` gains an opt-in `as_markdown=True` flag. Used by `PestelRenderer` for the executive summary, synthesis, and per-dimension impact bodies — bullet lists and emphasis now render as real HTML instead of escaped text.
- **PESTEL impact card classifier** (`pestel_renderer.py::_split_impact_into_buckets`): detects `N. **Title** :` headings at line start, classifies each by keyword (`opportun*` / `menace|risque` / `recommand*`), and emits `.opportunity-card` / `.threat-card` / `.recommendation-card` inside a `.cards-grid.impact-grid`. Falls back to flat Markdown when fewer than two buckets are detected or any heading fails to classify.
- **Collapsible PESTEL sources** (`pestel_renderer.py::_render_sources`): `<details class="sources-details">` wrapping the `<ul>`, with citation count in the `<summary>`. Inline URLs auto-linkified with `target="_blank" rel="noopener"`.
- **`markdown-it-py>=4.0.0`** runtime dependency.

### Changed
- **PESTEL CSS** (`templates/css/report.css`): new `.opportunity-card` / `.threat-card` / `.recommendation-card` classes share the existing card box model with semantic 4px left borders (green / red / blue). New `.pestel-report` scope tightens spacing, sets `h3` rhythm, narrows `.impact-grid` to `minmax(280px, 1fr)`, and styles the `.sources-details` wrapper.

### Security
- **XSS-safe Markdown rendering**: `MarkdownIt` is configured with `html=False`, so any raw `<script>` / inline HTML in LLM-emitted Markdown is escaped, not interpreted. Auto-linkified URLs in sources carry `rel="noopener"`.

## [3.0.0] — 2026-04-26

A modernization milestone that closes the door on accumulated infrastructure debt and re-aligns the repository with current industry conventions. No runtime API surface change; the major bump signals the operational reset (branch rename, working CI, secrets-free tests).

### Changed

- **Default branch renamed** `master` → `main`. All workflow triggers, README badges, and `mkdocs.yml::edit_uri` updated. Local clones must run `git branch -m master main && git fetch origin && git branch -u origin/main main`.
- **Dependency-installation step in CI** now runs `make dev` (full extras) instead of `make install`. After v2.2.0 moved pytest/pytest-cov/pytest-asyncio/etc. into `[project.optional-dependencies] test`, the production `make install` no longer installed the test runner.
- **`get_project_root()`** rewritten to be portable: `EPIC_NEWS_PROJECT_ROOT` env override → walk up from `__file__` for `pyproject.toml` → legacy `~/Projects/crews/epic_news` fallback. Drops the hardcoded path that broke CI (`/home/runner/work/epic_news/epic_news`).
- **Pre-commit hooks** point at `uv run <tool>` (ruff, yamllint, mypy) so they find their executables in `.venv` instead of failing with "command not found".
- **`make validate`** now runs lint + mypy + test (was lint + test). Matches CI exactly so failures surface locally before push.
- **`pestel_crew.py`** — added `# type: ignore[call-arg, arg-type]` markers on the 7 `Task()` constructors and the `Crew()` constructor so mypy stops complaining about CrewAI's `@CrewBase` decorator magic (description/expected_output are injected from YAML; `max_iter` is a runtime kwarg).

### Fixed

- **CI hadn't run automatically since July 2025** — the workflow trigger was `branches: [ main ]` while the repo was on `master`. Now consistent on `main`.
- **20 mypy errors** in `pestel_crew.py` that were never seen because CI was silent.
- **GitHub Actions versions bumped** to clear Node.js 20 deprecation warnings: `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v8.1.0` (pinned — no floating `v8` major tag), `codecov/codecov-action@v6`, `actions/upload-pages-artifact@v5`, `actions/deploy-pages@v5`, `actions/labeler@v6`, `docker/build-push-action@v7`, `docker/login-action@v4`, `docker/metadata-action@v6`, `docker/setup-buildx-action@v4`.
- **`uv.lock` version drift** that broke the four Dockerfile builds (lock recorded `epic-news==0.1.0` after the v2.1.0 bump).

### Security

- **Tests no longer require real API keys.** `pyproject.toml::[tool.pytest.ini_options].env` injects sentinel values for every credential at pytest startup (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `COMPOSIO_API_KEY`, `TAVILY_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, `ALPHAVANTAGE_API_KEY`, `COINMARKETCAP_API_KEY`, `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`, `MAIL`, `EPIC_ENABLE_EMAIL=false`). The CI `create env file` step that was passing real GitHub secrets into the test job is replaced with a stub `.env` containing only sentinels.

## [2.2.0] — 2026-04-26

### Added
- **Documentation site auto-published to GitHub Pages**: every push to `master` that touches `docs/`, `mkdocs.yml`, `README.md`, or `CHANGELOG.md` rebuilds the site at https://fjacquet.github.io/epic_news/ (Material theme, Diátaxis nav, light/dark toggle).
- **Per-category use case pages** in `docs/tutorials/use_cases/` (finance, news_research, business_intel, lifestyle) — each lists its crews, sample prompts, and outputs.
- **`docs/how-to/troubleshooting.md`** — diagnoses wrong crew classification, missing email, Composio Gmail connection issues, using the loguru/PostResult breadcrumbs added in v2.1.0.
- **`docs/reference/outputs.md`** — explains where Epic News writes HTML/JSON, what each loguru emoji line means, how PostResult fields map to delivery outcomes.

### Changed
- **README slimmed** from 341 → ~50 lines: title + badges + 30-second TL;DR + a small table linking into the docs (which is now the manual). New "Docs" badge points at the published site.
- **`docs/tutorials/user_guide.md`** rewritten as a 4-step landing page with a ToC pointing into the per-category use_case pages.
- **`docs/tutorials/index.md`** updated to surface the new pages.

### Removed
- **Standalone HTML dashboard pipeline**: deleted `src/epic_news/utils/dashboard_generator.py`, `templates/dashboard_template.html`, `templates/css/dashboard.css`, and `tests/utils/test_dashboard_generator.py`. The metrics-collecting `Dashboard` class in `epic_news.utils.observability` is unrelated and stays.

### Fixed
- **`uv.lock` version drift**: the v2.1.0 release bumped `pyproject.toml` to `2.1.0` but the lock still referenced `epic-news==0.1.0`, breaking `uv sync --locked` in all four Dockerfile builds. Refreshed.

### Security
- **litellm 1.83.0 advisories** (CVE-2025-65039 / Critical SQLi in proxy API key verification, CVE-2025-65033 / High RCE in MCP stdio test, CVE-2025-65034 / High SSTI in `/prompts/test`): not exploitable here — Epic News uses litellm only as the SDK called by CrewAI for completions; the litellm proxy server is never run. Constraint relaxed from `>=1.75.3` to `>=1.83.0` to track future fixed releases as they become resolvable against `crewai~=1.14.x`.

## [2.1.0] — 2026-04-26

### Added
- **Consolidated report stylesheet** (`templates/css/report.css`, ~1100 lines): single source of truth for all rendered HTML reports. Inlined at render time by `TemplateManager` so reports stay self-contained for email. Replaces the inline `<style>` blocks formerly scattered across 19 renderers + the universal template (#83).
- **Print-optimized typography** in `ui_theme.py`: Arial Nova Light (with system fallbacks) as `--font-family-base`, plus a `@media print` block that forces `html { font-size: 9pt }` and adds page-break protections on sections, tables, articles. Drastically reduces page count when printing reports (#83).
- **Theme CSS variables**: `--accent-color`, `--link-color`, `--text-muted`, `--subheader-color` for both light and dark themes (previously referenced by renderers without fallback). All renderer-specific styles now consume these vars (#83).
- **Email send observability** in `main.py::send_email`: payload log (recipient, subject, attachment, output_file) before kickoff, parsed `PostResult` log after kickoff (status, recipient, error_message). Replaces bare `print()` / stdlib `logging.getLogger` that bypassed the loguru sink (#84).
- **ADR-011**: Architecture Decision Record for the consolidated CSS source pattern.

### Changed
- **`PostCrew`** now uses loguru exclusively for tool-loading and fallback diagnostics, with explicit `🔧 Loading Gmail send tools from Composio...` and `✅ Loaded N Gmail send tools: [...]` traces (#84).
- **`generate_rss_weekly_html_report`** accepts both the canonical `RssWeeklyReport` shape and the legacy `RssFeeds` shape via runtime double-validation. Re-raises on validation failure instead of swallowing the exception (#85).
- **`generate_rss_weekly`** wraps the HTML generation step in `try/except` and only marks `state.output_file` on actual success — no more "✅ pipeline complete" lies when the HTML write failed (#85).
- **`send_email`** drops the attachment from `email_inputs` if the file does not exist on disk, so the email is sent body-only rather than wasting minutes in the Composio agent (#85).
- **`pyproject.toml`** runtime dependencies trimmed from 70 → 51 entries, organized into commented logical sections (core CrewAI, pydantic/data, HTTP/web, scraping, rendering, numerical/plotting). Dev/test tooling moved into `[project.optional-dependencies] test` and `[dependency-groups] dev` (#86).

### Fixed
- **RSS weekly HTML report** rendered an empty body (only title + summary) because `RssWeeklyRenderer` did not handle the canonical `feeds` top-level shape and used wrong article keys (`url`/`date`/`source` instead of `link`/`published`/`source_feed`). Now renders all articles across all feed digests with working links and parsed HTML summaries (#85).
- **Stdlib import shadowing risk**: removed `pathlib>=1.0.1` (deprecated Py2 backport) from runtime deps. Also removed `shutils`, `unicode`, `suppress` — declared but never imported, mostly Py2 fossils (#86).

### Removed
- Inline `<style>` blocks (~2200 lines of CSS) from 19 renderers — they now emit only semantic HTML with class names, the styling lives in `report.css` (#83).
- 4 unused/Py2-fossil packages: `pathlib`, `shutils`, `unicode`, `suppress` (#86).

## [Unreleased] — Epic News v2.0 Migration

### Added
- **ADR-001 through ADR-010**: Architecture Decision Records covering model selection, scoped memory, search migration, flow orchestration, HTML rendering, real-time retrieval, JSON standardization, Pydantic models, Composio integration, and UV package management
- **PRD-federated-html**: Product Requirements Document for CSS theme centralization
- **Federated HTML theme**: Single source of truth for CSS variables in `src/epic_news/config/ui_theme.py` with `generate_theme_css()` injected into templates at render time
- **Scoped memory**: Per-agent memory isolation via `LLMConfig.get_memory_config()` with `.scope()` — enabled for `fin_daily` and `meeting_prep` crews
- **Opt-in `reasoning_effort`**: Support for Magistral model reasoning via `LLM_REASONING_EFFORT` env var, passed through `model_kwargs`
- **CHANGELOG.md**: This file

### Changed
- **Default LLM**: Migrated from `openrouter/xiaomi/mimo-v2-flash:free` to `openrouter/mistralai/mistral-small-2603` (ADR-001)
- **Search provider**: Replaced `SerperDevTool` with `PerplexitySearchTool` as primary search across all crews (ADR-003)
- **Ruff config**: Added `fix = true` for automatic safe-fix application on lint
- **Template rendering**: `universal_report_template.html` now uses `{{ theme_css_vars }}` placeholder instead of hardcoded CSS variables

### Fixed
- **`CodeInterpreterTool` import**: Removed from `deep_research` crew (no longer exported by `crewai_tools`)
- **`langchain` import**: Replaced with `crewai.tools.BaseTool` in `data_centric_tools.py` (bare `langchain` not installed)

### Removed
- `SerperDevTool` as default search provider (kept as fallback in `HybridSearchTool` cascade)
- `CodeInterpreterTool` usage (replaced by built-in `allow_code_execution=True`)
- `langchain.tools.BaseTool` import (unnecessary — `crewai.tools.BaseTool` sufficient)
- **Scoped memory feature**: Removed `LLMConfig.get_memory_config()` and all `memory=` wiring from `fin_daily` and `meeting_prep` crews. CrewAI's default `Memory` hardcoded `llm='gpt-4o-mini'`, leaking an unused OpenAI dependency. The feature was opt-in and not productively used. ReceptionFlow's auto-spawned Flow memory is now overridden with our OpenRouter LLM and `read_only=True`. ADR-002 marked Superseded.

## [0.5] — 2025-08-11

### Added
- Pydantic output validation for all crews with parallel task execution
- Pydantic validators to handle LLM output variations
- OSINT specialized HTML renderers and consolidated report
- Comprehensive API keys reference documentation
- Documentation reorganized using Diataxis framework
- Mypy type checking in pre-commit and GitHub Actions
- Claude Code Review and PR Assistant GitHub workflows

### Changed
- OSINT crew: replaced `SerperDevTool` with `HybridSearchTool`, reduced agent count
- Python 3.13 upgrade with modern union syntax (`X | None`, `X | Y`)
- All mypy type errors resolved (zero errors achieved)
- Ruff UP047 fixes and code formatting applied
- Hierarchical CLAUDE.md files for better AI context

### Fixed
- `generate_osint` made async to work within CrewAI event loop

### Security
- Replaced MD5 with SHA-256 for event ID generation

## [0.4] — 2025-07-04

### Changed
- Consolidated HTML rendering through `TemplateManager`, removed legacy renderers
- JSON output standardization (PR-001), scraper consolidation (PR-002), rendering lint (PR-004)
- Added `workflow_dispatch` trigger to all Docker publish workflows

## [0.3] — 2025-07-04

### Added
- Combined Docker setup with supervisor for FastAPI and Streamlit
- Deep research crew with 4-agent architecture (strategist, collector, analyst, writer)
- PhD-level and ultra-comprehensive research flows
- Extractors package for structured crew output parsing
- Nutritional information requirement for menu generation

### Changed
- Imports reorganized to use `epic_news` namespace
- Removed unused and deprecated code in `src/` (Fixes #22)

## [0.2.2-alpha] — 2025-07-23

### Changed
- Docker and namespace improvements

## [0.2.1-alpha] — 2025-07-17

### Added
- Deep research flows with PhD-level academic research
- Extractors package for crew output parsing

## [0.2.0-alpha] — 2025-06-30

### Added
- Menu designer crew with structured HTML output and Pydantic models
- Menu plan validation and error recovery system
- Email sending with PostCrew and financial report integration
- Cross-reference report HTML generation
- Holiday planner HTML rendering system overhaul
- Company news renderer with comprehensive HTML tests
- Observability: tracing integration into core application flow
- Meeting prep crew output files
- Loguru logging (replaced standard `logging`)
- Advanced testing libraries (Faker, pytest-mock)
- Project-level TODO list for development planning

### Changed
- All crews refactored to comply with development guide (Two-Agent Pattern)
- Modular Pydantic models and structured outputs across all crews
- HTML rendering reorganized with new template system
- Documentation refactored and consolidated (Diataxis)
- Tests converted from `unittest.mock` to `pytest-mock`

### Removed
- `MarketingWritersCrew` and all associated code

## [0.1.2-alpha] — 2025-06-22

### Changed
- CI/CD improvements for GitHub Actions

## [0.1.1-alpha] — 2025-06-22

### Added
- New services and `.env` file creation
- Simplification and cleanup

## [0.1.0-alpha] — 2025-06-22

### Added
- Initial release with CrewAI-based multi-agent architecture
- ReceptionFlow orchestration pattern with crew dispatch
- 24+ specialized crews (financial, news, research, planning, content)
- HTML report generation with dark mode support
- OpenRouter LLM integration via `LLMConfig`
- Tool ecosystem (70+ tools: search, finance, scraping, RAG)
- Composio integration for external services (Gmail, Slack, Reddit)
- MCP server support (Wikipedia)
- FastAPI and Streamlit interfaces
- Docker deployment support
- pytest test suite with structure and rendering tests
