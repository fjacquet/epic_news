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

## All Available Crews (25)

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

### Meta

- **reception** - User request classification and crew routing (entry point)
- **post** - Post-processing and notifications

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
            tools=self.my_tools,  # ALWAYS assign tools in code, NEVER in YAML
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("default"),
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
            max_iter=LLMConfig.get_max_iter(),
            max_rpm=LLMConfig.get_max_rpm(),
            verbose=True,
        )
```

### Two-Agent Pattern (For Clean HTML Output)

**Problem**: Agents with tools write action traces to output files.

**Solution**: Separate research from reporting.

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
        tools=[],  # NO TOOLS = Clean output
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

**Examples using this pattern**: library, cooking, company_profiler, holiday_planner

### Tool Assignment Rules

**CRITICAL**: Tools must be assigned programmatically, never in YAML.

```python
# ✅ CORRECT
@agent
def my_agent(self) -> Agent:
    return Agent(
        config=self.agents_config["my_agent"],
        tools=[SearchTool(), WikipediaTool()],  # Assigned here
    )

# ❌ WRONG - Causes KeyError exceptions
# agents.yaml:
# my_agent:
#   tools:
#     - SearchTool  # Don't do this
```

### Pydantic Models

All Pydantic models used with CrewAI must use **legacy Union syntax**:

```python
from typing import Union, Optional

# ✅ CORRECT
field: Optional[str] = None
field: Union[str, int] = "default"

# ❌ WRONG - Causes AttributeError
field: str | None = None
field: str | int = "default"
```

**Model Location**: `src/epic_news/models/crews/<crew_name>.py`

### LLM Configuration

Always use centralized `LLMConfig`:

```python
from epic_news.config.llm_config import LLMConfig

llm=LLMConfig.get_openrouter_llm(),
llm_timeout=LLMConfig.get_timeout("default"),  # or "quick", "long"
```

**NEVER** hardcode model names or timeouts.

## Crew Execution Flow

1. **ReceptionFlow routes request** → `generate_<crew_name>()` method in `main.py`
2. **Crew initialization** → `MyCrew().crew()`
3. **Kickoff with inputs** → `.kickoff(inputs=crew_inputs)`
4. **Result parsing** → `MyModel.model_validate(json.loads(result.raw))`
5. **HTML rendering** → `my_crew_to_html(model, output_path)`

**Example from main.py**:

```python
@listen("or(classify_flow, analyze_flow)")
def generate_poem(self, content_state: ContentState):
    crew_inputs = {"topic": content_state.user_query, "style": "haiku"}

    result = PoemCrew().crew().kickoff(inputs=crew_inputs)

    poem_model = PoemModel.model_validate(json.loads(result.raw))

    poem_to_html(poem_model, html_file="output/poem/poem.html")
```

## Common Crew Patterns by Type

### Simple Single-Agent Crews

- **poem** (1 agent, 1 task, simplest example)
- **classify** (classification only)
- **saint_daily** (content retrieval)

### Two-Agent Research + Report

- **library** (researcher + reporter)
- **cooking** (chef + reporter)
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

- SerperDev, Tavily, BraveSearch
- WikipediaTool (via MCP)
- Perplexity (via MCP)

### Financial Crews

- AlphaVantage, YahooFinance, CoinMarketCap
- ExchangeRateTool

### Content Crews

- ScraperFactory (FireCrawl, Jina, ScrapeNinja)
- BatchArticleScraperTool

### Communication Crews

- Email tools (Gmail via Composio)
- Slack, Discord (via Composio)

### Data Analysis Crews

- Custom analytics tools
- ValidationTools

## HTML Rendering

Each crew that generates HTML reports must:

1. **Define Pydantic model** for structured output
2. **Create renderer** in `src/epic_news/utils/html/template_renderers/`
3. **Create factory function** in `src/epic_news/utils/html/template_renderers/`
4. **Use TemplateManager** for rendering

**Example**:

```python
from epic_news.utils.html.template_manager import TemplateManager

def poem_to_html(poem_model: PoemModel, html_file: str):
    TemplateManager.render_report(
        crew_identifier="poem",
        data=poem_model.model_dump(),
        output_path=html_file,
    )
```

See `docs/reference/RENDERING_ARCHITECTURE.md` for complete guide.

## Creating a New Crew

Follow the step-by-step tutorial: `docs/tutorials/01_YOUR_FIRST_CREW.md`

**Quick checklist**:

1. Create crew directory: `src/epic_news/crews/<crew_name>/`
2. Add `config/agents.yaml` and `config/tasks.yaml`
3. Create `<crew_name>_crew.py` with @CrewBase
4. Define Pydantic model in `src/epic_news/models/crews/<crew_name>.py`
5. Create HTML renderer (if needed)
6. Add `generate_<crew_name>()` method to ReceptionFlow in `main.py`
7. Write structure tests in `tests/structure/test_<crew_name>_structure.py`

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

**Symptom**: `KeyError: 'tools'` when running crew

**Solution**: Remove tools from YAML, assign in Python code only.

### AttributeError with Union Types

**Symptom**: `AttributeError: 'UnionType' object has no attribute '__origin__'`

**Solution**: Use legacy syntax `Optional[X]` instead of `X | None`.

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

- **Quick tasks** (cooking, classification): `LLMConfig.get_timeout("quick")` (120s)
- **Standard tasks** (most crews): `LLMConfig.get_timeout("default")` (300s)
- **Complex tasks** (deep_research): `LLMConfig.get_timeout("long")` (600s)

### Iteration Limits

- **Simple crews**: `max_iter=3`
- **Research crews**: `max_iter=5` (default)
- **Deep analysis**: `max_iter=10`

### Rate Limiting

- Default: `max_rpm=20`
- High-frequency crews: Increase to 30-40

## Reference Documentation

- **Tutorial**: `docs/tutorials/01_YOUR_FIRST_CREW.md`
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

### reception

- Entry point for all user requests
- Classification via classify crew
- Routes to appropriate specialized crew
- Maintains ContentState throughout flow

### poem

- Simplest crew (excellent learning example)
- Single agent, single task
- Known issue: French text requires JSON escaping
- See troubleshooting guide for solution

### menu_designer

- Complex weekly planning with shopping list
- Uses menu_generator utility
- Validates against dietary constraints
- Generates structured HTML tables

### fin_daily

- Financial market analysis
- Uses AlphaVantage + YahooFinance
- Daily execution schedule
- Technical indicators + sentiment analysis
