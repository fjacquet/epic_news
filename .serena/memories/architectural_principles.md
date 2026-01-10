# Architectural Principles

## Core Design Philosophy

Epic News operates on the **CrewAI Flow paradigm** with these guiding principles:

### 1. CrewAI-First Approach
- Use framework capabilities before writing custom Python
- Leverage CrewAI's built-in features for orchestration
- Never bypass the framework's execution model

### 2. Configuration-Driven Design
- Separate code from configuration using YAML
- Define agents and tasks in YAML files
- Assign tools programmatically (NOT in YAML)

### 3. Context-Driven Flow
- Let data flow naturally through the system
- Use CrewAI's input mechanism for context passing
- Avoid constructor injection for context

### 4. Async by Default
- Maximize performance with parallel execution
- Design for concurrent operations
- Use async patterns where appropriate

## Execution Model

### CRITICAL: CrewAI Flow Execution

**ALWAYS use CrewAI Flow command**:
```bash
crewai flow kickoff  # ✅ CORRECT
```

**NEVER use direct Python execution**:
```bash
python -m src.epic_news.crews.fin_daily.run  # ❌ WRONG
python src/epic_news/main.py                  # ❌ WRONG
```

### Why This Matters
- CrewAI Flow manages the complete execution lifecycle
- Ensures proper state management and context injection
- Handles async execution and crew coordination
- Guarantees consistent execution patterns

## Data Flow Architecture

### 1. State Management
- **Immutable State**: State flows through the system without mutation
- **Pydantic Models**: Use for structured data with clear state transitions
- **Context Passing**: Use `.to_crew_inputs()` methods

```python
# ✅ CORRECT - Context-driven flow
crew_inputs = self.state.to_crew_inputs()
result = MyCrew().crew().kickoff(inputs=crew_inputs)

# ❌ WRONG - Constructor injection
crew = MyCrew(topic=topic, objective=objective)
```

### 2. Two-Agent Pattern for HTML Reports

**Problem**: Agents with tools write action traces to output files instead of final results.

**Solution**: Separate research from reporting

1. **Research Agent(s)**:
   - Equipped with tools
   - NO `output_file` parameter
   - Gather data and pass via context

2. **Reporting Agent**:
   - **NO TOOLS** (critical!)
   - Has `output_file` parameter
   - Takes data from context
   - Generates clean HTML report

```python
# ✅ CORRECT - Two-agent pattern
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=[WikipediaSearchTool(), SerperDevTool()],
        # No output_file
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # NO TOOLS = No action traces
        output_file="output/report.html",
    )
```

### 3. Deterministic Python Rendering

For crews with predictable, structured output:

1. **Execute Crew**: Run via CrewAI Flow, get `CrewOutput`
2. **Parse to Pydantic**: Validate output against structured model
3. **Render via Factory**: Use Python factory function with `TemplateManager`

```python
# Example deterministic flow
report_content = SaintDailyCrew().crew().kickoff(inputs=inputs)
saint_model = SaintData.model_validate(json.loads(report_content.raw))
saint_to_html(saint_model, html_file="output/saint_daily/report.html")
```

## HTML Rendering Architecture

### Template System
- **TemplateManager**: Centralized template management
- **Jinja2 Templates**: Universal HTML templates
- **Renderer Pattern**: Crew-specific renderers extending `BaseRenderer`

### Renderer Guidelines
1. All renderers **must implement `__init__`** (even if empty)
2. Use `TemplateManager.render_report()` with crew identifier
3. Handle empty states gracefully
4. Use CSS variables for theme compatibility

### Factory Pattern
Each crew should expose a factory function:
- Normalizes `CrewOutput`, Pydantic model, or `dict`
- Delegates to `TemplateManager.render_report()`
- Optionally persists HTML
- Example: `saint_to_html()`, `menu_to_html()`

## Data Validation Strategy

### Pydantic Model Design
1. **Model the data you have**, not idealized structures
2. **Simplicity over complexity**: Prefer flat structures
3. **Legacy Union syntax**: Always use `Union[X, Y]` for CrewAI compatibility

### Data Normalization
When working with external data (LLMs, APIs):
1. **Field name mapping**: Map alternative names to schema
2. **Multilingual handling**: Map French → English keys
3. **Structure conversion**: Convert strings to objects as needed
4. **Default values**: Provide sensible defaults for missing fields

Example:
```python
# Map alternative field names
if "name" in source and "title" not in source:
    source["title"] = source["name"]

# Handle multilingual keys
if "fr" in phrase and "french" not in phrase:
    phrase["french"] = phrase["fr"]

# Provide defaults
if "address" not in accommodation:
    accommodation["address"] = "Address not provided"
```

## Information Retrieval Strategy

### Real-Time Retrieval (NOT RAG)
- **Principle**: Data freshness over static knowledge base
- **Approach**: Agents use real-time tools for every task
- **Rationale**: Prevents data staleness, unlimited scope

