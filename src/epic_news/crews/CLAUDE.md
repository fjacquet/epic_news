# Crews Directory Context

This directory contains all specialized crews in the Epic News system. Each crew is a self-contained unit with agents, tasks, and optional Pydantic models for structured output.

## Directory Structure

Each crew follows a standard pattern:

```
crew_name/
├── config/
│   ├── agents.yaml      # Agent definitions (role, goal, backstory)
│   └── tasks.yaml       # Task definitions
├── crew_name_crew.py    # Python implementation with @agent, @task, @crew decorators
└── (optional models)    # Pydantic models in src/epic_news/models/crews/
```

## All Available Crews (24)

### Content Generation

- **poem** - Generates poetry in various styles (simplest crew example)
- **news_daily** - Daily news aggregation and analysis
- **company_news** - Company-specific news research
- **rss_weekly** - Weekly RSS feed digest
- **saint_daily** - Daily saint information and spiritual content

### Research & Analysis

- **deep_research** - Academic-level deep research with quantitative analysis
- **company_profiler** - Company profiling and business intelligence
- **information_extraction** - Structured data extraction from sources
- **cross_reference_report** - Cross-referencing multiple sources
- **library** - Book research and recommendations
- **legal_analysis** - Legal document analysis
- **tech_stack** - Technology stack analysis
- **pestel** - PESTEL analysis (6 dimension researchers + reporter)

### Planning & Recommendations

- **cooking** - Recipe generation and meal planning
- **menu_designer** - Weekly menu planning with shopping lists
- **holiday_planner** - Travel and holiday planning
- **shopping_advisor** - Product research and shopping recommendations
- **meeting_prep** - Meeting preparation and briefings

### Business & HR

- **sales_prospecting** - Sales lead research and prospecting
- **hr_intelligence** - HR analytics and workforce insights
- **web_presence** - Website and online presence analysis

### Financial

- **fin_daily** - Daily financial analysis and market insights

### Technical

- **geospatial_analysis** - Geographic data analysis
- **classify** - Content classification and routing

Routing itself is done by `ReceptionFlow` in `src/epic_news/main.py` (there is no reception crew), and report emails are sent by `epic_news.utils.email_sender` (there is no post crew).

## Crew Implementation Patterns

