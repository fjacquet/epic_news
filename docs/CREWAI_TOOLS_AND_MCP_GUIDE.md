# CrewAI Tools & MCP Integration Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [CrewAI Official Tools](#crewai-official-tools)
3. [Integration Recommendations](#integration-recommendations)
4. [API Key Requirements](#api-key-requirements)
5. [Multi-Crew Protocol (MCP)](#multi-crew-protocol-mcp)
6. [Best Practices](#best-practices)
7. [Implementation Examples](#implementation-examples)

## Overview

This document provides a comprehensive guide to CrewAI tools and Multi-Crew Protocol (MCP) integration for the epic_news project. It covers all available official tools, integration strategies, and best practices for maintaining a modular, scalable AI agent system.

## CrewAI Official Tools

### ✅ Currently Integrated Tools

The following tools are already integrated into our epic_news project:

- **WebsiteSearchTool** - Website-specific content searches
- **GithubSearchTool** - GitHub repository and code searches  
- **PDFSearchTool** - PDF content extraction and search
- **ScrapeWebsiteTool** - Alternative web scraping capabilities
- **YoutubeVideoSearchTool** - YouTube video content search and analysis

### 🔧 File & Directory Management Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **FileReadTool** | Read file contents | Document processing workflows | No |
| **FileWriteTool** | Write content to files | Content generation and export | No |
| **DirectorySearchTool** | Search within directories | Code analysis, file discovery | No |
| **DirectoryReadTool** | Read directory contents | Project structure analysis | No |

### 🌐 Advanced Web Scraping Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **SeleniumScrapingTool** | Browser automation scraping | JavaScript-heavy sites | No |
| **FirecrawlScrapeWebsiteTool** | High-performance scraping | Large-scale content extraction | Yes (FIRECRAWL_API_KEY) |

> **Note**: ScrapeNinjaTool remains our primary web scraping tool per project preferences.

### 🔍 Search & API Integration Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **SerperApiTool** | Google search via Serper.dev | General web searches | Yes (SERPER_API_KEY) |
| **EXASearchTool** | Advanced search capabilities | Specialized search queries | Yes (EXA_API_KEY) |
| **BrowserbaseLoadTool** | Browser-based content loading | Dynamic content extraction | Yes (BROWSERBASE_API_KEY) |

### 🗄️ Database Integration Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **PGSearchTool** | PostgreSQL database search | Structured data queries | Connection String |
| **MySQLSearchTool** | MySQL database search | Relational data analysis | Connection String |
| **SQLSearchTool** | Generic SQL database queries | Multi-database support | Connection String |

### 🤖 AI-Powered Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **DallETool** | DALL-E image generation | Visual content creation | Yes (OPENAI_API_KEY) |
| **VisionTool** | Computer vision and image analysis | Image processing workflows | Yes (OPENAI_API_KEY) |
| **StagehandTool** | Advanced AI workflow management | Complex automation tasks | Varies |

### 📱 Communication & Integration Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **ComposioTool** | Integration with 200+ apps | Third-party service automation | Yes (COMPOSIO_API_KEY) |

### 🔧 Development & Code Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **CodeDocsSearchTool** | Search code documentation | Development workflow analysis | No |
| **CodeInterpreterTool** | Execute and interpret code | Dynamic code execution | No |

### 📄 Document Processing Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **DOCXSearchTool** | Microsoft Word document search | Office document analysis | No |
| **CSVSearchTool** | CSV file search and analysis | Structured data processing | No |
| **JSONSearchTool** | JSON data search and manipulation | API response processing | No |
| **XMLSearchTool** | XML document processing | Structured document parsing | No |
| **TXTSearchTool** | Plain text file search | Text document analysis | No |
| **ExcelSearchTool** | Excel spreadsheet analysis | Financial data processing | No |

### 🌍 Specialized Domain Tools

| Tool | Description | Use Case | API Key Required |
|------|-------------|----------|------------------|
| **MultiModalRagTool** | Multi-modal RAG system | Advanced information retrieval | Varies |
| **MDXSearchTool** | MDX file processing | Documentation workflows | No |
| **RagTool** | Generic RAG implementation | Knowledge base integration | Varies |

## Integration Recommendations

### 🎯 High Priority (Immediate Integration)

1. **FileReadTool & FileWriteTool** 
   - **Rationale**: Essential for document processing and content generation workflows
   - **Integration**: Add to `document_tools.py` factory
   - **Use Cases**: HTML report generation, content export, document analysis

2. **DirectorySearchTool**
   - **Rationale**: Great for code analysis and project structure exploration
   - **Integration**: Add to `system_tools.py` factory
   - **Use Cases**: Codebase analysis, file discovery, project mapping

3. **CSVSearchTool & JSONSearchTool**
   - **Rationale**: Handle structured data from API responses and exports
   - **Integration**: Add to `data_tools.py` factory
   - **Use Cases**: Financial data analysis, API response processing

### 🔄 Medium Priority (Future Consideration)

1. **DallETool**
   - **Rationale**: Image generation for enhanced content creation
   - **Requirements**: OPENAI_API_KEY
   - **Use Cases**: Visual content for reports, charts, diagrams

2. **VisionTool**
   - **Rationale**: Image analysis capabilities for comprehensive content processing
   - **Requirements**: OPENAI_API_KEY
   - **Use Cases**: Screenshot analysis, visual content extraction

3. **Database Tools (PGSearchTool, MySQLSearchTool)**
   - **Rationale**: If database integration becomes necessary
   - **Requirements**: Database connection strings
   - **Use Cases**: Persistent data storage, historical analysis

### ⚠️ Low Priority (Specialized Use Cases)

1. **SeleniumScrapingTool**
   - **Note**: ScrapeNinjaTool preferred for performance
   - **Use Case**: Only if JavaScript-heavy sites can't be handled otherwise

2. **ComposioTool**
   - **Rationale**: Complex setup, specialized integration needs
   - **Use Case**: When specific third-party integrations are required

## API Key Requirements

### Current Environment Variables

```bash
# Already configured
GEOAPIFY_API_KEY=your_geoapify_key
GITHUB_TOKEN=your_github_token
SERPER_API_KEY=your_serper_key

# Required for new tools
OPENAI_API_KEY=your_openai_key          # DallETool, VisionTool
EXA_API_KEY=your_exa_key                # EXASearchTool
FIRECRAWL_API_KEY=your_firecrawl_key    # FirecrawlScrapeWebsiteTool
BROWSERBASE_API_KEY=your_browserbase_key # BrowserbaseLoadTool
COMPOSIO_API_KEY=your_composio_key      # ComposioTool
```

### Security Best Practices

- All API keys stored in environment variables (never hardcoded)
- `.env` file included in `.gitignore`
- Graceful degradation when API keys are missing
- Environment variable validation in factory functions

## Multi-Crew Protocol (MCP)

> **Note**: This section requires further research of the official MCP documentation.

### Overview

The Multi-Crew Protocol (MCP) enables:
- Cross-crew communication and data sharing
- Distributed workflow orchestration
- Scalable multi-agent system architecture
- Event-driven crew coordination

### Key Features

- **Crew Interconnectivity**: Seamless communication between different crews
- **State Synchronization**: Shared state management across crew boundaries
- **Event Propagation**: Real-time event broadcasting and handling
- **Resource Sharing**: Efficient tool and data sharing mechanisms

### Implementation Considerations

1. **Network Architecture**: How crews discover and connect to each other
2. **Data Serialization**: Standardized formats for inter-crew communication
3. **Security**: Authentication and authorization between crews
4. **Scalability**: Load balancing and resource management

### Integration with epic_news

MCP could enhance our project by:
- Enabling crew specialization (e.g., separate research and analysis crews)
- Improving scalability for larger workloads
- Facilitating real-time collaboration between different analysis domains

**TODO**: Complete this section after accessing official MCP documentation.

## Best Practices

### 🏗️ Modular Architecture

1. **Factory Pattern**: Use factory functions for tool organization
   ```python
   # Example: src/epic_news/tools/document_tools.py
   def get_document_tools():
       return [FileReadTool(), FileWriteTool(), PDFSearchTool()]
   ```

2. **Domain Separation**: Group tools by functionality
   - `web_tools.py` - Web scraping and search tools
   - `location_tools.py` - Geospatial and location tools
   - `document_tools.py` - File and document processing tools
   - `data_tools.py` - Structured data processing tools

3. **Graceful Degradation**: Handle missing dependencies
   ```python
   def get_github_tools():
       try:
           from crewai_tools import GithubSearchTool
           return [GithubSearchTool(gh_token=os.getenv('GITHUB_TOKEN'))]
       except ImportError:
           return []  # Return empty list if dependencies missing
   ```

### 🔧 Configuration Management

1. **Environment Variables**: All configuration via environment
2. **YAML Configuration**: Agent and task configuration in YAML files
3. **Default Values**: Sensible defaults for optional parameters
4. **Validation**: Validate configuration at startup

### 🧪 Testing Strategy

1. **Unit Tests**: Test each tool factory function
2. **Integration Tests**: Test tool combinations
3. **Mock External APIs**: Use mocks for expensive API calls
4. **Environment Testing**: Test with/without API keys

### 📊 Performance Optimization

1. **Asynchronous Execution**: Enable async for independent tasks
2. **Caching**: Implement caching for expensive operations
3. **Rate Limiting**: Respect API rate limits
4. **Resource Management**: Monitor memory and CPU usage

## Implementation Examples

### Adding New Tool Factory

```python
# src/epic_news/tools/document_tools.py
import os
from typing import List
from crewai_tools import FileReadTool, FileWriteTool

def get_document_tools() -> List:
    """Factory function for document processing tools."""
    tools = []
    
    # Always available tools
    tools.extend([
        FileReadTool(),
        FileWriteTool()
    ])
    
    return tools
```

### Updating Agent Configuration

```yaml
# src/epic_news/crews/osint/config/agents.yaml
financial_analyst:
  role: >
    Senior Financial Data Analyst
  goal: >
    Analyze financial data using comprehensive document processing tools
  backstory: >
    Expert in financial analysis with access to advanced document processing capabilities
  tools:
    - web_tools
    - document_tools  # New factory added
```

### Environment Variable Setup

```bash
# .env file
# Document processing tools
OPENAI_API_KEY=sk-your-openai-key-here

# Advanced search tools
EXA_API_KEY=your-exa-api-key-here

# Web scraping tools
FIRECRAWL_API_KEY=your-firecrawl-key-here
```

### Test Implementation

```python
# tests/tools/test_document_tools.py
import pytest
from epic_news.tools.document_tools import get_document_tools

def test_get_document_tools():
    """Test document tools factory returns expected tools."""
    tools = get_document_tools()
    
    assert len(tools) >= 2  # At minimum FileReadTool and FileWriteTool
    tool_names = [tool.__class__.__name__ for tool in tools]
    assert 'FileReadTool' in tool_names
    assert 'FileWriteTool' in tool_names
```

---

## 📚 Additional Resources

- [CrewAI Official Documentation](https://docs.crewai.com/)
- [CrewAI Tools Repository](https://github.com/crewAIInc/crewAI-tools)
- [CrewAI Tools Cheat Sheet](https://github.com/0xZee/CrewAi-Tools)
- [Project Design Principles](./DESIGN_PRINCIPLES.md)
- [Agent Handbook](../agent_handbook.md)
- [Tools Handbook](../tools_handbook.md)

---

*Last Updated: 2025-01-20*
*Version: 1.0*