### Key Tools
- `SerperDevTool` / `TavilyTool`: General web search
- `get_scraper()`: Centralized scraping (via `ScraperFactory`)
- `YahooFinanceNewsTool`: Financial news
- `SaveToRagTool`: Short-term memory/scratchpad (not permanent storage)

### Tool Output Standardization
- All tool `_run()` methods return **JSON strings**
- Must be parseable via `json.loads()`
- Use `_json_utils.py` helpers

## Path and Directory Management

### Path Handling
- **All paths must be project-relative**
- Manage paths programmatically
- Never use hard-coded absolute paths

### Directory Creation
- **Centralized**: Use `ensure_output_directories()` at startup
- **Never**: Use `os.makedirs()` in crew/task logic
- **Called from**: `main.py` during initialization

## Tool Assignment Pattern

### CRITICAL: Tools in Code, Not YAML

**NEVER specify tools in YAML**:
```yaml
# ❌ WRONG - Don't do this
researcher:
  role: "Researcher"
  tools:
    - WikipediaTool
    - SerperTool
```

**ALWAYS assign tools in code**:
```python
# ✅ CORRECT
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=self.search_tools,  # From factory
        verbose=True,
    )
```

**Rationale**: Hybrid YAML/code tool config causes `KeyError` when CrewAI maps YAML names to non-existent functions.

## Error Handling and Resilience

### Fail Fast Principle
- Validate inputs early
- Use type hints and Pydantic for validation
- Provide clear, actionable error messages

### HTTP Resilience
- **Retry on 5xx**: Transient server errors
- **No retry on 4xx**: Client errors (bad request)
- **Use tenacity**: For retry logic
- **Proper timeouts**: Prevent hanging requests

Example:
```python
from tenacity import retry, stop_after_attempt, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(requests.exceptions.HTTPError)
)
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

## Code Organization Patterns

### Crew Structure
```
crew_name/
├── config/
│   ├── agents.yaml      # Agent definitions
│   └── tasks.yaml       # Task definitions
└── crew_name_crew.py    # Crew implementation
```

### Tool Factory Pattern
- Centralized tool creation
- Example: `web_search_factory.py`, `scraper_factory.py`
- Supports runtime provider selection via environment variables

### Model Organization
- Pydantic models in `src/epic_news/models/`
- One model per crew (or shared models)
- Clear naming: `SaintData`, `FinancialReport`, `MenuDesignerReport`

## Testing Strategy

### What to Test
- ✅ **DO**: Test deterministic components (tools, utilities)
- ✅ **DO**: Use `crewai flow kickoff` for end-to-end validation
- ❌ **DON'T**: Write unit tests for non-deterministic agents

### Test Utilities
- **Faker**: Realistic test data
- **pytest-mock**: Mocking
- **pendulum**: Date/time control
- **contextlib**: Reusable context managers for mocking

### Test Environment
- Environment variables in `pyproject.toml`
- `POSTHOG_DISABLED=1` for tests
- Mock API keys provided

## Anti-Patterns to Avoid

### Execution
- ❌ Never bypass CrewAI Flow
- ❌ Never call crew methods directly
- ❌ Never reinvent the wheel (use existing utilities)

### Data Flow
- ❌ Never pass context via constructor
- ❌ Never mutate state
- ❌ Never use Python 3.10+ Union syntax (`X | Y`) in Pydantic models

### Tool Assignment
- ❌ Never specify tools in YAML
- ❌ Never mix YAML and code tool configuration

### Over-Engineering
- ❌ Don't add features beyond requirements
- ❌ Don't create abstractions for one-time operations
- ❌ Don't add error handling for impossible scenarios
- ❌ Don't add docstrings to code you didn't change

## Key Learnings from Menu Designer Integration

1. **Pydantic Union Syntax**: Always use `Union[X, Y]` not `X | Y`
2. **Factory Consistency**: Small, deterministic factories for each crew
3. **Renderer Construction**: All `BaseRenderer` subclasses need `__init__`
4. **Nested Data Handling**: Support both flat and nested structures
5. **Debugging Pattern**: Use `dump_crewai_state()` for troubleshooting

## Summary: The Epic News Way

1. **Simple over Complex**: KISS principle always
2. **CrewAI-First**: Leverage the framework
3. **Configuration-Driven**: YAML for config, code for logic
4. **Type-Safe**: Pydantic validation everywhere
5. **Fail Fast**: Early validation, clear errors
6. **Real-Time Data**: Fresh over stale
7. **Deterministic Rendering**: Python over LLM for HTML when possible
8. **Test What Matters**: Focus on deterministic components
9. **Clean HTML**: Two-agent pattern prevents action traces
10. **Centralized Utilities**: Reuse over rewrite
