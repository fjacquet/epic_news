# Utils Directory Context

This directory contains all utility modules for the Epic News system, including HTML rendering, content extraction, observability, and helper functions.

## Directory Structure

```
utils/
├── html/                          # HTML rendering system
│   ├── template_manager.py       # Central rendering coordinator
│   ├── templates.py               # Legacy template functions
│   ├── path.py                    # Path resolution utilities
│   ├── validator.py               # HTML validation
│   ├── extractor.py               # HTML content extraction
│   └── template_renderers/        # Crew-specific renderers (17 renderers)
│       ├── base_renderer.py       # Abstract base class
│       ├── renderer_factory.py    # Renderer selection logic
│       ├── generic_renderer.py    # Fallback renderer
│       └── *_renderer.py          # Crew-specific renderers
├── extractors/                    # Content extraction from crew outputs
│   ├── base_extractor.py          # Abstract base class
│   ├── factory.py                 # Extractor selection
│   └── *_extractor.py             # Crew-specific extractors
├── diagnostics/                   # Debugging and analysis tools
│   ├── analysis.py                # Crew output analysis
│   ├── parsing.py                 # JSON parsing utilities
│   └── dumping.py                 # Debug data dumping
└── (root level utilities)         # Various helper modules
```

## HTML Rendering System

### Architecture Overview

The HTML rendering system follows a **deterministic Python rendering** pattern using BeautifulSoup:

1. **TemplateManager** (`template_manager.py`): Central coordinator that loads templates and delegates rendering
2. **BaseRenderer** (`base_renderer.py`): Abstract base class defining renderer interface
3. **Crew-specific renderers**: Extend BaseRenderer with crew-specific HTML generation
4. **RendererFactory** (`renderer_factory.py`): Selects appropriate renderer for each crew

**Key principle**: Generate HTML programmatically in Python, not via Jinja2/LLM-generated HTML strings.

### TemplateManager

**Location**: `src/epic_news/utils/html/template_manager.py`

**Purpose**: Central coordinator for all HTML report generation.

**Static method pattern**:
```python
from epic_news.utils.html.template_manager import TemplateManager

# Render a crew report
TemplateManager.render_report(
    crew_identifier="poem",           # Crew name
    data=poem_model.model_dump(),     # Pydantic model as dict
    output_path="output/poem/report.html"
)
```

**How it works**:
1. Loads universal template from `templates/universal_report_template.html`
2. Uses RendererFactory to get crew-specific renderer
3. Renderer generates HTML body from data
4. Injects body into template with title, date, dark mode CSS
5. Writes final HTML to output_path

**Benefits**:
- Centralized template management
- Consistent styling across all crews
- Dark mode support built-in
- CSS variable-based theming

### BaseRenderer

**Location**: `src/epic_news/utils/html/template_renderers/base_renderer.py`

**Purpose**: Abstract base class for all HTML content renderers.

**Required implementation**:
```python
from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer

class MyCrewRenderer(BaseRenderer):
    def __init__(self):
        \"\"\"MUST implement even if empty (mypy requirement).\"\"\"
        pass
    
    def render(self, data: dict[str, Any]) -> str:
        \"\"\"
        Generate HTML body from crew data.
        
        Args:
            data: Crew Pydantic model as dictionary
            
        Returns:
            HTML string for content body
        \"\"\"
        soup = self.create_soup("div", class_="report-container")
        # Build HTML using BeautifulSoup
        return str(soup)
```

**Helper methods**:
- `create_soup(tag, **attrs)`: Create new BeautifulSoup object
- `add_section(soup, parent_selector, tag, content, **attrs)`: Add section to soup
- `escape_html(text)`: Escape HTML special characters

### BeautifulSoup Patterns

**Creating elements**:
```python
soup = self.create_soup("div", class_="container")
root = soup.find("div")

# Create new tags
header = soup.new_tag("h1")
header.string = "My Title"
root.append(header)

# Set attributes
header["id"] = "main-title"
header["class"] = ["title", "highlighted"]  # List for multiple classes
```

