# MCP Server Integration Guide

## Overview

This project uses MCP (Model Context Protocol) servers to enhance crew capabilities with external data sources and specialized tools. MCP provides a standardized way to integrate external services into LLM-powered applications.

**Current MCP Servers**:
1. **Wikipedia MCP** - Encyclopedic research and knowledge retrieval
2. *(Future)* Perplexity MCP - Advanced web research
3. *(Future)* Custom Tools MCP - Project-specific tools server

## What is MCP?

The Model Context Protocol is a standard protocol that allows AI assistants to securely interact with local and remote resources. MCP servers expose tools, prompts, and resources that LLMs can use during execution.

**Benefits**:
- **Standardization**: Consistent interface for tool integration
- **Maintainability**: Use community-maintained servers instead of custom tools
- **Scalability**: Add new capabilities by installing servers, not writing code
- **Security**: Fine-grained control over data access

## Installed MCP Servers

### 1. Wikipedia MCP Server

**Purpose**: Provides maintained Wikipedia integration for encyclopedic research.

**Installation**:
```bash
# Via uv (recommended)
uv tool install wikipedia-mcp-server
```

**Available Tools**:
- `search(query, language)`: Search Wikipedia articles
  - `query`: Search terms
  - `language`: Language code (default: "en")
  - Returns: List of matching articles with titles and snippets

- `fetch(page_id)`: Fetch full article content
  - `page_id`: Wikipedia page ID from search results
  - Returns: Complete article text with metadata

**Configuration** (`src/epic_news/config/mcp_config.py`):
```python
from mcp.server import MCPServerStdio

def get_wikipedia_mcp():
    """Configure Wikipedia MCP server."""
    return MCPServerStdio(
        command="uvx",
        args=["wikipedia-mcp-server@latest"],
    )
```

**Crews Using Wikipedia MCP**:
- `deep_research`: Replaces custom WikipediaTool with maintained MCP server
- `library`: Adds Wikipedia context for book research
- `holiday_planner`: Provides destination information

**Example Usage**:
```python
# Search for articles
results = wikipedia_search("artificial intelligence", language="en")
# returns: [{"page_id": 12345, "title": "Artificial Intelligence", "snippet": "..."}]

# Fetch full article
article = wikipedia_fetch(page_id=12345)
# returns: {"title": "...", "content": "...", "url": "..."}
```

### 2. Perplexity MCP Server (Future)

**Purpose**: Advanced web research with real-time search and reasoning capabilities.

**Installation**:
```bash
# Install via npx
npx @perplexity-ai/mcp-server
```

**Environment Variables**:
```bash
PERPLEXITY_API_KEY=your_perplexity_api_key
```

**Available Tools**:
- `perplexity_search`: Direct web search
- `perplexity_ask`: Conversational AI with real-time search
- `perplexity_research`: Deep research using sonar-deep-research model
- `perplexity_reason`: Advanced reasoning with citations

**Target Crews**:
- `deep_research`: Replace SerperDev/Tavily with `perplexity_research`
- `company_news`: Use `perplexity_search` for news discovery
- `news_daily`: Use `perplexity_ask` for current events

### 3. Custom Tools MCP Server (Future)

**Purpose**: Centralize epic_news custom tools into MCP server for dynamic loading.

**Benefits**:
- Faster crew startup (tools loaded on-demand)
- Dynamic tool filtering per crew
- Centralized tool management
- Better observability

**Implementation Location**: `src/epic_news/mcp_servers/tools_server.py`

## Adding a New MCP Server

### Step 1: Install the MCP Server

```bash
# For Python-based servers
uv tool install package-name

# For Node.js-based servers
npx package-name
```

### Step 2: Configure the Server

Add configuration to `src/epic_news/config/mcp_config.py`:

```python
from mcp.server import MCPServerStdio
import os

def get_your_mcp_server():
    """Configure Your MCP server."""
    return MCPServerStdio(
        command="command_to_run",  # e.g., "uvx", "npx"
        args=["server-package@version"],
        env={
            "API_KEY": os.getenv("YOUR_API_KEY"),  # If needed
        },
    )
```

### Step 3: Update Environment Variables

Add required API keys to `.env`:

```bash
# Your MCP Server Configuration
YOUR_API_KEY=your_api_key_here
```

### Step 4: Integrate with Crews

Use the MCP server in crew initialization:

```python
from epic_news.config.mcp_config import get_your_mcp_server

@CrewBase
class YourCrew:
    def __init__(self):
        self.mcp_server = get_your_mcp_server()
        # MCP tools are now available to agents
```

### Step 5: Document the Integration

