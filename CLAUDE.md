# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Commands

### Package Management (ALWAYS use `uv`)
```bash
# Install dependencies
uv sync
uv pip install -e .  # Editable install (required to prevent ModuleNotFoundError)

# Add/remove packages
uv add package-name
uv remove package-name
```

**NEVER** use `pip`, `poetry`, or other package managers. This project exclusively uses `uv`.

### Running the Application
```bash
# ALWAYS use this command to run crews
crewai flow kickoff
```

**NEVER** run crews directly via Python (`python -m src.epic_news.crews...` or `python src/epic_news/main.py`). The CrewAI Flow command is the only supported execution method.

### Testing
```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/path/to/test_file.py

# Quick mode
uv run pytest -q
```

### Linting and Formatting
```bash
# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# YAML validation and formatting
uv run yamllint -s .
uv run yamlfix src
```

## Architecture Overview

### ReceptionFlow Pattern

The application uses a **single flow orchestration** pattern (`src/epic_news/main.py`):

1. **ReceptionFlow** is the main entry point with ~25 `generate_*` methods
2. Each method corresponds to a specialized crew (e.g., `generate_poem` → `PoemCrew`)
3. Flow methods call `.kickoff(inputs=crew_inputs)` and handle the result
4. User requests are classified and routed to the appropriate crew method

**Key insight**: All crew execution happens through ReceptionFlow methods, never directly.

### Crew Implementation Pattern

Each crew follows a standard structure:

```
crew_name/
├── config/
│   ├── agents.yaml      # Agent definitions (role, goal, backstory)
│   └── tasks.yaml       # Task definitions
└── crew_name_crew.py    # Python implementation
```

**Python crew class**:
```python
@CrewBase
class MyCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    @agent
    def agent_name(self) -> Agent:
        return Agent(
            config=self.agents_config["agent_name"],
            tools=self.my_tools,  # Tools MUST be assigned here, NOT in YAML
            verbose=True,
        )
    
    @task
    def task_name(self) -> Task:
        return Task(
            config=self.tasks_config["task_name"],
            agent=self.agent_name(),
            output_pydantic=MyPydanticModel,  # Structured output
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

**CRITICAL**: Tools must be assigned programmatically in the `@agent` method, never in `agents.yaml`. Hybrid YAML/code tool configuration causes `KeyError` exceptions.

### Pydantic Models: Legacy Union Syntax Required

CrewAI's internal schema parser **cannot handle** Python 3.10+ Union syntax (`X | Y`).

```python
from typing import Union, Optional

# ✅ CORRECT - Works with CrewAI
field: Optional[str] = None
field: Union[str, int] = "default"

# ❌ WRONG - Causes AttributeError
field: str | None = None
field: str | int = "default"
```

**All Pydantic models** used with CrewAI must use legacy `Union` and `Optional` syntax. This is enforced project-wide and disabled in ruff config (UP007, UP035, UP045).

### HTML Report Generation: Two-Agent Pattern

**Problem**: Agents with tools write action traces to output files instead of final content.

**Solution**: Separate research from reporting:

1. **Research Agent(s)**: Have tools, no `output_file`, pass data via context
2. **Reporting Agent**: NO tools, has `output_file`, generates clean HTML

```python
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=[WikipediaTool(), SearchTool()],  # Has tools
        # No output_file
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # NO TOOLS = No action traces
        output_file="output/report.html",
    )
```

### HTML Rendering Architecture

The project uses a **deterministic Python rendering** pattern for structured outputs:

1. **TemplateManager** (`src/epic_news/utils/html/template_manager.py`): Central rendering coordinator
2. **Crew-specific renderers** (`src/epic_news/utils/html/template_renderers/`): Extend `BaseRenderer`
3. **Factory functions**: Each crew has a `*_to_html()` function (e.g., `poem_to_html()`)

**Pattern**:
```python
# 1. Execute crew
result = MyCrew().crew().kickoff(inputs=crew_inputs)

# 2. Parse to Pydantic model
model = MyModel.model_validate(json.loads(result.raw))

# 3. Render via factory
my_crew_to_html(model, html_file="output/my_crew/report.html")
```

**Factory delegates to TemplateManager**:
```python
def my_crew_to_html(model: MyModel, html_file: str):
    TemplateManager.render_report(
        crew_identifier="my_crew",
        data=model.model_dump(),
        output_path=html_file,
    )