**IMPORTANT**: Use `tag.attrs["class"] = [...]` for CSS classes, NOT `class_="..."` in new_tag():
```python
# ✅ CORRECT
section = soup.new_tag("section")
section.attrs["class"] = ["card", "highlighted"]

# ❌ WRONG - Causes mypy errors
section = soup.new_tag("section", class_="card highlighted")
```

**CSS Variables**:
Always use CSS variables with fallbacks for theming:
```python
section["style"] = "color: var(--text-color, #343a40); background: var(--bg-color, #ffffff);"
```

**Empty state handling**:
```python
if not data.get("items"):
    empty_div = soup.new_tag("div", class_="empty-state")
    empty_div.string = "No items to display"
    root.append(empty_div)
    return str(soup)
```

### Crew-Specific Renderers

**Available renderers** (17 total):
- poem_renderer.py, cooking_renderer.py, shopping_renderer.py
- holiday_renderer.py, book_summary_renderer.py, menu_renderer.py
- saint_renderer.py, meeting_prep_renderer.py
- news_daily_renderer.py, company_news_renderer.py, rss_weekly_renderer.py
- financial_renderer.py, sales_prospecting_renderer.py
- cross_reference_report_renderer.py, deep_research_renderer.py
- generic_renderer.py (fallback for crews without specific renderer)

**Renderer naming convention**: `{crew_name}_renderer.py` → `{CrewName}Renderer` class

**Example**:
```python
# src/epic_news/utils/html/template_renderers/poem_renderer.py
from epic_news.utils.html.template_renderers.base_renderer import BaseRenderer

class PoemRenderer(BaseRenderer):
    def __init__(self):
        pass
    
    def render(self, data: dict[str, Any]) -> str:
        soup = self.create_soup("div", class_="poem-container")
        root = soup.find("div")
        
        # Add title
        if title := data.get("poem_title"):
            title_tag = soup.new_tag("h1")
            title_tag.string = title
            root.append(title_tag)
        
        # Add stanzas
        for stanza in data.get("stanzas", []):
            stanza_div = soup.new_tag("div")
            stanza_div.attrs["class"] = ["stanza"]
            stanza_div.string = stanza
            root.append(stanza_div)
        
        return str(soup)
```

### RendererFactory

**Location**: `src/epic_news/utils/html/template_renderers/renderer_factory.py`

**Purpose**: Select appropriate renderer for each crew.

```python
from epic_news.utils.html.template_renderers.renderer_factory import RendererFactory

renderer = RendererFactory.get_renderer("poem")  # Returns PoemRenderer()
html_body = renderer.render(data)
```

**Fallback**: Returns `GenericRenderer` if no specific renderer exists.

### Factory Functions Pattern

Each crew should have a `{crew_name}_to_html()` factory function:

```python
# src/epic_news/utils/html/template_renderers/poem_renderer.py
def poem_to_html(poem_model: PoemModel, html_file: str):
    \"\"\"Generate HTML report for poem crew.\"\"\"
    TemplateManager.render_report(
        crew_identifier="poem",
        data=poem_model.model_dump(),
        output_path=html_file,
    )
```

**Usage in ReceptionFlow**:
```python
@listen("or(classify_flow, analyze_flow)")
def generate_poem(self, content_state: ContentState):
    result = PoemCrew().crew().kickoff(inputs=crew_inputs)
    poem_model = PoemModel.model_validate(json.loads(result.raw))
    
    # Use factory function
    poem_to_html(poem_model, html_file="output/poem/poem.html")
```

## Content Extraction System

### Purpose

Extract and structure data from crew outputs for further processing or rendering.

**Key difference from renderers**: Extractors prepare data, renderers generate HTML.

### BaseExtractor

**Location**: `src/epic_news/utils/extractors/base_extractor.py`