### Standard CrewBase Pattern

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyCrew:
    """My crew description"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        # Initialize tools here
        self.my_tools = [...]

    @agent
    def my_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["my_agent"],
            tools=self.my_tools,  # ALWAYS assign tools in code, not in YAML
            llm=LLMConfig.get_openrouter_llm(task_type="default"),  # timeout lives on the LLM
            max_iter=LLMConfig.get_max_iter(),  # Agent field (Crew has no max_iter)
            verbose=True,
        )

    @task
    def my_task(self) -> Task:
        return Task(
            config=self.tasks_config["my_task"],
            agent=self.my_agent(),
            output_pydantic=MyPydanticModel,  # For structured output
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
```

CrewAI silently drops unknown keyword arguments. `llm_timeout=` (any object) and `Crew(max_iter=...)` are not fields and have no effect; don't add them, and don't silence `call-arg` errors with `# type: ignore`. `tests/crews/test_constructor_kwargs.py` fails on any undeclared `Agent`/`Task`/`Crew` kwarg, and `tests/crews/test_agent_settings_contract.py` checks every built agent (LLM timeout, `max_iter`, no duplicate tools, no `FileReadTool` next to web tools). See ADR-014.

Pass the agent itself to `Task(agent=self.my_agent())`, never `agent.copy()`: CrewAI's `LLM.__copy__` drops `timeout`.

**Tool hygiene**: give each agent only the tools its tasks use. An agent with web search/scrape tools must not also hold crewai's unscoped `FileReadTool`; use `OutputFileReadTool` (`tools/output_file_read_tool.py`, scoped to `output/` by default, `root=` to change it).

### MCP Tools (CrewBase-managed)

```python
from epic_news.config.mcp_config import MCPConfig, get_mcp_tools_or_empty

@CrewBase
class MyCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    mcp_server_params = MCPConfig.get_wikipedia_mcp()

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=[HybridSearchTool(), *get_mcp_tools_or_empty(self)],  # one shared adapter
            llm=LLMConfig.get_openrouter_llm(task_type="long"),
            max_iter=LLMConfig.get_max_iter(),
        )
```

- `get_mcp_tools_or_empty(self)` wraps CrewBase's `get_mcp_tools()`: if the server cannot start it logs a warning and returns `[]`, and remembers the failure so the other agents don't retry.
- CrewBase stops the adapter only after a **successful** kickoff. The flow must call `close_mcp(crew)` in a `finally` (see `generate_deep_research` / `generate_pestel` in `main.py`):

```python
crew = MyCrew()
try:
    output = kickoff_flow(crew, inputs)
finally:
    close_mcp(crew)  # safe after CrewBase's own stop, safe to call twice
```

### Two-Agent Pattern (Research + Tool-Free Reporting)

**Why**: `output_pydantic` already keeps tool action traces out of the structured result. The split is kept so the reporting step runs with no tools: it only formats the research context into the Pydantic model.

**Pattern**: Separate research from reporting.

```python
@agent
def researcher(self) -> Agent:
    return Agent(
        config=self.agents_config["researcher"],
        tools=[WikipediaTool(), SearchTool()],  # Has tools
        # No output_file
    )

@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # NO TOOLS: formatting only
        output_file="output/report.html",
    )

@task
def research_task(self) -> Task:
    return Task(
        config=self.tasks_config["research_task"],
        agent=self.researcher(),
    )

@task
def reporting_task(self) -> Task:
    return Task(
        config=self.tasks_config["reporting_task"],
        agent=self.reporter(),
        context=[self.research_task()],  # Gets data from research
    )
```

**Examples using this pattern**: library, company_profiler, holiday_planner

### Tool Assignment Rules

**CRITICAL**: Assign tools programmatically. CrewBase resolves a YAML `tools:` entry only by name against `@tool`-decorated methods on the crew class; any other name raises `KeyError`. The project does not use `@tool` methods, so keep tools in Python.

```python
# ✅ CORRECT
@agent
def my_agent(self) -> Agent:
    return Agent(
        config=self.agents_config["my_agent"],
        tools=[SearchTool(), WikipediaTool()],  # Assigned here
    )

# ❌ WRONG - KeyError (no matching @tool method)
# agents.yaml:
# my_agent:
#   tools:
#     - SearchTool  # Don't do this
```

### Pydantic Models

All Pydantic models used with CrewAI **support modern Python 3.13 syntax** (CrewAI 1.8.0+):

```python
# ✅ RECOMMENDED - Modern Python 3.13 syntax
field: str | None = None
field: str | int = "default"

# ✅ Also works - Legacy syntax (not required)
from typing import Union, Optional
field: Optional[str] = None
field: Union[str, int] = "default"
```

**Model Location**: `src/epic_news/models/crews/<crew_name>.py`

### LLM Configuration

Always use centralized `LLMConfig`:

```python
from epic_news.config.llm_config import LLMConfig

llm=LLMConfig.get_openrouter_llm(task_type="default"),  # or "quick", "long"
max_iter=LLMConfig.get_max_iter(),
```

**NEVER** hardcode model names or timeouts, and never pass `llm_timeout=` (ignored by CrewAI).

### Async Tasks (`async_execution=True`)

Only crews listed in `ASYNC_ALLOWED` (`tests/crews/test_async_agent_isolation.py`: PESTEL, NewsDaily) may run tasks async; all others stay sequential.

- Give each async task its own agent by calling the agent factory again (e.g. `agent=self._new_researcher()`), never `Agent.copy()`: CrewAI's `LLM.__copy__` drops the timeout (ADR-014).
- Register task-only agents in `Crew(agents=...)` so the ADR-014 contract tests see them (see `news_daily.py`).
- Concurrency is bounded by the process-wide LLM cap (`LLM_MAX_CONCURRENCY`, default 3).

## Crew Execution Flow

1. **ReceptionFlow routes request** → `generate_<crew_name>()` method in `main.py`
2. **Kickoff with inputs** → `kickoff_flow(MyCrew(), inputs)` (calls `.crew().kickoff(inputs=...)` with retries)
3. **Result parsing** → `load_or_parse_model(json_path, MyModel, output, inputs, label)`
4. **Rendering** → `render_and_write_html("MY_CREW", model, html_path)`, wrapped in `emit_report(...)` when the crew also supports DOCX

**Example from main.py** (simplified):

```python
output = kickoff_flow(PoemCrew(), inputs)
dump_crewai_state(output, "POEM")
poem_model = load_or_parse_model(self.state.output_file, PoemJSONOutput, output, inputs, "poem")
render_and_write_html("POEM", poem_model, html_file)
```

## Common Crew Patterns by Type

### Simple Single-Agent Crews

- **poem** (1 agent, 1 task, simplest example)
- **classify** (classification only)
- **saint_daily** (content retrieval)
- **cooking** (1 agent, 1 task returning a `PaprikaRecipe`; YAML/JSON exports written in Python by `utils/recipe_export.py`)

### Two-Agent Research + Report

- **library** (researcher + reporter)
- **company_profiler** (profiler + reporter)
- **holiday_planner** (researcher + reporter)

### Multi-Agent Specialized

- **deep_research** (4 agents: planner, collector, analyzer, quality_assessor)
- **sales_prospecting** (3+ agents: researcher, profiler, strategist)
- **hr_intelligence** (multi-stage analysis)

### Financial Analysis

- **fin_daily** (market analyst + technical analyst)
- **company_news** (news collector + analyst)

### Content Aggregation

- **news_daily** (scraper + aggregator + analyzer)
- **rss_weekly** (feed parser + summarizer)

## Tool Categories by Crew Type

### Research Crews

- `HybridSearchTool` (Perplexity → Brave → Serper fallback), `PerplexitySearchTool` via `web_tools.get_search_tools()`
- Wikipedia (via MCP: `deep_research`, `pestel`)

### Financial Crews

- `get_stock_research_tools()`, `get_crypto_research_tools()`, `get_yahoo_finance_tools()` (`tools/finance_tools.py`)
- ExchangeRateTool

### Content Crews

- `scraper_factory.get_scraper()` (ScrapeNinja by default, FireCrawl via `WEB_SCRAPER_PROVIDER=firecrawl`)

## HTML Rendering

Each crew that generates HTML reports must:

1. **Define Pydantic model** for structured output
2. **Create renderer** in `src/epic_news/utils/html/template_renderers/`
3. **Register it** in `RendererFactory._RENDERER_MAP` under the crew key
4. **Render from the flow** with `render_and_write_html("MY_CREW", model, html_path)` (uses `TemplateManager().render_report(selected_crew=..., content_data=...)`)

See `docs/reference/RENDERING_ARCHITECTURE.md` for complete guide.

## Creating a New Crew

Follow the step-by-step tutorial: `docs/tutorials/getting_started.md`

**Quick checklist**:

1. Create crew directory: `src/epic_news/crews/<crew_name>/`
2. Add `config/agents.yaml` and `config/tasks.yaml`
3. Create `<crew_name>_crew.py` with @CrewBase
4. Define Pydantic model in `src/epic_news/models/crews/<crew_name>.py`
5. Create HTML renderer (if needed)
6. Add `generate_<crew_name>()` method to ReceptionFlow in `main.py`
7. Write structure tests in `tests/crews/test_<crew_name>_structure.py`

## Common Issues

### JSON Escaping Errors

**Symptom**: `pydantic_core.ValidationError: Invalid JSON: invalid escape`

**Solution**: Add `system_template` to reporter agent:

```python
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],
        system_template="""You are a JSON formatting expert.

        CRITICAL: Escape all special characters in JSON strings:
        - Use \\" for quotes inside strings
        - Use \\\\ for backslashes
        - French apostrophes MUST be escaped: "l'amour" → "l\\'amour"

        Output ONLY valid JSON with properly escaped strings."""
    )
```

See `docs/troubleshooting/COMMON_ERRORS.md` for complete troubleshooting guide.

### Tool KeyError Exceptions

**Symptom**: `KeyError: '<ToolName>'` when the crew class is built

**Cause**: A YAML `tools:` entry with no matching `@tool` method on the crew class.

**Solution**: Remove tools from YAML, assign in Python code only.

### AttributeError with Union Types

**Symptom**: `AttributeError: 'UnionType' object has no attribute '__origin__'`

**Solution**: This error occurred in CrewAI < 1.0.0. Since CrewAI 1.8.0+, modern union syntax (`X | None`) is fully supported. If you encounter this error, upgrade CrewAI: `uv add crewai>=1.8.0`

## Testing Patterns

Each crew should have:

1. **Structure tests** - Verify agents, tasks, crew exist
2. **Configuration tests** - Validate YAML configs
3. **Integration tests** - Test kickoff with mock inputs (optional)

**Example structure test**:

```python
def test_poem_crew_structure():
    crew = PoemCrew()
    assert hasattr(crew, "poem_writer")
    assert hasattr(crew, "generate_poem_task")
    assert hasattr(crew, "crew")
```

## Performance Tuning

### Timeout Configuration

Set on the LLM via `LLMConfig.get_openrouter_llm(task_type=...)`:

- **Quick tasks** (cooking, classification): `task_type="quick"` (120s)
- **Standard tasks** (most crews): `task_type="default"` (300s)
- **Complex tasks** (deep_research): `task_type="long"` (600s)

### Iteration Limits

`max_iter` is an **Agent** field (CrewAI default 25). Every agent sets `max_iter=LLMConfig.get_max_iter()` (`CREW_MAX_ITER`, default 15). The only override is fin_daily's stock analyst (`max_iter=30`, one tool call per portfolio ticker), listed in `MAX_ITER_OVERRIDES` in `tests/crews/test_agent_settings_contract.py`; add new overrides there too.

### Rate Limiting

- Default: `max_rpm=20`
- High-frequency crews: Increase to 30-40

## Reference Documentation

- **Tutorial**: `docs/tutorials/getting_started.md`
- **Troubleshooting**: `docs/troubleshooting/COMMON_ERRORS.md`
- **Rendering**: `docs/reference/RENDERING_ARCHITECTURE.md`
- **Main CLAUDE.md**: Root-level comprehensive guide
- **Tools**: `src/epic_news/tools/CLAUDE.md`
- **Utilities**: `src/epic_news/utils/CLAUDE.md`

## Crew-Specific Notes

### deep_research

- Most complex crew (4 agents, academic standards)
- Uses quantitative analysis with statistical tests
- PhD-level quality thresholds
- Iterative replanning on quality failures

### poem

- Simplest crew (excellent learning example)
- Single agent, single task
- Known issue: French text requires JSON escaping
- See troubleshooting guide for solution

### menu_designer

- Complex weekly planning with shopping list
- Validated by `MenuPlanValidator` (via `services/menu_designer_service.py`)
- Generates structured HTML tables

### fin_daily

- Financial market analysis
- Uses `get_stock_research_tools()` + `get_crypto_research_tools()`
- Technical indicators + sentiment analysis
