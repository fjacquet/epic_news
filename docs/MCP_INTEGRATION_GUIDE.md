# MCP Server Integration Guide

## Overview

This project uses **Model Context Protocol (MCP)** servers to enhance crew capabilities with advanced tools and integrations. MCP provides a standardized way to connect AI assistants to external data sources and tools.

## Architecture

```
epic_news/
├── src/epic_news/config/
│   └── mcp_config.py          # MCP server configurations
├── crews/                      # Crews using MCP tools
│   ├── deep_research/         # Uses Wikipedia & Perplexity MCP
│   ├── company_news/          # Uses Perplexity MCP
│   └── news_daily/            # Uses Perplexity MCP
└── docs/
    └── MCP_INTEGRATION_GUIDE.md  # This file
```

## Available MCP Servers

### 1. Perplexity MCP Server
**Purpose**: Advanced web research and reasoning

**Installation**: Automatic via `npx @perplexity-ai/mcp-server`

**Available Tools**:
- `perplexity_search`: Direct web search with real-time results
- `perplexity_ask`: Conversational AI with integrated search
- `perplexity_research`: Deep research using sonar-deep-research model
- `perplexity_reason`: Advanced reasoning capabilities

**Configuration**:
```python
from epic_news.config.mcp_config import MCPConfig

perplexity_config = MCPConfig.get_perplexity_mcp()
# Returns: {
#     "command": "npx",
#     "args": ["@perplexity-ai/mcp-server"],
#     "env": {"PERPLEXITY_API_KEY": "your_key"}
# }
```

**Environment Variables**:
```bash
PERPLEXITY_API_KEY=pplx-your-api-key-here
```

**Use Cases**:
- Deep research tasks requiring real-time web data
- Complex research requiring reasoning capabilities
- News aggregation with current events
- Market research and trend analysis

### 2. Wikipedia MCP Server
**Purpose**: Maintained Wikipedia integration

**Installation**: Automatic via `uvx --from wikipedia-mcp-server@latest wikipedia-mcp`

**Available Tools**:
- `search`: Search Wikipedia articles with language support
- `fetch`: Fetch full page content by article ID

**Configuration**:
```python
from epic_news.config.mcp_config import MCPConfig

wikipedia_config = MCPConfig.get_wikipedia_mcp()
# Returns: {
#     "command": "uvx",
#     "args": ["--from", "wikipedia-mcp-server@latest", "wikipedia-mcp"],
#     "env": {}
# }
```

**No API key required** - Wikipedia MCP is free to use.

**Use Cases**:
- Encyclopedic research
- Background information gathering
- Historical context and facts
- Educational content

### 3. Custom Tools MCP Server (Future)
**Purpose**: Dynamic loading of epic_news custom tools

**Status**: Planned for future implementation

**Implementation**: See `src/epic_news/mcp_servers/tools_server.py` (to be created)

## Using MCP Servers with CrewAI

### Method 1: Using CrewAI's MCPServerAdapter

CrewAI supports MCP tools through the `crewai-tools[mcp]` package using `MCPServerAdapter`:

```python
from crewai import Agent
from crewai.project import CrewBase, agent
from crewai_tools import MCPServerAdapter
from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig

@CrewBase
class MyResearchCrew:
    """Example crew using MCP tools"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Initialize Wikipedia MCP server (lazy initialization recommended)
    _wikipedia_mcp = None

    @property
    def wikipedia_tools(self):
        """Get Wikipedia MCP tools."""
        if self._wikipedia_mcp is None:
            wikipedia_params = MCPConfig.get_wikipedia_mcp()
            self._wikipedia_mcp = MCPServerAdapter(wikipedia_params)
        return self._wikipedia_mcp.tools

    # Create agent with MCP tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.wikipedia_tools,
            llm=LLMConfig.get_openrouter_llm(),
            llm_timeout=LLMConfig.get_timeout("long"),
            verbose=True,
        )
```

**Alternative: Context Manager Pattern** (for short-lived usage):

```python
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

# Get Wikipedia tools using context manager
wikipedia_params = MCPConfig.get_wikipedia_mcp()
with MCPServerAdapter(wikipedia_params) as tools:
    # Use tools here
    # MCP server will be automatically stopped when exiting the context
    pass
```

### Method 2: Direct Tool Import (If Available)

Some MCP servers may provide direct Python imports:

```python
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool

# Use existing custom tools
tools = [
    WikipediaSearchTool(),
    WikipediaArticleTool(),
]
```

## Crews Using MCP Tools