```python
from epic_news.utils.extractors.base_extractor import ContentExtractor

class MyCrewExtractor(ContentExtractor):
    def extract(self, state_data: dict[str, Any]) -> dict[str, Any]:
        \"\"\"
        Extract and structure content from state data.
        
        Args:
            state_data: Raw crew state data
            
        Returns:
            Structured dictionary ready for rendering
        \"\"\"
        return {
            "title": state_data.get("title"),
            "items": self._extract_items(state_data),
            "metadata": self._extract_metadata(state_data),
        }
```

### Extractor Factory

**Location**: `src/epic_news/utils/extractors/factory.py`

```python
from epic_news.utils.extractors.factory import ExtractorFactory

extractor = ExtractorFactory.get_extractor("news_daily")
structured_data = extractor.extract(raw_state_data)
```

### Available Extractors

- poem.py, cooking.py, shopping.py, saint.py
- news.py, daily_news.py, rss_weekly.py, fin_daily.py
- deep_research.py, generic.py (fallback)

## Observability & Monitoring

### Location

`src/epic_news/utils/observability.py`

### Components

**1. Tracer**: Event tracing for debugging
```python
from epic_news.utils.observability import Tracer, TraceEvent

tracer = Tracer(trace_id="my_crew_trace")

# Add events
tracer.add_event(TraceEvent(
    event_type="task_start",
    source="my_crew:researcher",
    details={"task": "search_web", "query": "AI news"}
))

# Query events
task_events = tracer.get_events(event_type="task_start")

# Save/load traces
tracer = Tracer.load_trace("my_crew_trace")
```

**2. HallucinationGuard**: Detect potential AI hallucinations
```python
from epic_news.utils.observability import HallucinationGuard

guard = HallucinationGuard(confidence_threshold=0.7)

# Check single statement
result = guard.check_statement(
    statement="This is definitely the best solution.",
    context={"source": "agent_output"}
)

# Validate full output
validation = guard.validate_output(
    output=agent_output,
    context={"crew": "research"},
    fix_hallucinations=True  # Adds disclaimer if issues found
)
```

**3. Dashboard**: Metrics collection
```python
from epic_news.utils.observability import Dashboard

dashboard = Dashboard(dashboard_id="my_crew_dashboard")

# Update metrics
dashboard.update_metric(
    category="agents",
    name="researcher",
    metric="calls",
    value=10
)

# Get metrics
agent_metrics = dashboard.get_metrics("agents", "researcher")
```

**4. Decorators**: Automatic tracing/monitoring
```python
from epic_news.utils.observability import trace_task, monitor_agent, guard_output

tracer = Tracer()
dashboard = Dashboard()
guard = HallucinationGuard()

@trace_task(tracer)
def my_task_function():
    # Automatically traced
    pass

@monitor_agent(dashboard)
def my_agent_function():
    # Automatically monitored
    pass

@guard_output(guard)
def my_output_function():
    # Automatically checked for hallucinations
    pass
```

**5. Factory Function**: Get all tools at once
```python
from epic_news.utils.observability import get_observability_tools

tools = get_observability_tools(crew_name="research")
# Returns: tracer, dashboard, hallucination_guard, decorators
```

## Helper Utilities

### Directory Management

**Location**: `src/epic_news/utils/directory_utils.py`

```python
from epic_news.utils.directory_utils import ensure_output_directory

# Create output directories if they don't exist
ensure_output_directory("output/reports")
ensure_output_directory("logs")
```

**IMPORTANT**: Never use `os.makedirs()` in crew/task logic. Use centralized directory management.

### Path Utilities

**Location**: `src/epic_news/utils/path_utils.py`

```python
from epic_news.utils.path_utils import get_project_root, resolve_output_path

# Get project root
root = get_project_root()

# Resolve output paths
output_file = resolve_output_path("reports", "my_report.html")
# Returns: /project/root/output/reports/my_report.html
```

### Logging

**Location**: `src/epic_news/utils/logger.py`

**Uses Loguru** for structured logging:
```python
from loguru import logger

logger.info("Task started")
logger.warning("API rate limit approaching")
logger.error("Failed to fetch data", exc_info=True)
logger.debug("Processing item {item_id}", item_id=123)
```

