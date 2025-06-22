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

**Always verify** that `{topic}` and `{objective}` placeholders receive correct user input:

- Debug flow: User Request → Information Extraction → `to_crew_inputs()` → Task Placeholders
- Check task descriptions in execution logs for proper context injection

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

### Documentation

- Update `tools_handbook.md` for new tools
- Include API key requirements
- Provide usage examples

## Agent Guidelines

### Research Agents

- Exhaustive information gathering (20+ data points)
- Include metrics, sources, and limitations
- Structured output for downstream agents

### Reporting Agents

- Transform research into professional reports
- Maintain information depth
- Use consistent formatting and tone

### Collaboration Standards

- Pass full context between agents
- Document reasoning and uncertainty
- Reference prior work consistently
- Highlight data limitations

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
