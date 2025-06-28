# Epic News Design Principles

> **Light as a Haiku** 🌸  
> Epic News is designed to be elegant, minimalist, and simple. Every line of code should serve a purpose.

## Philosophy

Epic News operates on the **CrewAI Flow paradigm** - a revolutionary approach to multi-agent AI systems that emphasizes:

- **CrewAI-First**: Use framework capabilities before writing custom Python
- **Configuration-Driven**: Separate code from configuration using YAML
- **Context-Driven**: Let data flow naturally through the system
- **Async by Default**: Maximize performance with parallel execution

## Core Principles

### 1. KISS, YAGNI, DRY

- **Keep It Simple, Stupid**: Favor simple solutions over complex ones
- **You Aren't Gonna Need It**: Don't build features until they're needed
- **Don't Repeat Yourself**: Eliminate code duplication through abstraction

### 2. Fail Fast

- Validate inputs early and provide clear error messages
- Use type hints and Pydantic models for data validation
- Prefer explicit errors over silent failures

### 3. Immutable State

- State flows through the system without mutation
- Use Pydantic models for structured data
- Clear state transitions between flow steps

### 4. Code Style and Quality

- **Imports**: ALL imports must be placed at the top of Python files, never inside functions or methods. This ensures clarity, prevents circular imports, and follows PEP 8 standards.
- **Whitespace**: Avoid trailing whitespace (`W291`) and whitespace on blank lines (`W293`). These are enforced by `ruff` and help maintain a clean, readable codebase.

## CrewAI Best Practices

### Context Injection (CRITICAL)

**NEVER** pass context via constructor parameters. Use CrewAI's input mechanism:

```python
# ✅ CORRECT - Context-driven
crew_inputs = self.state.to_crew_inputs()
result = MyCrew().crew().kickoff(inputs=crew_inputs)

# ❌ WRONG - Constructor injection
crew = MyCrew(topic=topic, objective=objective)
```

### Python Type Compatibility (CRITICAL)

**CrewAI Pydantic Schema Parser Limitation**: CrewAI's internal schema parser is incompatible with Python 3.10+ Union syntax (`X | Y`). Always use the legacy `Union[X, Y]` syntax for all Pydantic models used with CrewAI.

```python
from typing import Union, Optional

# ✅ CORRECT - Compatible with CrewAI
field: Union[str, None] = None
field: Optional[str] = None

# ❌ WRONG - Causes AttributeError in CrewAI
field: str | None = None
```

**Rationale**: CrewAI's `PydanticSchemaParser` attempts to access `field_type.__name__` on `types.UnionType` objects, which don't have this attribute. This causes runtime errors during schema generation for task outputs.

**Enforcement**: This constraint is enforced via Ruff rule `UP007` (disabled) to prevent automatic conversion to the newer syntax.

### Tool Selection Strategy

**RAG Contamination Prevention** - RAG systems can inject irrelevant data:

| Use Case | Recommended Tools | Avoid |
|----------|------------------|-------|
| **Product Research** | `get_search_tools()` + `get_scrape_tools()` | RAG tools |
| **Price Analysis** | Live scraping only | RAG (prices change rapidly) |
| **General Knowledge** | RAG acceptable | N/A |
| **Report Generation** | `get_reporting_tools()` only | Search/scrape |

```python
# ✅ CORRECT - Fresh data for product research
@agent
def product_researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["product_researcher"],
        tools=get_search_tools() + get_scrape_tools(),  # NO RAG
        verbose=True,
    )
```

### Async Execution

Enable async execution for I/O-bound tasks:

```python
@crew
def my_crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        async_execution=True,  # ✅ Enable for performance
        verbose=True,
    )
```

**Exception**: Final task in sequential process must be synchronous.

## Configuration Management

### YAML-First Approach

Define agents, tasks, and crews in YAML files:

```yaml
# agents.yaml
product_researcher:
  role: "Product Research Specialist"
  goal: "Research {topic} comprehensively"
  backstory: "Expert in analyzing products and market trends"
```

### Path Management

**CRITICAL**: All file paths must be project-relative and managed programmatically:

```python
# ✅ CORRECT - Project-relative paths
_crew_path = pathlib.Path(__file__).parent
project_root = _crew_path.parent.parent.parent.parent.parent
output_dir = str(project_root / 'output' / 'news')

# ❌ WRONG - Absolute paths create nested structures
# output_dir = os.path.join(os.getcwd(), 'output', 'news')
```

**Never** create nested `/Users/.../Users/...` directory structures.

### Directory Management

**CRITICAL**: Directory creation should be centralized and happen only once at application startup:

```python
# ✅ CORRECT - Centralized directory creation at initialization
from epic_news.utils.directory_utils import ensure_output_directories

def __init__(self):
    ensure_output_directories()  # Creates all required directories at once
    # Rest of initialization...

# ✅ CORRECT - Just use the directories, don't create them again
def generate_report(self):
    self.state.output_file = "output/report/result.html"  # Directory already exists

# ❌ WRONG - Redundant directory creation
def generate_report(self):
    os.makedirs("output/report", exist_ok=True)  # Redundant, already created at init
    self.state.output_file = "output/report/result.html"
```

**Why**:

- Minimizes redundant directory creation calls
- Simplifies code by removing scattered directory management
- Improves performance by creating directories only once
- Makes directory structure explicit and centrally managed

## Tool Architecture

### Single Responsibility

Each tool should have one clear purpose:

```python
class GitHubSearchTool(BaseTool):
    name: str = "GitHub Search"
    description: str = "Search GitHub repositories"
    # ... focused implementation
```

### Centralized Factories

Use factory functions for tool organization:

```python
def get_search_tools() -> list[BaseTool]:
    return [SerperDevTool(), GitHubSearchTool()]

def get_scrape_tools() -> list[BaseTool]:
    return [ScrapeNinjaTool(), WebsiteReaderTool()]
```

### Model Separation

Define Pydantic models in `src/epic_news/models/`:

```python
# src/epic_news/models/github_models.py
class GitHubSearchInput(BaseModel):
    query: str
    max_results: int = 10
```

### Tool Assignment (CRITICAL)

**NEVER** specify tools in `agents.yaml`. Tools must be assigned programmatically in code:

```yaml
# ✅ CORRECT - No tools in YAML
researcher:
  role: "Lead News Researcher"
  goal: "Research {topic} comprehensively"
  backstory: "Expert in analyzing products and market trends"
  # NO tools: section here
```

```python
# ✅ CORRECT - Tools assigned in code
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=self.search_tools,  # Tools from factory functions
        verbose=True,
    )
```

**Why**: Hybrid YAML/code tool configuration causes `KeyError` when CrewAI tries to map YAML tool names to non-existent functions. Tools should be managed through factory functions and assigned programmatically.

## Output Standards

### HTML Reports

All agent outputs must be comprehensive HTML reports:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Report Title</title>
</head>
<body>
    <h1>📊 Report Title</h1>
    <!-- Structured content with emojis -->
</body>
</html>
```

**Requirements**:

- UTF-8 encoding for emoji support
- Semantic HTML5 structure
- Clear sections with actionable conclusions
- No raw API responses or placeholder text
- Publication date and data sources

### Quality Checklist

- ✅ HTML validity
- ✅ Complete information (no TODOs)
- ✅ Accurate data with sources
- ✅ Clear structure and formatting
- ✅ Actionable recommendations

## Project Structure

```
epic_news/
├── src/epic_news/
│   ├── crews/           # Crew implementations
│   ├── tools/           # Tool implementations
│   ├── models/          # Pydantic models
│   └── main.py          # Flow orchestration
├── docs/                # Documentation
├── output/              # Generated reports
└── tests/               # Unit tests
```

## Development Workflow

### Package Management

- Use `uv` for all Python operations
- Run workflows with `crewai flow kickoff`

### Testing Philosophy

- **Focus on Tools**: Test deterministic components (tools)
- **E2E Validation**: Use `crewai flow kickoff` for integration testing
- **No Agent Tests**: Agents are non-deterministic by nature
- **Pytest**: Use pytest for unit testing
- **pydantic v2**: Use pydantic v2 for data validation
- **Type Hints**: Use type hints for data validation

### Documentation

- Update `tools_handbook.md` for new tools
- Include API key requirements
- Provide usage examples

## HTML Output Architecture

### CrewAI Agent Output Patterns

**CRITICAL**: CrewAI has a known issue where agents with tools write action traces to output files instead of final results.

#### Single Agent Pattern (Problematic)

```python
# ❌ PROBLEMATIC - Agent with tools writes action traces to output file
@agent
def researcher_reporter(self) -> Agent:
    return Agent(
        tools=[WikipediaSearchTool(), SerperDevTool()],  # Tools cause action traces
        # Output file gets: "Action: Wikipedia Search\n{\"query\": \"...\"}" instead of HTML
    )