**Configuration**:
- Logs to `logs/` directory
- Auto-rotation (10MB per file)
- Colored console output
- Structured JSON format

### String Utilities

**Location**: `src/epic_news/utils/string_utils.py`

```python
from epic_news.utils.string_utils import (
    truncate_text,
    sanitize_filename,
    slugify,
    remove_html_tags,
)

# Truncate with ellipsis
short = truncate_text("Long text here", max_length=10)  # "Long te..."

# Clean filename
filename = sanitize_filename("My Report (2024).html")  # "my-report-2024.html"

# Create URL slug
slug = slugify("My Article Title!")  # "my-article-title"

# Strip HTML
clean = remove_html_tags("<p>Hello <b>world</b></p>")  # "Hello world"
```

### HTTP Utilities

**Location**: `src/epic_news/utils/http.py`

```python
from epic_news.utils.http import fetch_with_retry, async_fetch_batch

# Fetch with automatic retries
response = fetch_with_retry("https://api.example.com/data", max_retries=3)

# Async batch fetching
urls = ["https://example.com/1", "https://example.com/2"]
results = async_fetch_batch(urls)
```

**Features**:
- Automatic retry with exponential backoff
- Timeout handling
- User-agent rotation
- Response caching support

### Data Normalization

**Location**: `src/epic_news/utils/data_normalization.py`

```python
from epic_news.utils.data_normalization import (
    normalize_date,
    normalize_price,
    normalize_percentage,
)

# Standardize date formats
date = normalize_date("2024-01-15")  # datetime object

# Parse price strings
price = normalize_price("$1,234.56")  # 1234.56

# Parse percentages
pct = normalize_percentage("45.2%")  # 0.452
```

### File Utilities

**Location**: `src/epic_news/utils/file_utils.py`

```python
from epic_news.utils.file_utils import (
    read_json,
    write_json,
    read_yaml,
    ensure_directory,
)

# JSON handling
data = read_json("config.json")
write_json("output.json", data)

# YAML handling
config = read_yaml("agents.yaml")

# Directory handling
ensure_directory("output/reports")  # Creates if doesn't exist
```

## Menu Planning Utilities

### Menu Generator

**Location**: `src/epic_news/utils/menu_generator.py`

**Purpose**: Generate weekly meal plans with shopping lists.

```python
from epic_news.utils.menu_generator import MenuGenerator

generator = MenuGenerator()

# Generate weekly menu
menu = generator.generate_menu(
    dietary_restrictions=["vegetarian"],
    people_count=4,
    budget_per_meal=15.0,
)

# Generate shopping list
shopping_list = generator.create_shopping_list(menu)
```

### Menu Validator

**Location**: `src/epic_news/utils/menu_plan_validator.py`

```python
from epic_news.utils.menu_plan_validator import MenuPlanValidator

validator = MenuPlanValidator()

# Validate menu structure
is_valid = validator.validate(menu_data)

# Get validation errors
errors = validator.get_errors()
```

### Menu Utilities

**Location**: `src/epic_news/utils/menu_utils.py`

Helper functions for menu manipulation and formatting.

## RSS Utilities

### RSS Utils

**Location**: `src/epic_news/utils/rss_utils.py`

```python
from epic_news.utils.rss_utils import (
    parse_rss_feed,
    filter_by_date,
    deduplicate_entries,
)

# Parse feed
entries = parse_rss_feed("https://example.com/feed.xml")

# Filter recent entries
recent = filter_by_date(entries, days_ago=7)

# Remove duplicates
unique = deduplicate_entries(entries)
```

### RSS Weekly Converter

**Location**: `src/epic_news/utils/rss_weekly_converter.py`

Converts RSS feed data to structured format for HTML rendering.

## Diagnostics & Debugging

### Analysis Tools

**Location**: `src/epic_news/utils/diagnostics/analysis.py`

```python
from epic_news.utils.diagnostics.analysis import analyze_crew_output

# Analyze crew execution
analysis = analyze_crew_output(crew_result)
# Returns: token usage, execution time, task breakdown, errors
```

