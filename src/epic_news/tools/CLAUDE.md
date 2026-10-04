# Tools Directory Context

This directory contains all custom tools and tool factories for the Epic News system. Tools extend agent capabilities with web scraping, data retrieval, API integration, and specialized processing.

## Directory Contents

**Note (post tools-migration cleanup)**: most standalone per-provider tools
(web search/scrape, finance/crypto quotes, GitHub, email/OSINT lookup) now live
in the sibling `crewai_custom_tools` package, e.g.
`from crewai_custom_tools import ScrapeNinjaTool, PerplexitySearchTool`. The files
below are what remains in `src/epic_news/tools/`.

### Tool Categories

**Factories** (select/assemble tools by provider or feature flag):
- web_tools.py — web search/scrape/YouTube/PDF tool bundles
- finance_tools.py — Yahoo Finance / stock / crypto / ETF tool bundles
- github_tools.py, location_tools.py, report_tools.py — per-domain factory functions
- scraper_factory.py — scraper provider selection (delegates to `crewai_custom_tools`)

**Data & Reporting** (kept in-repo):
- data_centric_tools.py (MetricsCalculatorTool, KPITrackerTool, DataVisualizationTool, StructuredReportTool; `get_data_centric_tools()`)
- html_to_pdf_tool.py (HtmlToPdfTool), render_report_tool.py (RenderReportTool)

**Shared**:
- _json_utils.py (JSON-output helpers: `ensure_json_str`, etc.)

## Tool Implementation Patterns

### Factory Pattern (Centralized Tool Management)

Tools are organized via factory functions for centralized configuration and graceful degradation:

```python
# src/epic_news/tools/web_tools.py
def get_search_tools():
    return [PerplexitySearchTool()]
```

**Key factories**:
- `web_tools`: `get_search_tools()`, `get_news_tools()`, `get_scrape_tools()`, `get_youtube_tools()`, `get_website_search_tools()`, `get_github_tools()`, `get_pdf_tools()`, `get_all_web_tools()`
- `finance_tools`: `get_yahoo_finance_tools()`, `get_stock_research_tools()`, `get_crypto_research_tools()`
- `github_tools.get_github_tools()` - GitHub integrations
- `location_tools.get_location_tools()` - Geoapify place search
- `report_tools.get_report_tools()` - RenderReportTool (+ HtmlToPdfTool when available)
- `data_centric_tools.get_data_centric_tools()` - metrics/KPI/report tools

### Scraper Factory (Provider Abstraction)

**Location**: `src/epic_news/tools/scraper_factory.py`

**Purpose**: Centralized web scraper selection (ScrapeNinja vs Firecrawl)

```python
from epic_news.tools.scraper_factory import get_scraper

# Returns tool based on WEB_SCRAPER_PROVIDER env var
scraper = get_scraper()  # Default: ScrapeNinjaTool
result_json = scraper.run({"url": "https://example.com"})
```

**Environment variables**:
- `WEB_SCRAPER_PROVIDER`: "scrapeninja" (default) or "firecrawl"
- `RAPIDAPI_KEY`: Required for ScrapeNinja
- `FIRECRAWL_API_KEY`: Required for Firecrawl

**Benefits**:
- Switch scrapers without code changes
- Consistent interface across providers
- Fallback support for API limits

### JSON Output Standardization

**ALL tool `_run()` methods MUST return JSON strings** parseable by `json.loads()`.

**Helper module**: `src/epic_news/tools/_json_utils.py`

```python
from epic_news.tools._json_utils import ensure_json_str

def _run(self, **kwargs):
    result = self._fetch_data(kwargs)
    
    # ✅ CORRECT - Always return JSON string
    return ensure_json_str(result)
    
    # ❌ WRONG - Don't return raw objects
    # return result
```

**Why**: CrewAI agents expect JSON for structured parsing and inter-task communication.

### Custom Tool Base Class Pattern

```python
from crewai.tools import BaseTool

class MyCustomTool(BaseTool):
    name: str = "My Custom Tool"
    description: str = "What this tool does"
    
    def _run(self, **kwargs) -> str:
        \"\"\"
        Execute tool logic.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            str: JSON string of results
        \"\"\"
        # Implementation
        result = self._fetch_data(kwargs)
        return ensure_json_str(result)
```

**Key requirements**:
1. Inherit from `BaseTool`
2. Define `name` and `description` class attributes
3. Implement `_run()` method
4. Return JSON string from `_run()`

### API Key Management

**Security rules**:
- ALL API keys stored in `.env` file, NEVER in code
- Validate keys before tool initialization
- Graceful degradation if keys missing

