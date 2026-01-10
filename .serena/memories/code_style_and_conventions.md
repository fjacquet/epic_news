# Code Style and Conventions

## Python Version
- **Required**: Python >=3.10, <3.13
- **Target**: Python 3.10 (as specified in ruff config)

## Code Formatting (Ruff)

### Line Length
- **Maximum**: 110 characters
- Enforced by ruff formatter

### Import Organization
- **ALL imports MUST be at the top of the file**
- Never place imports inside functions or methods
- Follow PEP 8 import ordering
- Use isort integration (via ruff)
- Known first-party: `epic_news`

### String Quotes
- **Double quotes**: `"string"` (enforced by ruff)

### Indentation
- **Spaces**: 4 spaces per indentation level
- **Never use tabs**

### Line Endings
- **Auto-detection**: Let ruff handle line endings

### Whitespace Rules
- **No trailing whitespace** (W291) - strictly enforced
- **No whitespace on blank lines** (W293) - strictly enforced
- These are caught by pre-commit hooks

## Type Hints and Annotations

### CRITICAL: CrewAI Pydantic Compatibility
**ALWAYS use legacy Union syntax for Pydantic models**:

```python
from typing import Union, Optional

# ✅ CORRECT - Compatible with CrewAI
field: Optional[str] = None
field: Union[str, int] = "default"
field: Union[str, None] = None

# ❌ WRONG - Causes AttributeError in CrewAI
field: str | None = None
field: str | int = "default"
```

**Rationale**: CrewAI's PydanticSchemaParser cannot handle Python 3.10+ Union syntax (`X | Y`).

### General Type Hints
- Use type hints for all function parameters and return values
- Leverage Pydantic models for data validation
- Use `List`, `Dict`, `Tuple` from `typing` module

## Naming Conventions

### Functions and Variables
- **snake_case**: `my_function()`, `variable_name`
- Be descriptive: `calculate_total_price()` not `calc()`

### Classes
- **PascalCase**: `MyClass`, `FinancialReport`, `SaintData`
- Pydantic models follow the same convention

### Constants
- **UPPER_SNAKE_CASE**: `MAX_RETRIES`, `API_TIMEOUT`

### Private Members
- **Single underscore prefix**: `_internal_method()`, `_helper_function()`

### Crew Names
- **PascalCase with "Crew" suffix**: `FinDailyCrew`, `NewsDailyCrew`

## Documentation

### Docstrings
- Use triple double-quotes: `"""Docstring"""`
- Add docstrings for public functions and classes
- Keep them concise and meaningful
- Don't add docstrings to code you didn't change (avoid over-engineering)

### Comments
- Use comments sparingly
- Only add comments where logic isn't self-evident
- Avoid obvious comments like `# increment counter`

## Logging

### Use Loguru
```python
from loguru import logger

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Configuration
- Logging configured in `src/epic_news/utils/logger.py`
- Logs to console and file in `logs/` directory
- Setup via `setup_logging()` called in `main.py`

## Pydantic Models

### Field Annotations
- Always use legacy Union syntax (see above)
- Provide default values where appropriate
- Use field validators for custom validation

### Model Design
- **Model the data you have**, not idealized structures
- Prefer simpler, flatter structures over deeply nested ones
- Use descriptive field names

### Data Normalization
When working with external data:
1. Map alternative field names to expected schema
2. Handle multilingual keys (e.g., French → English)
3. Convert structures as needed
4. Provide sensible defaults for missing fields

## Error Handling

### Fail Fast
- Validate inputs early
- Provide clear, actionable error messages
- Use Pydantic validation for data integrity

### HTTP Resilience
- Use tenacity for retry logic on 5xx errors
- Don't retry on 4xx client errors
- Implement proper timeout handling

## File and Path Management

### Path Handling
- All paths must be **project-relative**
- Manage paths programmatically
- Avoid hard-coded absolute paths

### Directory Creation
- Use centralized `ensure_output_directories()` at startup
- **Never** use `os.makedirs()` in crew/task logic

## Tool Development

### Tool Assignment
- **NEVER** specify tools in YAML files
- **ALWAYS** assign tools programmatically in code
- Use centralized factory functions

```python
# ✅ CORRECT
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=self.search_tools,  # Assigned in code
        verbose=True,
    )