```

**Important renderer notes**:
- All `BaseRenderer` subclasses **must implement `__init__`** (even if empty)
- Use `tag.attrs["class"] = [...]` for CSS classes, NOT `class_="..."`
- Use CSS variables with fallbacks: `color: var(--text-color, #343a40);`
- Handle empty states gracefully

### Information Retrieval: Real-Time, Not RAG

The project uses **real-time data fetching** instead of traditional RAG:

- **Rationale**: Financial markets change constantly; vector databases would be stale
- **Approach**: Agents use live tools (SerperDev, Tavily, YahooFinance, etc.) for every execution
- **SaveToRagTool**: Used as a short-term scratchpad within a single crew execution, not permanent storage

### Tool Output Standardization

All tool `_run()` methods must return **JSON strings** parseable by `json.loads()`. Use helpers from `src/epic_news/tools/_json_utils.py` for standardization.

### Path Management

- All file paths must be **project-relative**, managed programmatically
- Directory creation is centralized via `ensure_output_directories()` (called at startup)
- **Never** use `os.makedirs()` in crew/task logic

## LLM Configuration - OpenRouter

This project uses **OpenRouter** as the primary LLM provider for cost efficiency and model flexibility.

### Centralized Configuration

All LLM configuration is managed through `LLMConfig` (`src/epic_news/config/llm_config.py`):

```python
from epic_news.config.llm_config import LLMConfig

# Get OpenRouter LLM instance
llm = LLMConfig.get_openrouter_llm()

# Get timeouts by task type
llm_timeout = LLMConfig.get_timeout("quick")    # 120s
llm_timeout = LLMConfig.get_timeout("default")  # 300s
llm_timeout = LLMConfig.get_timeout("long")     # 600s

# Get crew configuration
max_iter = LLMConfig.get_max_iter()  # default: 5
max_rpm = LLMConfig.get_max_rpm()    # default: 20
```

### Environment Variables

Configure in `.env`:
```bash
# OpenRouter Configuration (PRIMARY LLM PROVIDER)
OPENROUTER_API_KEY=your_openrouter_api_key_here
MODEL=openrouter/xiaomi/mimo-v2-flash:free  # Default model
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# LLM Parameters
LLM_TEMPERATURE=0.7                          # 0.0-2.0: Lower=deterministic, Higher=creative
LLM_MAX_TOKENS=                              # Leave empty for no limit

# Timeout Configuration (seconds)
LLM_TIMEOUT_QUICK=120                        # Quick tasks (cooking, classification)
LLM_TIMEOUT_DEFAULT=300                      # Standard tasks (research, analysis)
LLM_TIMEOUT_LONG=600                         # Complex tasks (deep research, reports)

# Crew Configuration
CREW_MAX_ITER=5                              # Max iterations per crew
CREW_MAX_RPM=20                              # Max requests per minute
```

### Switching Models

To change models globally, update `.env`:
```bash
MODEL=openrouter/anthropic/claude-3.5-sonnet
```
All crews will use the new model on next run.

### Agent Configuration Pattern

**ALWAYS** use `LLMConfig` methods in agent/crew definitions:

```python
from epic_news.config.llm_config import LLMConfig

@agent
def my_agent(self) -> Agent:
    return Agent(
        config=self.agents_config["my_agent"],
        llm=LLMConfig.get_openrouter_llm(),  # ✅ CORRECT
        llm_timeout=LLMConfig.get_timeout("default"),  # ✅ CORRECT
        verbose=True,
    )

@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        llm_timeout=LLMConfig.get_timeout("default"),  # ✅ CORRECT
        max_iter=LLMConfig.get_max_iter(),              # ✅ CORRECT
        max_rpm=LLMConfig.get_max_rpm(),                # ✅ CORRECT
        verbose=True,
    )
```

**NEVER** hardcode model names or timeout values:
```python
# ❌ WRONG - Hardcoded values
llm="gpt-4o-mini"
llm_timeout=300
max_iter=5
```

## MCP Servers

The project uses MCP (Model Context Protocol) servers for advanced tool integration.

### Available MCP Servers

1. **Wikipedia MCP** (`wikipedia-mcp-server`): Maintained Wikipedia integration
   - `search`: Search Wikipedia with language support
   - `fetch`: Fetch page content by ID

### Configuration

MCP servers are configured in `src/epic_news/config/mcp_config.py`:

```python
from epic_news.config.mcp_config import get_wikipedia_mcp

# Get Wikipedia MCP server
wikipedia_server = get_wikipedia_mcp()
```

### Usage in Crews

MCP servers are automatically available to crews that need them. The Wikipedia MCP server is primarily used by:
- `deep_research` crew (encyclopedic research)
- `library` crew (book context)
- `holiday_planner` crew (destination information)

**Note**: MCP integration is transparent - crews access MCP tools like any other tool.

## Composio Tools

The project integrates **Composio 1.0** with 176 tools across 10 toolkits for comprehensive external service integration.

### Available Toolkits

1. **Social Platform Search**: Reddit, Twitter, HackerNews
2. **Communication**: Gmail, Slack, Discord, Notion
3. **Financial Data**: CoinMarketCap
4. **Content Creation**: Canva, Airtable

### Configuration

All Composio tools are managed through `ComposioConfig` (`src/epic_news/config/composio_config.py`):

```python
from epic_news.config.composio_config import ComposioConfig

composio = ComposioConfig()

# Get tool categories
search_tools = composio.get_search_tools()           # Reddit, Twitter, HackerNews
comm_tools = composio.get_communication_tools()      # Gmail, Slack, Discord, Notion
financial_tools = composio.get_financial_tools()     # CoinMarketCap
content_tools = composio.get_content_creation_tools()  # Canva, Airtable
```

### Tool Categories

**Search Tools** (5 tools):
- `REDDIT_GET_POSTS`: Aggregate Reddit discussions
- `TWITTER_SEARCH`: Real-time social media trends
- `HACKERNEWS_GET_STORIES`: Tech news aggregation

**Communication Tools** (Gmail, Slack, Discord, Notion):
- Email sending, Slack messaging, Discord notifications
- Note: Gmail in Composio 1.0 uses `CREATE_EMAIL_DRAFT` instead of deprecated `GMAIL_SEND_EMAIL`

**Financial Tools**:
- `COINMARKETCAP_GET_LISTINGS`: Cryptocurrency market data

**Content Creation**:
- Canva design integration
- Airtable data management

### Usage Pattern

```python
from epic_news.config.composio_config import ComposioConfig

def __init__(self):
    composio = ComposioConfig()
    self.search_tools = composio.get_search_tools()

@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=self.search_tools,  # Reddit, Twitter, HackerNews
        verbose=True,
    )
```

### Environment Variables

Required API keys in `.env`:
```bash
# Composio Configuration
COMPOSIO_API_KEY=your_composio_api_key

# Optional: Individual service keys if using direct integrations
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_API_KEY=your_twitter_api_key
```

### Crew-Specific Tool Assignment

Different crews use different Composio tool categories:
- **News crews** (`company_news`, `news_daily`): Search tools (Reddit, Twitter, HackerNews)
- **Financial crews** (`fin_daily`): Financial tools (CoinMarketCap)
- **Communication crews** (`post`): Communication tools (Gmail, Slack)

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
4. **Python 3.10+ Union syntax in Pydantic** → Use `Union[X, Y]` and `Optional[X]`
5. **Single-agent HTML reports** → Use two-agent pattern (researcher + reporter)
6. **Constructor injection for context** → Use `.kickoff(inputs=crew_inputs)`
7. **Using `os.makedirs()` in crews** → Use centralized `ensure_output_directories()`
8. **Hardcoded LLM configuration** → Always use `LLMConfig.get_openrouter_llm()`, `LLMConfig.get_timeout()`, etc.
9. **Hardcoded model names** → Use `MODEL` from `.env` via `LLMConfig`, never `llm="gpt-4o-mini"`

## Development Workflow

1. Setup: `uv sync && uv pip install -e .`
2. Make changes
3. Test: `uv run pytest`
4. Lint: `uv run ruff check --fix`
5. Validate: `crewai flow kickoff` (end-to-end)
6. Commit (pre-commit hooks run automatically)

## Key Documentation

- `docs/1_DEVELOPMENT_GUIDE.md`: Comprehensive development guide
- `docs/3_ARCHITECTURAL_PATTERNS.md`: Detailed architectural patterns
- `docs/2_TOOLS_HANDBOOK.md`: All available tools and their usage
- `README.md`: User-facing documentation and use cases
