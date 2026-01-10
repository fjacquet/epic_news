# Tools Directory Context

This directory contains all custom tools and tool factories for the Epic News system. Tools extend agent capabilities with web scraping, data retrieval, API integration, and specialized processing.

## Directory Contents (62 Tools)

### Tool Categories

**Search & Web** (14 tools):
- brave_search_tool.py, serp api_tool.py, tavily_tool.py
- web_search_factory.py (centralizes search provider selection)
- web_tools.py (factory for web-related tools)
- scraper_factory.py, scrape_ninja_tool.py, firecrawl_tool.py
- batch_article_scraper_tool.py
- search_base.py (base class for search tools)

**Financial** (12 tools):
- Yahoo Finance: yahoo_finance_*.py (news, ticker, company, history, etf_holdings)
- alpha_vantage_tool.py
- CoinMarketCap: coinmarketcap_*.py (list, info, news, historical)
- kraken_api_tool.py
- exchange_rate_tool.py
- finance_tools.py (factory)

**Wikipedia** (3 tools):
- wikipedia_search_tool.py
- wikipedia_article_tool.py
- wikipedia_processing_tool.py

**RSS & Feeds** (3 tools):
- rss_feed_tool.py
- rss_feed_parser_tool.py
- unified_rss_tool.py
- opml_parser_tool.py

**GitHub** (4 tools):
- github_tools.py (factory)
- github_base.py
- github_search_tool.py
- github_org_tool.py

**Location & Weather** (3 tools):
- location_tools.py (factory)
- geoapify_places_tool.py
- accuweather_tool.py

**Email** (3 tools):
- email_base.py
- email_search.py
- serper_email_search_tool.py

**RAG & Data** (4 tools):
- rag_tools.py (factory)
- save_to_rag_tool.py
- hybrid_search_tool.py
- data_centric_tools.py

**HTML & Reporting** (5 tools):
- html_generator_tool.py
- html_to_pdf_tool.py
- render_report_tool.py
- reporting_tool.py
- report_tools.py (factory)
- universal_report_tool.py

**Miscellaneous** (11 tools):
- airtable_tool.py
- todoist_tool.py
- fact_checking_factory.py
- google_fact_check_tool.py
- hunter_io_tool.py
- tech_stack_tool.py
- utility_tools.py
- custom_tool.py
- cache_manager.py
- _json_utils.py

## Tool Implementation Patterns

### Factory Pattern (Centralized Tool Management)

Tools are organized via factory functions for centralized configuration and graceful degradation:

```python
# src/epic_news/tools/web_tools.py
def get_web_search_tools():
    \"\"\"Returns all web search tools with proper API key handling.\"\"\"
    tools = []
    
    if os.getenv("TAVILY_API_KEY"):
        tools.append(TavilyTool())
    
    if os.getenv("SERPER_API_KEY"):
        tools.append(SerperApiTool())
    
    # Graceful degradation: return what's available
    return tools
```

**Key factories**:
- `get_web_search_tools()` - Web search providers
- `get_github_tools()` - GitHub integrations
- `get_finance_tools()` - Financial data tools
- `get_location_tools()` - Geographic data tools
- `get_rag_tools()` - RAG/vector tools
- `get_report_tools()` - HTML/PDF generation

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
from crewai_tools import BaseTool

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
COINMARKETCAP_API_KEY=xxxxx
ACCUWEATHER_API_KEY=xxxxx
HUNTER_IO_API_KEY=xxxxx
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

**CRITICAL**: Tools MUST be assigned in Python code, NEVER in YAML files.

```python
from epic_news.tools.web_tools import get_web_search_tools
from epic_news.tools.finance_tools import get_finance_tools

@CrewBase
class MyCrew:
    def __init__(self):
        self.search_tools = get_web_search_tools()
        self.finance_tools = get_finance_tools()
    
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.search_tools,  # ✅ CORRECT - Assigned here
            llm=LLMConfig.get_openrouter_llm(),
            verbose=True,
        )
```

**NEVER do this**:
```yaml
# agents.yaml - ❌ WRONG
researcher:
  role: Research Specialist
  tools:  # DON'T ASSIGN TOOLS IN YAML
    - TavilyTool
```

**Why**: Hybrid YAML/code tool configuration causes `KeyError` exceptions.

### Tool Selection by Crew Type

Different crews need different tool combinations:

**Research Crews** (deep_research, company_profiler):
- Web search: Tavily, Serper, Brave
- Wikipedia tools
- Scraper factory

**Financial Crews** (fin_daily, company_news):
- Yahoo Finance tools
- AlphaVantage
- CoinMarketCap
- Exchange rate tool

**Content Crews** (news_daily, rss_weekly):
- RSS tools
- Batch article scraper
- Web scraper factory

**Business Crews** (sales_prospecting, hr_intelligence):
- Email search tools
- GitHub tools (tech companies)
- Hunter.io (email finding)

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
   from crewai_tools import BaseTool
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

4. **Document in tools handbook**: Update `docs/2_TOOLS_HANDBOOK.md`

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

**HTTP resilience** (for API tools):
- Use `httpx` with retries via `tenacity`
- Mock external APIs in tests
- No live network calls in test suite

**Run all tool tests**:
```bash
uv run pytest tests/tools/ -v
```

## Common Tool Patterns

### 1. Search Tools

Base class: `src/epic_news/tools/search_base.py`

```python
from epic_news.tools.search_base import SearchBase

class MySearchTool(SearchBase):
    name = "My Search"
    description = "Searches my data source"
    
    def _execute_search(self, query: str) -> dict:
        # Implementation
        return {"results": [...]}
```

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

### 4. RAG Tools

Short-term scratchpad pattern (not permanent storage):

```python
from epic_news.tools.save_to_rag_tool import SaveToRagTool

# In crew __init__
self.rag_tool = SaveToRagTool()

# In agent
@agent
def researcher(self) -> Agent:
    return Agent(
        tools=[SearchTool(), self.rag_tool],
    )

# In task description
\"\"\"
1. Search for information
2. Save findings to RAG using SaveToRagTool
3. Use findings in next task
\"\"\"
```

**Important**: RAG is used as temporary storage within a single crew execution, NOT as a persistent knowledge base.

## Performance & Optimization

### Caching

**Cache manager**: `src/epic_news/tools/cache_manager.py`

```python
from epic_news.tools.cache_manager import CacheManager

cache = CacheManager(ttl=3600)  # 1 hour

def _run(self, query: str) -> str:
    # Check cache first
    cached = cache.get(query)
    if cached:
        return cached
    
    # Fetch and cache
    result = self._fetch(query)
    cache.set(query, result)
    return result
```

**When to cache**:
- Expensive API calls
- Rate-limited endpoints
- Frequently repeated queries
- Static data (company info, historical prices)

**When NOT to cache**:
- Real-time data (stock prices, news)
- User-specific data
- Rapidly changing information

### HTTP Resilience

Use `httpx` with `tenacity` for retries:

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_with_retry(self, url: str):
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
```

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
COINMARKETCAP_API_KEY=  # Cryptocurrency data

# Location & Weather
ACCUWEATHER_API_KEY=    # Weather forecasts
GEOAPIFY_API_KEY=       # Place search (uses free tier if not set)

# Business Intelligence
HUNTER_IO_API_KEY=      # Email finding
GITHUB_TOKEN=           # GitHub API (uses public API if not set)

# Productivity
AIRTABLE_API_KEY=       # Airtable integration
TODOIST_API_KEY=        # Task management

# Specialized
GOOGLE_API_KEY=         # Fact checking
EXA_API_KEY=            # Specialized search
BROWSERBASE_API_KEY=    # Browser automation
```

## Related Documentation

- **Main CLAUDE.md**: Root-level comprehensive guide
- **Tools Handbook**: `docs/2_TOOLS_HANDBOOK.md` (complete tool reference)
- **Crews**: `src/epic_news/crews/CLAUDE.md` (crew patterns and tool usage)
- **Utils**: `src/epic_news/utils/CLAUDE.md` (utility functions)
- **Development Guide**: `docs/1_DEVELOPMENT_GUIDE.md`

## Key Takeaways

1. **Factory pattern**: Centralize tool management for flexibility
2. **JSON outputs**: ALL `_run()` methods return JSON strings
3. **API keys**: Store in `.env`, validate before use, graceful degradation
4. **Tool assignment**: In Python code (agent methods), NEVER in YAML
5. **Scraper factory**: Abstract provider selection for easy switching
6. **Testing**: Mock external APIs, verify JSON outputs
7. **Performance**: Cache expensive calls, use retries for HTTP requests
8. **RAG usage**: Temporary scratchpad within execution, not permanent storage