**Naming convention**: `SERVICE_NAME_API_KEY`

```bash
# .env
TAVILY_API_KEY=tvly-xxxxx
SERPER_API_KEY=xxxxx
FIRECRAWL_API_KEY=fc-xxxxx
RAPIDAPI_KEY=rapi-xxxxx
ALPHA_VANTAGE_API_KEY=xxxxx
ACCUWEATHER_API_KEY=xxxxx
HUNTER_API_KEY=xxxxx
AIRTABLE_API_KEY=xxxxx
TODOIST_API_KEY=xxxxx
```

**Validation pattern**:
```python
def get_my_tool():
    api_key = os.getenv("MY_SERVICE_API_KEY")
    if not api_key:
        logger.warning("MY_SERVICE_API_KEY not found, tool unavailable")
        return []
    return [MyServiceTool(api_key=api_key)]
```

## Tool Usage in Crews

### Assigning Tools to Agents

**CRITICAL**: Tools MUST be assigned in Python code, not in YAML files.

```python
from epic_news.tools.web_tools import get_search_tools
from epic_news.tools.finance_tools import get_stock_research_tools

@CrewBase
class MyCrew:
    def __init__(self):
        self.search_tools = get_search_tools()
        self.finance_tools = get_stock_research_tools()
    
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.search_tools,  # ✅ CORRECT - Assigned here
            llm=LLMConfig.get_openrouter_llm(task_type="default"),
            max_iter=LLMConfig.get_max_iter(),
            verbose=True,
        )
```

**Don't do this**:
```yaml
# agents.yaml - ❌ WRONG
researcher:
  role: Research Specialist
  tools:  # DON'T ASSIGN TOOLS IN YAML
    - TavilyTool
```

**Why**: CrewBase resolves YAML `tools:` names only against `@tool`-decorated methods on the crew class; any other name raises `KeyError`. The project keeps tools in Python.

### Tool Selection by Crew Type

Different crews need different tool combinations:

**Research Crews** (deep_research, company_profiler):
- `HybridSearchTool` (Perplexity → Brave → Serper fallback)
- Wikipedia (MCP, deep_research and pestel)
- Scraper factory

**Financial Crews** (fin_daily):
- Yahoo Finance tools, AlphaVantage, Kraken (via `finance_tools`)
- Exchange rate tool

**Content Crews** (news_daily, rss_weekly):
- `get_news_tools()` (Perplexity), `UnifiedRssTool`
- Web scraper factory

**Business Crews** (sales_prospecting, hr_intelligence):
- GitHub tools (tech companies)
- Hunter.io (email finding, from `crewai_custom_tools`)

**Planning Crews** (holiday_planner, menu_designer):
- Location tools (Geoapify)
- Weather tools (AccuWeather)
- Wikipedia (destination info)

## Tool Development Guidelines

### Creating a New Tool

1. **Choose tool type**:
   - Standalone: Direct API integration
   - Factory: Group of related tools
   - Wrapper: Enhance existing tool

2. **Implement tool class**:
   ```python
   from crewai.tools import BaseTool
   from epic_news.tools._json_utils import ensure_json_str
   
   class MyNewTool(BaseTool):
       name: str = "My New Tool"
       description: str = "Clear description of what it does"
       
       def _run(self, param1: str, param2: str) -> str:
           # Implementation
           result = self._process(param1, param2)
           return ensure_json_str(result)
   ```

3. **Add to factory** (if applicable):
   ```python
   def get_my_tools():
       return [MyNewTool(), MyOtherTool()]
   ```

4. **Document it**: Update `docs/reference/tools.md`

5. **Write tests**:
   ```python
   def test_my_new_tool():
       tool = MyNewTool()
       result = tool.run(param1="test", param2="value")
       
       # Verify JSON output
       parsed = json.loads(result)
       assert "expected_key" in parsed
   ```

### Testing Requirements

**JSON output validation**:
```bash
uv run pytest tests/tools/test_json_outputs.py
```

**External APIs**:
- Mock external APIs in tests
- No live network calls in test suite

**Run all tool tests**:
```bash
uv run pytest tests/tools/ -v
```

## Common Tool Patterns

### 1. Search Tools

Search tools now live in `crewai_custom_tools` (the `search_base.py` base
class was removed from this directory in the tools migration). Import the
concrete tool you need, e.g. `from crewai_custom_tools import TavilyTool`,
rather than subclassing a local base class.

### 2. Financial Data Tools

Pattern: Fetch, parse, return JSON

