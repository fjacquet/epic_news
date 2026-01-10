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