### Parsing Utilities

**Location**: `src/epic_news/utils/diagnostics/parsing.py`

```python
from epic_news.utils.diagnostics.parsing import (
    safe_json_parse,
    extract_json_from_text,
)

# Safe JSON parsing with fallback
data = safe_json_parse(possibly_invalid_json, default={})

# Extract JSON from mixed text
json_data = extract_json_from_text("Some text {\"key\": \"value\"} more text")
```

### Debug Dumping

**Location**: `src/epic_news/utils/diagnostics/dumping.py`

```python
from epic_news.utils.diagnostics.dumping import dump_crew_state

# Dump crew state for debugging
dump_crew_state(
    crew_name="research",
    state_data=state,
    output_dir="debug/",
)
# Creates: debug/research_state_20240115_153045.json
```

## Flow & Orchestration

### Task Orchestration

**Location**: `src/epic_news/utils/task_orchestration.py`

Utilities for coordinating multi-task workflows within crews.

### Flow Enforcement

**Location**: `src/epic_news/utils/flow_enforcement.py`

Ensures crews follow proper execution patterns and state transitions.

## Performance & Reliability

### CrewAI Retry Patch

**Location**: `src/epic_news/utils/crewai_retry_patch.py`

**Purpose**: Patches CrewAI to add automatic retry logic for transient failures.

```python
from epic_news.utils.crewai_retry_patch import apply_retry_patch

# Apply patch at application startup
apply_retry_patch(max_retries=3, backoff_factor=2)
```

### LLM Retry Logic

**Location**: `src/epic_news/utils/llm_retry.py`

```python
from epic_news.utils.llm_retry import retry_on_llm_error

@retry_on_llm_error(max_retries=3)
def call_llm():
    # LLM call that might fail
    pass
```

### Tool Logging

**Location**: `src/epic_news/utils/tool_logging.py`

Decorators and utilities for logging tool usage and performance:
```python
from epic_news.utils.tool_logging import log_tool_usage

@log_tool_usage
def my_tool_function():
    # Automatically logged with timing, args, results
    pass
```

## Report Utilities

### Report Utils

**Location**: `src/epic_news/utils/report_utils.py`

Common report generation utilities:
```python
from epic_news.utils.report_utils import (
    format_currency,
    format_percentage,
    format_large_number,
)

# Format values for reports
price = format_currency(1234.56)  # "$1,234.56"
pct = format_percentage(0.452)    # "45.2%"
num = format_large_number(1500000)  # "1.5M"
```

### Dashboard Generator

**Location**: `src/epic_news/utils/dashboard_generator.py`

Generate interactive HTML dashboards from crew metrics.

## Testing Utilities

### Debug Utils

**Location**: `src/epic_news/utils/debug_utils.py`

```python
from epic_news.utils.debug_utils import (
    print_structure,
    compare_outputs,
    validate_pydantic,
)

# Print data structure
print_structure(complex_dict)

# Compare crew outputs
diff = compare_outputs(output1, output2)

# Validate Pydantic model
errors = validate_pydantic(MyModel, data)
```

## Common Patterns

### HTML Rendering Workflow

1. **Crew execution** → Returns Pydantic model
2. **Model validation** → `MyModel.model_validate(json.loads(result.raw))`
3. **Factory function** → `my_crew_to_html(model, output_path)`
4. **TemplateManager** → Delegates to crew-specific renderer
5. **Renderer.render()** → Generates HTML body using BeautifulSoup
6. **Template injection** → Inserts body into universal template
7. **File write** → Saves final HTML to output_path

### Content Extraction Workflow

1. **Raw state data** → From crew execution
2. **Extractor selection** → `ExtractorFactory.get_extractor(crew_name)`
3. **Data extraction** → `extractor.extract(state_data)`
4. **Structured output** → Dictionary ready for rendering or further processing

### Observability Workflow

1. **Initialize tools** → `get_observability_tools(crew_name)`
2. **Decorate functions** → Apply `@trace_task`, `@monitor_agent`, `@guard_output`
3. **Automatic tracking** → Events, metrics, hallucination checks
4. **Post-execution** → Load traces/dashboards for analysis