```python
class MyFinanceTool(BaseTool):
    name = "Finance Data Fetcher"
    
    def _run(self, ticker: str) -> str:
        # Fetch from API
        data = self._fetch(ticker)
        
        # Parse and structure
        result = {
            "ticker": ticker,
            "price": data["price"],
            "change": data["change"],
        }
        
        return ensure_json_str(result)
```

### 3. Web Scraping Tools

Use scraper factory for consistency:

```python
from epic_news.tools.scraper_factory import get_scraper

class MyScrapingTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.scraper = get_scraper()
    
    def _run(self, url: str) -> str:
        result = self.scraper.run({"url": url})
        return result  # Already JSON from scraper
```

## Performance & Optimization

### Caching

`cache_manager.py` was removed from this directory in the tools migration
(its only consumers were migrated/deleted tools). Tools that still need
caching should implement it locally or rely on caching provided by
`crewai_custom_tools`.

**When to cache**:
- Expensive API calls
- Rate-limited endpoints
- Frequently repeated queries
- Static data (company info, historical prices)

**When NOT to cache**:
- Real-time data (stock prices, news)
- User-specific data
- Rapidly changing information

### Async Execution

For independent, I/O-bound operations:

```python
import asyncio
import httpx

async def _run_async(self, urls: list[str]) -> str:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
    
    results = [r.json() for r in responses]
    return ensure_json_str(results)
```

## Troubleshooting

### Issue: Tool returns non-JSON output

**Symptom**: Agent fails to parse tool result

**Solution**: Wrap output with `ensure_json_str()`

```python
from epic_news.tools._json_utils import ensure_json_str

def _run(self, param: str) -> str:
    result = self._process(param)
    return ensure_json_str(result)  # Always return JSON string
```

### Issue: API key not found

**Symptom**: Tool initialization fails or returns empty results

**Solution**: Check `.env` file and factory graceful degradation

```python
def get_my_tools():
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        logger.warning("MY_API_KEY not set, tool unavailable")
        return []  # Graceful degradation
    return [MyTool(api_key=api_key)]
```

### Issue: Rate limit exceeded

**Symptom**: 429 errors from API

**Solutions**:
1. Implement caching
2. Add request delays
3. Use rate-limited queue
4. Switch to alternative provider via factory

### Issue: Scraper fails on dynamic content

**Symptom**: Empty or incomplete page content

**Solution**: Switch scraper provider

```bash
# .env - Switch from ScrapeNinja to Firecrawl
WEB_SCRAPER_PROVIDER=firecrawl
```

### Issue: Tools not available to agent

**Symptom**: Agent says "I don't have access to that tool"

**Solution**: Verify tools assigned in Python code, not YAML

```python
@agent
def my_agent(self) -> Agent:
    return Agent(
        tools=self.my_tools,  # ✅ Must assign here
    )
```

## Tool API Keys Reference

### Required for Basic Operation

```bash
# Web Search (at least one recommended)
TAVILY_API_KEY=         # Advanced search with filtering
SERPER_API_KEY=         # Google search via Serper.dev

# Web Scraping (at least one required)
RAPIDAPI_KEY=           # For ScrapeNinja (default)
FIRECRAWL_API_KEY=      # Alternative scraper
```

### Optional by Feature

```bash
# Financial Data
ALPHA_VANTAGE_API_KEY=  # Fundamental company data

# Location & Weather
ACCUWEATHER_API_KEY=    # Weather forecasts
GEOAPIFY_API_KEY=       # Place search (uses free tier if not set)

# Business Intelligence
HUNTER_API_KEY=         # Email finding
GITHUB_TOKEN=           # GitHub API (uses public API if not set)

# Productivity
AIRTABLE_API_KEY=       # Airtable integration
TODOIST_API_KEY=        # Task management

# Specialized
GOOGLE_API_KEY=         # Fact checking
BROWSERBASE_API_KEY=    # Browser automation
```

## Related Documentation

- **Main CLAUDE.md**: Root-level comprehensive guide
- **Tools Reference**: `docs/reference/tools.md` (complete tool reference)
- **Crews**: `src/epic_news/crews/CLAUDE.md` (crew patterns and tool usage)
- **Utils**: `src/epic_news/utils/CLAUDE.md` (utility functions)
- **Development Setup**: `docs/how-to/development_setup.md`

## Key Takeaways

1. **Factory pattern**: Centralize tool management for flexibility
2. **JSON outputs**: ALL `_run()` methods return JSON strings
3. **API keys**: Store in `.env`, validate before use, graceful degradation
4. **Tool assignment**: In Python code (agent methods), NEVER in YAML
5. **Scraper factory**: Abstract provider selection for easy switching
6. **Testing**: Mock external APIs, verify JSON outputs
7. **Performance**: Cache expensive calls