Update:
- `CLAUDE.md`: Add to MCP Servers section
- This guide: Add server details
- `.env.example`: Add required environment variables

## Available MCP Tools by Server

### Wikipedia MCP

| Tool | Parameters | Returns | Use Case |
|------|-----------|---------|----------|
| `search` | query, language | List of articles | Find relevant Wikipedia articles |
| `fetch` | page_id | Article content | Get full article text |

### Perplexity MCP (Future)

| Tool | Parameters | Returns | Use Case |
|------|-----------|---------|----------|
| `perplexity_search` | query | Search results | Web search |
| `perplexity_ask` | question | AI response | Conversational research |
| `perplexity_research` | topic | Deep research | Comprehensive analysis |
| `perplexity_reason` | problem | Reasoning chain | Advanced problem solving |

## Troubleshooting

### MCP Server Not Starting

**Symptoms**: Error when crew initializes, tool calls fail

**Solutions**:
1. Verify installation:
   ```bash
   # For uv tools
   uv tool list

   # For npx
   npx package-name --version
   ```

2. Check environment variables:
   ```bash
   # Verify API keys are set
   echo $PERPLEXITY_API_KEY
   ```

3. Test server manually:
   ```bash
   # Run server in isolation
   uvx wikipedia-mcp-server@latest
   ```

### Tool Not Found

**Symptoms**: `ToolNotFoundError` when agent tries to use MCP tool

**Solutions**:
1. Verify tool name matches server documentation
2. Check if server is properly configured in crew
3. Ensure server started successfully (check logs)

### Rate Limiting

**Symptoms**: HTTP 429 errors, slow responses

**Solutions**:
1. Adjust `max_rpm` in crew configuration:
   ```python
   max_rpm=5  # Lower rate for expensive APIs
   ```

2. Use caching when possible
3. Monitor API usage in provider dashboard

### Authentication Errors

**Symptoms**: HTTP 401/403 errors

**Solutions**:
1. Verify API key is correct in `.env`
2. Check API key has required permissions
3. Ensure API key environment variable is loaded:
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Should be at module level
   ```

## Best Practices

### 1. Use MCP Servers for Common Tasks

**Prefer MCP servers over custom tools when available**:
- ✅ Use Wikipedia MCP instead of custom WikipediaTool
- ✅ Use Perplexity MCP instead of SerperDev/Tavily
- ⚠️ Keep custom tools only for project-specific functionality

### 2. Error Handling

Always handle MCP server failures gracefully:

```python
try:
    wikipedia_server = get_wikipedia_mcp()
except Exception as e:
    logger.warning(f"Wikipedia MCP not available: {e}")
    # Fallback to alternative tool or skip
```

### 3. Server Lifecycle

MCP servers are typically:
- Started when crew initializes
- Shared across all agents in the crew
- Automatically cleaned up when crew completes

### 4. API Key Management

**Never hardcode API keys**:
```python
# ✅ CORRECT
env={"API_KEY": os.getenv("PERPLEXITY_API_KEY")}

# ❌ WRONG
env={"API_KEY": "sk-1234567890abcdef"}
```

### 5. Tool Discovery

Use server documentation to discover available tools:
```python
# Most MCP servers support tool listing
server.list_tools()
```

## Performance Considerations

### Latency

MCP adds minimal overhead:
- Local servers (Wikipedia): ~10-50ms
- Remote servers (Perplexity): ~200-500ms (network dependent)

### Caching

Some MCP servers include built-in caching:
- Wikipedia MCP: Caches article content for 15 minutes
- Consider implementing application-level caching for expensive calls

### Rate Limiting

Monitor MCP API usage:
- Track requests per minute in crew logs
- Use `max_rpm` to prevent rate limit errors
- Consider premium API tiers for high-volume crews

## Future MCP Integrations

Potential MCP servers to add:

1. **GitHub MCP**: Code repository search and analysis
2. **Google Drive MCP**: Document access and search
3. **Notion MCP**: Knowledge base integration
4. **Slack MCP**: Team communication and data retrieval
5. **Financial Data MCP**: Market data and analytics

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Servers Directory](https://mcpservers.org/)
- [Wikipedia MCP Server](https://mcpservers.org/servers/progamesigner/wikipedia-mcp)
- [Perplexity MCP Guide](https://docs.perplexity.ai/guides/mcp-server)
- [CrewAI MCP Integration](https://docs.crewai.com/concepts/mcp)

## Support

For MCP-related issues:
1. Check server-specific documentation
2. Review CrewAI MCP integration docs
3. Check `logs/` directory for error details
4. Open issue on project GitHub with MCP server name and error logs