### Deep Research Crew

**MCP Servers**: Wikipedia MCP (replaces custom Wikipedia tools)

**Before**:
```python
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool

@agent
def wikipedia_specialist(self) -> Agent:
    return Agent(
        config=self.agents_config["wikipedia_specialist"],
        tools=[
            WikipediaSearchTool(),
            WikipediaArticleTool(),
        ],
        verbose=True,
    )
```

**After** (with MCP):
```python
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

@CrewBase
class DeepResearchCrew:
    # Initialize Wikipedia MCP server
    _wikipedia_mcp = None

    @property
    def wikipedia_tools(self):
        """Get Wikipedia MCP tools (lazy initialization)."""
        if self._wikipedia_mcp is None:
            wikipedia_params = MCPConfig.get_wikipedia_mcp()
            self._wikipedia_mcp = MCPServerAdapter(wikipedia_params)
        return self._wikipedia_mcp.tools

    @agent
    def wikipedia_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["wikipedia_specialist"],
            tools=self.wikipedia_tools,  # Use MCP tools
            verbose=True,
        )
```

**Benefits**:
- Maintained Wikipedia integration
- Automatic updates
- Better error handling
- No custom tool maintenance required

### Company News Crew

**MCP Servers**: Perplexity MCP (enhances web search)

**Use Case**: Real-time company news research

**Integration**:
```python
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

@CrewBase
class CompanyNewsCrew:
    # Initialize Perplexity MCP server
    _perplexity_mcp = None

    @property
    def perplexity_tools(self):
        """Get Perplexity MCP tools."""
        if self._perplexity_mcp is None:
            perplexity_params = MCPConfig.get_perplexity_mcp()
            self._perplexity_mcp = MCPServerAdapter(perplexity_params)
        return self._perplexity_mcp.tools

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=self.perplexity_tools,  # Use perplexity_search, perplexity_research
            llm=LLMConfig.get_openrouter_llm(),
            verbose=True,
        )
```

### News Daily Crew

**MCP Servers**: Perplexity MCP (current events)

**Use Case**: Daily news curation in French

**Integration**:
```python
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

@CrewBase
class NewsDailyCrew:
    @property
    def perplexity_tools(self):
        """Get Perplexity MCP tools for news research."""
        if not hasattr(self, '_perplexity_mcp') or self._perplexity_mcp is None:
            perplexity_params = MCPConfig.get_perplexity_mcp()
            self._perplexity_mcp = MCPServerAdapter(perplexity_params)
        return self._perplexity_mcp.tools

    # Use perplexity_ask for conversational news queries
    # Use perplexity_search for topic-specific news
```

## Environment Setup

### Required Environment Variables

Add to your `.env` file:

```bash
# Perplexity MCP (Optional - only if using Perplexity tools)
PERPLEXITY_API_KEY=pplx-your-api-key-here
```

### No Additional Variables Required

- **Wikipedia MCP**: No API key needed
- **Custom Tools MCP**: Uses existing project configuration

## Testing MCP Integration

### Test MCP Configuration

```python
from epic_news.config.mcp_config import MCPConfig

# Test Wikipedia MCP (no API key required)
wikipedia_config = MCPConfig.get_wikipedia_mcp()
print("✓ Wikipedia MCP configured:", wikipedia_config)

# Test Perplexity MCP (requires API key)
try:
    perplexity_config = MCPConfig.get_perplexity_mcp()
    print("✓ Perplexity MCP configured:", perplexity_config)
except ValueError as e:
    print("⚠ Perplexity MCP not configured:", e)

# Test all servers
all_servers = MCPConfig.get_all_mcp_servers()
print(f"✓ Total MCP servers configured: {len(all_servers)}")
for name in all_servers.keys():
    print(f"  - {name}")
```

### Test MCP Tools with CrewAI

```bash
# Test Wikipedia MCP with deep_research crew
uv run crewai flow kickoff -f deep_research
```

### Test MCP Server Directly

```python
# Test Wikipedia MCP server
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

wikipedia_params = MCPConfig.get_wikipedia_mcp()
with MCPServerAdapter(wikipedia_params) as tools:
    print(f"Available tools: {[tool.name for tool in tools]}")
    # Expected: ['search', 'fetch']
```

## Troubleshooting

### Issue: MCP server not starting

**Symptoms**: Error when initializing MCP client

**Solutions**:
1. Check if `npx` is installed (for Perplexity): `npx --version`
2. Check if `uv` is installed (for Wikipedia): `uv --version`
3. Verify environment variables are set correctly