## Best Practices

### HTML Rendering

1. **Always extend BaseRenderer** for crew-specific renderers
2. **Implement `__init__`** even if empty (mypy requirement)
3. **Use CSS variables** with fallbacks for theming
4. **Handle empty states** gracefully
5. **Use `tag.attrs["class"] = [...]`** for CSS classes
6. **Return string** from `render()` method: `str(soup)`

### Content Extraction

1. **Validate input data** before extraction
2. **Provide sensible defaults** for missing fields
3. **Document data structure** in extractor docstring
4. **Test with edge cases** (empty lists, null values)

### Path Management

1. **Use centralized functions** (`ensure_output_directory`, `resolve_output_path`)
2. **Never hardcode paths** in crews or tasks
3. **Always use project-relative paths**
4. **Validate paths exist** before reading/writing

### Logging

1. **Use Loguru**, not standard logging
2. **Log at appropriate levels** (debug, info, warning, error)
3. **Include context** in log messages
4. **Don't log sensitive data** (API keys, credentials)

### Error Handling

1. **Use try/except** for external calls (APIs, file I/O)
2. **Log errors** with full context
3. **Provide fallback values** when possible
4. **Fail gracefully** - don't crash the entire flow

## Troubleshooting

### Issue: Renderer not found

**Symptom**: `GenericRenderer` used instead of crew-specific renderer

**Solution**: 
1. Check renderer exists in `template_renderers/`
2. Verify class name follows convention: `{CrewName}Renderer`
3. Check RendererFactory registration

### Issue: BeautifulSoup type errors

**Symptom**: Mypy errors about AttributeValueList, PageElement unions

**Solutions**:
- Use `tag.attrs["class"] = [...]` instead of `class_="..."`
- Add type guards for union types
- Use `# type: ignore` for complex BeautifulSoup patterns

### Issue: HTML rendering fails

**Symptom**: HTML file empty or malformed

**Solutions**:
1. Verify Pydantic model → `model.model_dump()` produces correct structure
2. Check renderer `render()` returns valid HTML string
3. Validate template placeholders match TemplateManager replacements
4. Check output directory exists

### Issue: Path not found

**Symptom**: FileNotFoundError when reading/writing files

**Solutions**:
1. Use `ensure_output_directory()` before writing
2. Use `resolve_output_path()` for consistent path resolution
3. Check paths are project-relative, not absolute
4. Verify file exists before reading

### Issue: Extractor returns wrong structure

**Symptom**: Renderer fails because data structure doesn't match

**Solutions**:
1. Align extractor output with renderer input expectations
2. Document expected data structure in both extractor and renderer
3. Add validation in extractor
4. Use Pydantic models to enforce structure

## Related Documentation

- **Main CLAUDE.md**: Root-level comprehensive guide
- **Crews**: `src/epic_news/crews/CLAUDE.md` (crew patterns)
- **Tools**: `src/epic_news/tools/CLAUDE.md` (tool usage)
- **Rendering Architecture**: `docs/reference/RENDERING_ARCHITECTURE.md`
- **Development Guide**: `docs/1_DEVELOPMENT_GUIDE.md`

## Key Takeaways

1. **HTML rendering**: Use TemplateManager + crew-specific renderers extending BaseRenderer
2. **BeautifulSoup**: Use `tag.attrs["class"] = [...]` for CSS classes
3. **Content extraction**: Separate extractors from renderers for clean architecture
4. **Observability**: Use Tracer, Dashboard, HallucinationGuard for debugging
5. **Path management**: Centralized via `directory_utils` and `path_utils`
6. **Logging**: Use Loguru, not standard logging
7. **Helper utilities**: Rich set of utilities for common tasks (string, file, HTTP, data)
8. **Testing**: Use debug utilities for validation and comparison
9. **Error handling**: Graceful degradation with logging
10. **Factory pattern**: Use factory functions for consistency across system
