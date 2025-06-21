# Composio Tools Integration Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Composio Tool Categories](#composio-tool-categories)
3. [Integration Recommendations](#integration-recommendations)
4. [Authentication Methods](#authentication-methods)
5. [Best Practices](#best-practices)
6. [Implementation Examples](#implementation-examples)

## Overview

This document provides a comprehensive guide to Composio tools for the epic_news project. Composio offers over 200 tools that can be integrated with AI agents to enhance their capabilities across various domains. These tools follow a consistent authentication and integration pattern, making them easily adaptable to our existing crew architecture.

## Composio Tool Categories

### 🌐 Web & Search Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **WebTool** | General web interaction capabilities | None | Medium |
| **Firecrawl** | Automates web crawling and data extraction | API_KEY | High |
| **BrowserbaseTool** | Gets a URL, reads contents, and returns it | API_KEY | Medium |
| **Tavily** | Advanced search with image inclusion and domain filtering | API_KEY | High |
| **PerplexityAI** | Natural language search with sophisticated AI models | API_KEY | High |
| **YouSearch** | Search engine with enhanced filtering | API_KEY | Medium |
| **ZenRows** | Web scraping and data extraction tool | API_KEY | Medium |
| **SpiderTool** | Web crawling capabilities | None | Low |
| **Exa** | Specialized search service with similarity functions | API_KEY | Medium |

### 💻 Code & Development Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **CodeAnalysisTool** | Code indexing tool | None | High |
| **CodeInterpreter** | Python-based coding with data analysis | None | High |
| **ShellTool** | Execute shell commands | None | High |
| **GitTool** | Command manager for workspace | None | High |
| **Greptile** | Code understanding and question answering | None | Medium |
| **CodeFormatTool** | Code formatting capabilities | None | Medium |
| **WorkspaceTool** | Creates local workspaces | None | Medium |
| **HistoryFetcher** | Maintains history across commands | None | Low |

### 📊 Data & Analytics Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **SqlTool** | Execute SQL queries in a database | Varies | High |
| **GoogleBigQuery** | Query BigData through Google BigQuery | GOOGLE_SERVICE_ACCOUNT | Medium |
| **Snowflake** | Run queries on Snowflake data platform | BASIC | Medium |
| **RagTool** | Retrieval-augmented generation capabilities | None | High |
| **Entelligence** | AI-powered business insights and analytics | None | Medium |
| **MicrosoftClarity** | Website usage analytics tool | BEARER_TOKEN | Low |

### 📂 Document & Content Management

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **GoogleDocs** | Google Docs document operations | OAUTH2/BEARER_TOKEN | High |
| **SharePoint** | Microsoft platform for document management | OAUTH2 | Medium |
| **EmbedTool** | Embedding images and finding images with text | None | Medium |
| **ImageAnalyser** | Local image analysis capabilities | None | Medium |

### 🤝 CRM & Business Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **Zoho** | Interact with Zoho CRM | OAUTH2 | Medium |
| **Rocketlane** | Customer onboarding and project delivery | API_KEY | Low |
| **Vero** | Customer engagement platform | API_KEY | Low |
| **Adobe** | Digital media and marketing services | API_KEY | Medium |

### 🗺️ Location & Weather Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **GoogleMaps** | Maps, directions, and location services | OAUTH2/API_KEY | Medium |
| **WeatherMap** | Visual weather data and forecasts | None | Medium |

### 📱 Communication & Collaboration Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **GoogleMeet** | Google's video conferencing platform | OAUTH2 | Low |
| **LinkedIn** | Professional networking platform | OAUTH2 | Medium |
| **TwitterMedia** | Twitter/X multimedia tools | OAUTH1 | Medium |
| **Webex** | Communication and collaboration platform | OAUTH2 | Low |

### 🧮 Specialized Tools

| Tool | Description | Authentication | Priority |
|------|-------------|----------------|----------|
| **Mathematical** | Mathematical tools for LLMs | None | Medium |
| **Anthropic** | Anthropic AI integration | Varies | High |
| **InducedAI** | Browser automation and data extraction | API_KEY | Medium |

## Integration Recommendations

### Priority Integration Targets

Based on our project needs, these tools offer the highest value for immediate integration:

1. **Tavily** - Provides superior search capabilities with domain filtering
2. **CodeAnalysisTool** - Enhances code understanding and analysis
3. **PerplexityAI** - Offers advanced NLP-based search
4. **RagTool** - Enables retrieval-augmented generation
5. **Firecrawl** - Powerful web crawling alternative

### Integration Workflow

1. **Tool Factory Pattern**:
   ```python
   def get_composio_tools(tool_names=None):
       """Get Composio tools by name.
       
       Args:
           tool_names: List of tool names to initialize. If None, returns all tools.
           
       Returns:
           List of initialized Composio tools
       """
       tools = []
       available_tools = {
           "tavily": _get_tavily_tool,
           "perplexity": _get_perplexity_tool,
           "code_analysis": _get_code_analysis_tool,
           # Add other tools as needed
       }
       
       if tool_names is None:
           tool_names = list(available_tools.keys())
           
       for name in tool_names:
           if name in available_tools:
               try:
                   tool = available_tools[name]()
                   if tool:
                       tools.append(tool)
               except Exception as e:
                   logger.warning(f"Failed to initialize {name} tool: {str(e)}")
                   
       return tools
   ```

2. **Individual Tool Initialization**:
   ```python
   def _get_tavily_tool():
       """Initialize Tavily search tool"""
       try:
           from composio_crewai import ComposioToolSet
           
           # Get API key from environment
           api_key = os.environ.get("TAVILY_API_KEY")
           if not api_key:
               logger.warning("TAVILY_API_KEY not found in environment")
               return None
               
           return ComposioToolSet().get_tool("tavily", api_key=api_key)
       except ImportError:
           logger.warning("Failed to import ComposioToolSet")
           return None
   ```

## Authentication Methods

Composio tools use several authentication methods:

| Auth Method | Description | Configuration |
|-------------|-------------|---------------|
| **API_KEY** | Simple API key authentication | Set as environment variable |
| **OAUTH2** | OAuth 2.0 authentication flow | Requires client ID, secret, and user authorization |
| **BEARER_TOKEN** | Token-based authentication | Set as environment variable |
| **BASIC** | Username/password authentication | Set as environment variables |
| **GOOGLE_SERVICE_ACCOUNT** | Google service account auth | Requires JSON key file |
| **OAUTH1** | OAuth 1.0 authentication flow | Requires consumer key/secret and user tokens |

### Environment Variable Pattern

For API key authentication, use this naming convention:
```
TOOL_NAME_API_KEY=your_api_key_here
```

For example:
```
TAVILY_API_KEY=api_key_123456
PERPLEXITY_API_KEY=api_key_789012
```

## Best Practices

1. **Centralized Tool Management**
   - Create a central factory for all Composio tools
   - Group related tools by functionality

2. **Graceful Degradation**
   - Handle missing dependencies elegantly
   - Provide fallbacks when API keys are unavailable

3. **Secure Authentication**
   - Never hardcode API keys or tokens in source code
   - Use environment variables for all sensitive credentials

4. **Performance Optimization**
   - Initialize tools only when needed
   - Consider caching results for expensive operations

5. **Error Handling**
   - Implement robust error handling for API failures
   - Log detailed error information for debugging

## Implementation Examples

### Basic Integration Example

```python
from epic_news.tools.composio_tools import get_composio_tools

class ResearchCrew:
    def __init__(self):
        # Get specific Composio tools
        self.search_tools = get_composio_tools(["tavily", "perplexity"])
        
        # Initialize agents with these tools
        self.researcher = Agent(
            name="Researcher",
            tools=self.search_tools,
            # Other configuration...
        )
```

### Advanced Integration with Error Handling

```python
def initialize_composio_tools():
    """Initialize all required Composio tools with error handling"""
    tools = {}
    
    # Try to initialize Tavily search
    try:
        from composio_crewai import ComposioToolSet
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            tools["tavily"] = ComposioToolSet().get_tool("tavily", api_key=tavily_key)
        else:
            logger.warning("Tavily search unavailable: Missing API key")
    except Exception as e:
        logger.error(f"Tavily initialization failed: {str(e)}")
    
    # Initialize other tools with similar pattern...
    
    return tools
```

---

**Note**: This guide is intended to complement the existing `CREWAI_TOOLS_AND_MCP_GUIDE.md` document. Always refer to the official Composio documentation at https://composio.dev/tools for the most up-to-date information on available tools and authentication requirements.