### Issue: Perplexity API key not found

**Symptoms**: `ValueError: PERPLEXITY_API_KEY environment variable is required`

**Solutions**:
1. Add `PERPLEXITY_API_KEY` to your `.env` file
2. Restart your terminal/IDE to reload environment variables
3. Verify the key is valid at https://www.perplexity.ai

### Issue: Wikipedia MCP not responding

**Symptoms**: Timeout or connection errors

**Solutions**:
1. Ensure you have internet connectivity
2. Update wikipedia-mcp-server: `uv tool install --upgrade wikipedia-mcp-server`
3. Check if the MCP server is running: `uvx --from wikipedia-mcp-server@latest wikipedia-mcp --help`

## Benefits of MCP Integration

### 1. **Maintained Tools**
- MCP servers are maintained by their providers
- Automatic updates and bug fixes
- No need to maintain custom Wikipedia/Perplexity wrappers

### 2. **Better Performance**
- MCP servers are optimized for their specific use cases
- Efficient data transfer
- Reduced API calls

### 3. **Standardized Interface**
- Consistent tool interface across different providers
- Easy to swap or add new MCP servers
- Better observability and debugging

### 4. **Enhanced Capabilities**
- Access to advanced features (Perplexity reasoning, deep research)
- Real-time data access
- Multi-language support (Wikipedia)

## Migration from Custom Tools

### Wikipedia Tools Migration

**Before** (Custom Tools):
```python
from epic_news.tools.wikipedia_search_tool import WikipediaSearchTool
from epic_news.tools.wikipedia_article_tool import WikipediaArticleTool

tools = [
    WikipediaSearchTool(),
    WikipediaArticleTool(),
]
```

**After** (MCP with MCPServerAdapter):
```python
from crewai_tools import MCPServerAdapter
from epic_news.config.mcp_config import MCPConfig

# Option 1: Property-based (recommended for crews)
@property
def wikipedia_tools(self):
    if self._wikipedia_mcp is None:
        wikipedia_params = MCPConfig.get_wikipedia_mcp()
        self._wikipedia_mcp = MCPServerAdapter(wikipedia_params)
    return self._wikipedia_mcp.tools

# Option 2: Context manager (for one-off usage)
wikipedia_params = MCPConfig.get_wikipedia_mcp()
with MCPServerAdapter(wikipedia_params) as tools:
    # Use tools
    pass
```

**Benefits**:
- Maintained by Wikipedia MCP team
- Better error handling
- More languages supported
- Automatic updates
- No custom tool dependencies

### Search Tools Enhancement

**Before** (Basic Search):
```python
from crewai_tools import SerperDevTool

tools = [SerperDevTool()]
```

**After** (Enhanced with Perplexity):
```python
from crewai_tools import MCPServerAdapter, SerperDevTool
from epic_news.config.mcp_config import MCPConfig

@CrewBase
class MyNewsCrew:
    @property
    def search_tools(self):
        """Get Perplexity MCP tools + backup search."""
        if not hasattr(self, '_perplexity_mcp'):
            perplexity_params = MCPConfig.get_perplexity_mcp()
            self._perplexity_mcp = MCPServerAdapter(perplexity_params)

        # Combine MCP tools with traditional tools
        return self._perplexity_mcp.tools + [SerperDevTool()]

# Use perplexity_search for better results
# Use perplexity_research for deep analysis
# Keep SerperDevTool as backup
```

## Future Enhancements

### Custom Tools MCP Server

**Goal**: Expose epic_news 62 custom tools via MCP

**Benefits**:
- Dynamic tool loading
- Better observability
- Centralized tool management
- Version control for tools

**Implementation**: See `src/epic_news/mcp_servers/tools_server.py` (planned)

### Additional MCP Servers

Potential MCP servers to integrate:
- **GitHub MCP**: For code repository analysis
- **Notion MCP**: For documentation storage
- **Slack MCP**: For team notifications
- **Custom News APIs**: Via custom MCP servers

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [CrewAI MCP Documentation](https://docs.crewai.com/tools/mcp)
- [Perplexity MCP Server](https://docs.perplexity.ai/guides/mcp-server)
- [Wikipedia MCP Server](https://mcpservers.org/servers/progamesigner/wikipedia-mcp)
- [MCP Server Registry](https://mcpservers.org/)

## Getting Help

If you encounter issues with MCP integration:

1. Check this guide's Troubleshooting section
2. Review the MCP server documentation (links above)
3. Check CrewAI's MCP integration docs
4. Open an issue with debug logs and configuration