```

### Tool Output
- All tool `_run()` methods must return **JSON strings**
- Results must be parseable via `json.loads()`
- Use `_json_utils.py` helpers for standardization

## HTML Rendering

### BeautifulSoup Class Attributes
```python
# ✅ CORRECT - Use attrs dictionary
tag = soup.new_tag("div")
tag.attrs["class"] = ["container", "my-class"]

# ❌ WRONG - Produces invalid HTML
tag = soup.new_tag("div", class_="container")
```

### CSS Styling
- Use CSS variables with fallbacks for colors
- Ensure theme compatibility (light/dark modes)
```css
.element {
    color: var(--text-color, #343a40);
    background: var(--highlight-bg, #f8f9fa);
}
```

### Empty State Handling
- Always check for empty data
- Render user-friendly messages when data is missing

## Testing Conventions

### Test Structure
- Tests in `tests/` directory mirror `src/` structure
- Use descriptive test function names: `test_function_name_behavior()`

### Test Libraries
- Use `pytest` for all tests
- Use `pytest-mock` (mocker fixture) for mocking
- Use `Faker` for realistic test data
- Use `pendulum` for date/time control in tests

### What to Test
- **DO**: Test deterministic components (tools, utilities)
- **DO**: Use `crewai flow kickoff` for end-to-end validation
- **DON'T**: Write unit tests for non-deterministic agents

### Test Environment
- Environment variables set in `pyproject.toml` [tool.pytest.ini_options]
- `POSTHOG_DISABLED=1` to disable telemetry in tests

## Linting Rules (Ruff)

### Enabled Rule Sets
- **E**: pycodestyle errors
- **W**: pycodestyle warnings
- **F**: Pyflakes
- **I**: isort (import sorting)
- **N**: pep8-naming
- **UP**: pyupgrade (except UP007, UP035, UP045 - Union compatibility)
- **B**: flake8-bugbear (except B008, B904)
- **C4**: flake8-comprehensions
- **PIE**: flake8-pie
- **SIM**: flake8-simplify
- **RET**: flake8-return (except RET504)

### Ignored Rules
- `E501`: Line too long (handled by formatter)
- `UP007`, `UP035`, `UP045`: Union syntax (CrewAI compatibility)
- `B008`: Function calls in defaults (needed for FastAPI/Pydantic)
- `B904`: Raise from exceptions
- `RET504`: Unnecessary assignment before return

## YAML Style (yamllint)

### Configuration
- Indentation: 2 spaces
- Max line length: 120 characters
- Document start: Required (`---`)
- Document end: Not required
- No trailing spaces
- New line at end of file required
- No duplicate keys

### Formatting
```yaml
---
# Document starts with ---
agent_name:
  role: "Role description"
  goal: "Agent goal"
  backstory: "Agent backstory"
```

## Git Workflow

### Commit Messages
- Use descriptive, concise messages
- For multiline commits, use file-based approach:
```bash
echo "feat: Add feature

Detailed description here" > commit_message.tmp
git commit -F commit_message.tmp
rm commit_message.tmp
```

### Pre-commit Hooks
Automatically run on commit:
1. `ruff check --fix` (linting)
2. `ruff format` (formatting)
3. `yamllint -s` (YAML validation)

## Anti-Patterns (What to Avoid)

### General
- ❌ Don't over-engineer solutions
- ❌ Don't add features beyond what's requested
- ❌ Don't add unnecessary error handling for impossible scenarios
- ❌ Don't create abstractions for one-time operations
- ❌ Don't add docstrings/comments to code you didn't change

### CrewAI Specific
- ❌ Never bypass CrewAI Flow with direct execution
- ❌ Never call crew methods directly from `main.py`
- ❌ Never pass context via constructor parameters
- ❌ Never specify tools in YAML files
- ❌ Never use `python -m` to run crews

### Package Management
- ❌ Never use `pip`, `poetry`, or other package managers
- ❌ Only use `uv` for ALL Python package operations