```

**Result**: Output file contains action traces like:

```
Thought: I will search for information about...
Action: Wikipedia Search
{"query": "saint june 23"}
```

#### Two-Agent Pattern (Recommended)

```python
# ✅ CORRECT - Separate research and reporting agents
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=[WikipediaSearchTool(), SerperDevTool()],  # Research with tools
        # No output_file - passes data to next agent
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # NO TOOLS = No action traces
        # Generates clean HTML output
    )
```

**Result**: Clean HTML output without action traces.

#### Pattern Examples

**ShoppingAdvisorCrew** (Working):

- `product_researcher` → Tools for research
- `price_analyst` → Tools for analysis  
- `competitor_analyst` → Tools for competition
- `shopping_advisor` → **NO TOOLS** → Clean HTML output

**SaintDailyCrew** (Fixed):

- `saint_researcher` → **NO TOOLS** → Direct HTML generation
- Alternative: Add separate research agent with tools + reporter without tools

### HTML Generation Best Practices

#### Agent Configuration for HTML Output

```yaml
# agents.yaml - Final reporting agent
reporter:
  role: "HTML Report Specialist"
  goal: >
    Generate complete HTML5 document based on research data.
    Output only pure HTML starting with <!DOCTYPE html>.
    No JSON wrapper, no markdown, no tool usage traces.
  backstory: >
    Expert at creating professional HTML reports based on provided research.
    Can generate comprehensive reports without needing research tools.
```

#### Task Configuration for HTML Output

```yaml
# tasks.yaml - HTML generation task
html_report_task:
  agent: reporter
  description: >
    Generate a complete HTML5 document with the following structure:
    - <!DOCTYPE html> declaration
    - Professional CSS styling
    - Structured content sections
    Start your response immediately with <!DOCTYPE html>.
    Do not write any text before or after the HTML.
  expected_output: >
    Raw HTML5 document starting with <!DOCTYPE html> and ending with </html>.
    No JSON wrapper, no markdown, no explanatory text - just pure HTML.
  output_file: output/reports/result.html
```

### Troubleshooting HTML Output Issues

#### Problem: Action Traces in Output

```
# Output file contains:
Thought: I will research...
Action: Wikipedia Search
{"query": "..."}
```

**Solution**: Remove tools from the final reporting agent:

```python
@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # Remove all tools
        # Agent generates HTML based on knowledge/context
    )
```

#### Problem: JSON-Wrapped HTML

```json
{"html": "<!DOCTYPE html>..."}
```

**Solution**: Use post-processing HTML extractor or ensure agent outputs raw HTML.

#### Problem: Markdown Instead of HTML

```markdown
# Report Title
## Section 1
```

**Solution**: Explicitly require HTML5 in agent goal and task description.

## Agent Guidelines

### Research Agents

- Exhaustive information gathering (20+ data points)
- Include metrics, sources, and limitations
- Structured output for downstream agents
- **Use tools freely** - they don't write to output files

### Reporting Agents

- Transform research into professional reports
- Maintain information depth
- Use consistent formatting and tone
- **NO TOOLS** - prevents action traces in output
- Generate HTML directly based on research context

### Collaboration Standards

- Pass full context between agents
- Document reasoning and uncertainty
- Reference prior work consistently
- Highlight data limitations
- **Research agents** provide comprehensive data
- **Reporting agents** focus on clean output generation

## Error Handling

### Graceful Degradation

- Provide partial results when possible
- Clear error messages with context
- Fallback strategies for tool failures

### Validation

- Input validation at tool entry points
- Output format verification
- Path validation before file operations

---

*This document evolves with the project. Update it when introducing new patterns or discovering better practices.*
