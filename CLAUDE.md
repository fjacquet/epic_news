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

**CRITICAL**: Tools must be assigned in `@agent` methods, NEVER in `agents.yaml` (causes `KeyError`).

### Pydantic Models

Use Python 3.13 union syntax (`X | None`, `X | Y`) for all new code. Ruff auto-upgrades via UP007/UP035/UP045.

### HTML Report Generation: Two-Agent Pattern

Separate research (has tools, no `output_file`) from reporting (NO tools, has `output_file`) to avoid action traces in output. See `src/epic_news/crews/CLAUDE.md` for code examples.

### HTML Rendering Architecture

Pipeline: Crew result → Pydantic model → `*_to_html()` factory → `TemplateManager.render_report()` → `BaseRenderer` subclass.

See `src/epic_news/utils/CLAUDE.md` for full rendering system docs.

**Renderer rules**: `BaseRenderer` subclasses must implement `__init__` (even if empty), use `tag.attrs["class"] = [...]` (NOT `class_="..."`), use CSS variables with fallbacks, handle empty states.

### Federated HTML Theme

CSS theme variables are defined in `src/epic_news/config/ui_theme.py` (single source of truth). The template uses a `{{ theme_css_vars }}` placeholder injected by `TemplateManager` at render time. To change colors/typography, edit `ui_theme.py` — all reports update automatically.

### Information Retrieval: Real-Time, Not RAG

The project uses **real-time data fetching** instead of traditional RAG:

- **Rationale**: Financial markets change constantly; vector databases would be stale
- **Approach**: Agents use live tools (Perplexity, Tavily, YahooFinance, etc.) for every execution
- **SaveToRagTool**: Used as a short-term scratchpad within a single crew execution, not permanent storage

### Tool Output Standardization

All tool `_run()` methods must return **JSON strings** parseable by `json.loads()`. Use helpers from `src/epic_news/tools/_json_utils.py` for standardization.

### Path Management

- All file paths must be **project-relative**, managed programmatically
- Directory creation is centralized via `ensure_output_directories()` (called at startup)
- **Never** use `os.makedirs()` in crew/task logic

## LLM Configuration - OpenRouter

All config via `LLMConfig` (`src/epic_news/config/llm_config.py`):

- `LLMConfig.get_openrouter_llm()` — LLM instance (supports opt-in `reasoning_effort` for Magistral models)
- `LLMConfig.get_timeout("quick"|"default"|"long")` — 120s / 300s / 600s
- `LLMConfig.get_max_iter()` / `LLMConfig.get_max_rpm()` — crew limits (default: 5 / 20)

### Environment Variables

Key `.env` settings: `OPENROUTER_API_KEY`, `MODEL` (default: `openrouter/mistralai/mistral-small-2603`), `OPENROUTER_BASE_URL`, `LLM_TEMPERATURE` (0.7), `LLM_TIMEOUT_QUICK/DEFAULT/LONG`, `LLM_REASONING_EFFORT` (opt-in, for Magistral models), `CREW_MAX_ITER`, `CREW_MAX_RPM`. Change `MODEL` in `.env` to switch models globally.

**NEVER** hardcode model names or timeout values — always use `LLMConfig` methods.

## MCP Servers

Wikipedia MCP (`wikipedia-mcp-server`) configured in `src/epic_news/config/mcp_config.py` via `get_wikipedia_mcp()`. Used by: `deep_research`, `library`, `holiday_planner`. MCP tools are transparent to crews.

## Composio Tools

Composio 1.0 integration via `ComposioConfig` (`src/epic_news/config/composio_config.py`):

- `get_search_tools()` — Reddit, Twitter, HackerNews (used by: `company_news`, `news_daily`)
- `get_communication_tools()` — Gmail, Slack, Discord, Notion (used by: `post`)
- `get_financial_tools()` — CoinMarketCap (used by: `fin_daily`)
- `get_content_creation_tools()` — Canva, Airtable

**Note**: Gmail uses `CREATE_EMAIL_DRAFT` (not deprecated `GMAIL_SEND_EMAIL`). Requires `COMPOSIO_API_KEY` in `.env`.

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
3. **Tools in YAML files** → Tools must be assigned in Python code
4. **Legacy Union syntax in new code** → Use modern `X | Y` and `X | None` (Python 3.13+)
5. **Single-agent HTML reports** → Use two-agent pattern (researcher + reporter)
6. **Constructor injection for context** → Use `.kickoff(inputs=crew_inputs)`
7. **Using `os.makedirs()` in crews** → Use centralized `ensure_output_directories()`
8. **Hardcoded LLM configuration** → Always use `LLMConfig.get_openrouter_llm()`, `LLMConfig.get_timeout()`, etc.
9. **Hardcoded model names** → Use `MODEL` from `.env` via `LLMConfig`, never `llm="gpt-4o-mini"`

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

- `docs/1_DEVELOPMENT_GUIDE.md`: Comprehensive development guide
- `docs/3_ARCHITECTURAL_PATTERNS.md`: Detailed architectural patterns
- `docs/2_TOOLS_HANDBOOK.md`: All available tools and their usage
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