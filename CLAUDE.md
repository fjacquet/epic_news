# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Commands

### Package Management (ALWAYS use `uv`)

```bash
uv sync && uv pip install -e .   # Install deps + editable install (required)
uv add package-name              # Add a package
uv remove package-name           # Remove a package
```

**NEVER** use `pip`, `poetry`, or other package managers. This project exclusively uses `uv`.

### Running the Application

```bash
crewai flow kickoff    # or: make run-crew
```

**NEVER** run crews directly via Python. The CrewAI Flow command is the only supported execution method.

**Debugging kickoff failures**: `crewai flow kickoff` runs `uv run kickoff` in a subprocess and masks any crew crash behind a generic `Command '['uv', 'run', 'kickoff']' returned non-zero exit status 1`. The real traceback is printed by the subprocess *above* that line.

### Testing

```bash
uv run pytest                           # Run all tests (or: make test)
uv run pytest tests/path/to/test_file.py  # Run specific test
uv run pytest -q                        # Quick mode
uv run pytest -v                        # Verbose (or: make test-verbose)
```

### Linting, Formatting, and Type Checking

```bash
uv run ruff check --fix .     # Auto-fix lint issues (or: make lint)
uv run ruff format .          # Format code (or: make format)
uv run yamllint -s .          # YAML validation
uv run yamlfix src            # YAML formatting
uv run mypy src/epic_news     # Type checking (or: make type-check)
make fix                      # Format + lint in one shot
make validate                 # lint + test
```

### Pre-commit Hooks

Hooks run automatically on commit: ruff lint, ruff format, yamllint, mypy. Run manually:

```bash
uv run pre-commit run --all-files   # or: make pre-commit
```

### Security Checks

```bash
make security    # Runs bandit (code) + safety (deps)
```

### Useful Makefile Targets

Run `make help` to see all targets. Key ones: `install`, `dev`, `test`, `lint`, `format`, `fix`, `validate`, `coverage`, `security`, `type-check`, `clean`, `run-crew`, `run-streamlit`, `run-api`, `docker-build-all`.

## Architecture Overview

### ReceptionFlow Pattern

The application uses a **single flow orchestration** pattern (`src/epic_news/main.py`):

1. **ReceptionFlow** is the main entry point with ~25 `generate_*` methods
2. Each method corresponds to a specialized crew (e.g., `generate_poem` → `PoemCrew`)
3. Flow methods call `.kickoff(inputs=crew_inputs)` and handle the result
4. User requests are classified and routed to the appropriate crew method

**Key insight**: All crew execution happens through ReceptionFlow methods, never directly.

### Crew Implementation Pattern

Each crew follows: `crew_name/{config/agents.yaml, config/tasks.yaml, crew_name_crew.py}` with `@CrewBase`, `@agent`, `@task`, `@crew` decorators. See `src/epic_news/crews/CLAUDE.md` for full code examples.

**CRITICAL**: Assign tools in `@agent` methods, not in `agents.yaml`. CrewBase resolves a YAML `tools:` entry only by name against `@tool`-decorated methods on the crew class; any other name raises `KeyError`. Keeping tools in Python is the project rule.

### Pydantic Models

Use Python 3.13 union syntax (`X | None`, `X | Y`) for all new code. Ruff auto-upgrades via UP007/UP035/UP045.

### HTML Report Generation: Two-Agent Pattern

Separate research (has tools, no `output_file`) from reporting (NO tools, has `output_file`). `output_pydantic` already keeps action traces out of the structured output; the split is kept so the reporting step runs tool-free. See `src/epic_news/crews/CLAUDE.md` for code examples.

### HTML Rendering Architecture

Pipeline: Crew result → Pydantic model (`load_or_parse_model`) → `render_and_write_html()` → `TemplateManager().render_report(selected_crew=..., content_data=...)` → `RendererFactory` → `BaseRenderer` subclass. `emit_report()` chooses HTML or DOCX.

See `src/epic_news/utils/CLAUDE.md` for full rendering system docs.

**Renderer rules**: `BaseRenderer` subclasses must implement `__init__` (even if empty), use `tag.attrs["class"] = [...]` (NOT `class_="..."`), use CSS variables with fallbacks, handle empty states.

### Federated HTML Theme

CSS theme variables are defined in `src/epic_news/config/ui_theme.py` (single source of truth). The template uses a `{{ theme_css_vars }}` placeholder injected by `TemplateManager` at render time. To change colors/typography, edit `ui_theme.py` — all reports update automatically.

### Information Retrieval: Real-Time, Not RAG

The project uses **real-time data fetching** instead of traditional RAG:

- **Rationale**: Financial markets change constantly; vector databases would be stale
- **Approach**: Agents use live tools (Perplexity, Tavily, YahooFinance, etc.) for every execution

### Tool Output Standardization

All tool `_run()` methods must return **JSON strings** parseable by `json.loads()`. Use helpers from `src/epic_news/tools/_json_utils.py` for standardization.

### Path Management

- All file paths must be **project-relative**, managed programmatically
- Directory creation is centralized via `ensure_output_directories()` (called at startup)
- **Never** use `os.makedirs()` in crew/task logic

## LLM Configuration

All config via `LLMConfig` (`src/epic_news/config/llm_config.py`). Default model: Gemini 3.8 Flash on LiteLLM's native route (`gemini/gemini-3.8-flash`, ADR-016); any `openrouter/...` model goes through OpenRouter. The method keeps its historical name `get_openrouter_llm()` for both routes.

- `LLMConfig.get_openrouter_llm(task_type="quick"|"default"|"long")` — LLM instance with the matching timeout (120s / 300s / 600s, from `LLMConfig.get_timeout()`) set on the LLM itself; supports opt-in `reasoning_effort` (Magistral). Gemini models get no default temperature (LiteLLM keeps 1.0); Gemini 3 reasoning defaults to `medium`
- `LLMConfig.get_max_iter()` — pass as `max_iter=` on each `Agent` (default 15; fin_daily's stock analyst uses 30). CrewAI `Crew` has no `max_iter` field
- `LLMConfig.get_max_rpm()` — `max_rpm=` on the `Crew` (default 20)

**Timeouts**: always `llm=LLMConfig.get_openrouter_llm(task_type=...)`. Never pass `llm_timeout=` to an `Agent`/`Crew`/`Task`: it is not a CrewAI field and is silently ignored (the call then uses LiteLLM's 600s default). Don't wire tasks with `agent.copy()`: CrewAI's `LLM.__copy__` drops `timeout`.

`tests/crews/test_constructor_kwargs.py` (AST scan) fails on any `Agent`/`Task`/`Crew` kwarg that is not a declared field, and `tests/crews/test_agent_settings_contract.py` checks every built agent has an LLM timeout and the configured `max_iter` (ADR-014).

### Environment Variables

Key `.env` settings: `MODEL` (default: `gemini/gemini-3.8-flash`), `GEMINI_API_KEY` (native Gemini route; LiteLLM reads `GOOGLE_API_KEY` first if both are set), `OPENROUTER_API_KEY` / `OPENROUTER_BASE_URL` (for `openrouter/...` models), `LLM_TEMPERATURE` (0.7, not sent to Gemini), `LLM_TIMEOUT_QUICK/DEFAULT/LONG` (120/300/600), `LLM_REASONING_EFFORT` (unset → `medium` for Gemini 3, none otherwise), `CREW_MAX_ITER` (15), `CREW_MAX_RPM` (20), `LLM_MAX_CONCURRENCY` (3, process-wide cap on simultaneous LLM calls), `CREW_KICKOFF_ATTEMPTS` (1), `SCRAPE_MAX_CHARS` (12000), `DOCX_FRAGMENT_CONCURRENCY` (3), `MENU_RECIPE_CONCURRENCY` (3). Change `MODEL` in `.env` to switch models globally.

**NEVER** hardcode model names or timeout values — always use `LLMConfig` methods.

## MCP Servers

Wikipedia MCP (`wikipedia-mcp-server`, locked in `uv.lock` and run from the venv's `wikipedia-mcp` script, never fetched at runtime) configured in `src/epic_news/config/mcp_config.py` via `MCPConfig.get_wikipedia_mcp()`. Used by: `deep_research`, `pestel`.

Wire MCP servers through CrewBase:

- set `mcp_server_params = MCPConfig.get_wikipedia_mcp()` on the crew class;
- in `@agent` methods use `*get_mcp_tools_or_empty(self)` (wraps `get_mcp_tools()`; a server that cannot start logs a warning, the crew runs without its tools, and the failed start is not retried by the other agents);
- CrewBase stops the adapter only after a *successful* kickoff, so the flow calls `close_mcp(crew)` in a `finally` around `kickoff_flow(...)`.

Do not hand-build a `MCPServerAdapter` (it spawns a subprocess that leaks if never stopped).

## Composio Tools

Composio 1.0 integration via `ComposioConfig` (`src/epic_news/config/composio_config.py`):

- `get_search_tools()` — Reddit, Twitter, HackerNews search tools (used by: `company_news`)
- `get_gmail_email_tools()` — Gmail toolkit for agents (currently unused)

Report emails are sent deterministically by `epic_news.utils.email_sender.send_report_email()`, which calls Composio `GMAIL_SEND_EMAIL` directly (no agent). Requires `COMPOSIO_API_KEY` in `.env`.

Not to be confused with `epic_news.tools.web_tools.get_search_tools()` (`PerplexitySearchTool`), which most crews use.

## API

`src/epic_news/api.py` (FastAPI, `make run-api`) exposes `GET /health` (open) and `POST /kickoff`. Settings:

- `EPIC_API_TOKEN` — `/kickoff` requires `Authorization: Bearer <token>`; unset → 503 (fails closed), wrong token → 401
- `EPIC_API_BIND` — host address Docker Compose publishes port 8000 on (default `127.0.0.1`)
- `EPIC_API_MAX_CONCURRENT` — concurrent kickoffs (default 1); extra requests get 429

`user_request` is capped at 2000 characters. See `docs/how-to/expose-api-n8n.md` and ADR-012.

## File Access Boundary

Agent-driven code reads and writes only under `output/` (ADR-015): `render_and_write_html()` refuses paths outside it, DOCX images are limited to it, and agents that need to read files get `OutputFileReadTool` (`src/epic_news/tools/output_file_read_tool.py`, `root="output"` by default; fin_daily reads portfolio CSVs with `root="data"`). Never give crewai's unscoped `FileReadTool` to an agent that also has web search/scrape tools.

## Code Style Specifics

### Imports

ALL imports must be at the top of files, never inside functions or methods.

### Whitespace

- No trailing whitespace (W291)
- No whitespace on blank lines (W293)
- Enforced by pre-commit hooks

### Logging

Use Loguru, not standard `logging`:

```python
from loguru import logger

logger.info("Message")
logger.error("Error message")
```

Configuration in `src/epic_news/utils/logger.py`.

## Common Pitfalls

1. **Using `pip` instead of `uv`** → Always use `uv`
2. **Running crews directly** → Always use `crewai flow kickoff`
3. **Tools in YAML files** → Assign tools in Python code (YAML names only resolve against `@tool` methods, else `KeyError`)
4. **Legacy Union syntax in new code** → Use modern `X | Y` and `X | None` (Python 3.13+)
5. **Single-agent HTML reports** → Use two-agent pattern (researcher + reporter)
6. **Constructor injection for context** → Use `.kickoff(inputs=crew_inputs)`
7. **Using `os.makedirs()` in crews** → Use centralized `ensure_output_directories()`
8. **Hardcoded LLM configuration** → Always use `LLMConfig.get_openrouter_llm(task_type=...)`, `LLMConfig.get_max_iter()`, etc.
9. **Hardcoded model names** → Use `MODEL` from `.env` via `LLMConfig`, never `llm="gpt-4o-mini"`
10. **Enabling CrewAI `Memory`/RAG** → Project uses real-time retrieval, not memory; never pass `memory=Memory(...)` to a `Flow`/`Crew` (a LanceDB store with no embedder crashes kickoff)
11. **Unknown kwargs on CrewAI objects** → CrewAI silently drops unknown keyword arguments (`llm_timeout=`, `Crew(max_iter=...)`). Don't hide call-arg errors with `# type: ignore`; check the field exists (`"x" in Agent.model_fields`)

## Python Version

This project requires **Python 3.13** (`requires-python = ">=3.13,<3.14"`). The `.python-version` file is set to `3.13`.

## Development Workflow

1. Setup: `make dev` (or `uv sync && uv pip install -e .`)
2. Make changes
3. Test: `make test` (or `uv run pytest`)
4. Fix: `make fix` (format + lint)
5. Validate: `make validate` (lint + test)
6. End-to-end: `make run-crew` (or `crewai flow kickoff`)
7. Commit (pre-commit hooks: ruff lint, ruff format, yamllint, mypy)

## Key Documentation

- `docs/how-to/development_setup.md`: Development setup and workflow
- `docs/explanations/architecture.md`: Architecture and patterns
- `docs/adr/`: Architecture decision records
- `docs/reference/tools.md`: Available tools and their usage
- `README.md`: User-facing documentation and use cases

## Subdirectory CLAUDE.md Files

More detailed context exists in subdirectory CLAUDE.md files:

- `src/epic_news/crews/CLAUDE.md`: Crew implementation patterns
- `src/epic_news/tools/CLAUDE.md`: Tool development guide
- `src/epic_news/utils/CLAUDE.md`: Utility modules and HTML rendering system

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:

```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)

```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)

```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)

```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)

```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)

```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)

```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)

```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)

```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)

```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands

```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->