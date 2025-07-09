# 2. Epic News Tools Handbook

This handbook provides a comprehensive overview of all tools available to agents within the epic_news project, including native CrewAI tools, custom-built tools, and integrations from the Composio library.

## 1. Tool Integration & Best Practices

### 1.1. Modular Architecture & Factories

- **Factory Pattern**: Use factory functions to organize and provide tools. This allows for centralized management and easy modification.
- **Domain Separation**: Group tools by functionality into separate files (e.g., `web_tools.py`, `document_tools.py`).
- **Graceful Degradation**: If a tool fails to initialize (e.g., missing API key), the factory should handle it gracefully (e.g., return an empty list) so the application can proceed without it.

```python
# Example: src/epic_news/tools/document_tools.py
def get_document_tools():
    return [FileReadTool(), FileWriteTool(), PDFSearchTool()]

# Example: Graceful degradation
def get_github_tools():
    try:
        from crewai_tools import GithubSearchTool
        return [GithubSearchTool(gh_token=os.getenv('GITHUB_TOKEN'))]
    except (ImportError, Exception):
        return [] # Return empty list if dependencies or keys are missing
```

### 1.2. API Key Management

- **Security**: All API keys and sensitive credentials must be stored in environment variables (e.g., in a `.env` file) and never hardcoded in source code.
- **Validation**: Factory functions should validate the presence of required environment variables.
- **Naming Convention**: Use a consistent naming convention, such as `TOOL_NAME_API_KEY`.

```bash
# .env file
TAVILY_API_KEY=tvly-xxxxxx
SERPER_API_KEY=xxxxxx
FIRECRAWL_API_KEY=fc-xxxxxx
```

### 1.3. Performance & Testing

- **Asynchronous Execution**: Enable async for independent, I/O-bound tasks.
- **Caching**: Implement caching for expensive or frequently repeated API calls.
- **Testing**: Write unit tests for tool factories and integration tests for tool combinations. Mock external APIs to avoid costs and dependencies during testing.

## 2. Available Tools by Category

### 2.1. 🌐 Web & Search Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **TavilyTool** | Composio/Custom | Advanced search with domain filtering. | `TAVILY_API_KEY` |
| **SerperApiTool** | CrewAI | Google search via Serper.dev for general web searches. | `SERPER_API_KEY` |
| **FirecrawlScrapeWebsiteTool**| CrewAI/Custom | Extracts full content from a specific URL. | `FIRECRAWL_API_KEY` |
| **FirecrawlSearchTool** | Custom | Performs a targeted search within a specific website. | `FIRECRAWL_API_KEY` |
| **ScrapeNinjaTool** | Custom | Advanced web scraping with proxy and JS extraction. | `RAPIDAPI_KEY` |
| **EXASearchTool** | CrewAI | Specialized search with similarity functions. | `EXA_API_KEY` |
| **BrowserbaseLoadTool** | CrewAI | Browser-based content loading for dynamic sites. | `BROWSERBASE_API_KEY` |
| **YoutubeVideoSearchTool** | CrewAI | Finds relevant video content on YouTube. | YouTube API Key |
| **PerplexityAI** | Composio | Natural language search with sophisticated AI models. | `PERPLEXITY_API_KEY` |
| **SeleniumScrapingTool** | CrewAI | Browser automation for JS-heavy sites. (ScrapeNinja is preferred). | No |

### 2.2. 📄 Document & File Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **FileReadTool** | CrewAI | Reads the content of a specified file. | No |
| **FileWriteTool** | CrewAI | Writes content to a specified file. | No |
| **DirectorySearchTool** | CrewAI | Searches for files within a directory. | No |
| **DirectoryReadTool** | CrewAI | Reads the contents of a directory. | No |
| **PDFSearchTool** | CrewAI | Extracts and searches content from PDF files. | No |
| **DOCXSearchTool** | CrewAI | Searches content in Microsoft Word documents. | No |
| **CSVSearchTool** | CrewAI | Searches and analyzes data in CSV files. | No |
| **JSONSearchTool** | CrewAI | Searches and manipulates data in JSON files. | No |
| **XMLSearchTool** | CrewAI | Processes and searches XML documents. | No |
| **ExcelSearchTool** | CrewAI | Analyzes data in Excel spreadsheets. | No |
| **MDXSearchTool** | CrewAI | Processes and searches MDX files. | No |

### 2.3. 📊 Data & Analytics Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **YahooFinanceNewsTool** | Custom | Fetches the latest financial news for a specific ticker. | No |
| **YahooFinanceHistoryTool** | Custom | Gets historical price data for a ticker. | No |
| **YahooFinanceCompanyInfoTool**| Custom | Gets detailed company information (summary, industry). | No |
| **AlphaVantageCompanyTool** | Custom | Fetches fundamental company data (P/E, EPS). | `ALPHA_VANTAGE_API_KEY` |
| **CoinMarketCapInfoTool** | Custom | Gets detailed info for a cryptocurrency. | `COINMARKETCAP_API_KEY` |
| **KrakenTickerInfoTool** | Custom | Fetches real-time ticker data from Kraken exchange. | No |
| **TechStackAnalysisTool** | Custom | Identifies the technology stack of a website. | `SERPER_API_KEY` |
| **GoogleFactCheckTool** | Custom | Searches for fact-checked claims via Google's API. | `GOOGLE_API_KEY` |

### 2.4. 💻 Code & Development Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **GithubSearchTool** | CrewAI | Searches GitHub repositories and code. | `GITHUB_TOKEN` |
| **CodeDocsSearchTool** | CrewAI | Searches code documentation. | No |
| **CodeInterpreterTool** | CrewAI | Executes and interprets Python code. | No |
| **ShellTool** | Composio | Executes shell commands. | No |

### 2.5. 🤖 AI & RAG Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **RagTool** | CrewAI/Composio | Generic Retrieval-Augmented Generation capabilities. | Varies |
| **SaveToRagTool** | Custom | Persists text into the RAG vector database. | No |
| **DallETool** | CrewAI | Generates images using DALL-E. | `OPENAI_API_KEY` |
| **VisionTool** | CrewAI | Provides computer vision and image analysis. | `OPENAI_API_KEY` |

### 2.6. 🌍 Specialized & Integration Tools

| Tool | Source | Description | API Key Required |
|---|---|---|---|
| **AccuWeatherTool** | Custom | Gets current weather conditions for a location. | `ACCUWEATHER_API_KEY` |
| **AirtableTool** | Custom | Creates a new record in an Airtable table. | `AIRTABLE_API_KEY` |
| **TodoistTool** | Custom | Manages tasks and projects in Todoist. | `TODOIST_API_KEY` |
| **WikipediaTools** | Custom | A suite of tools to search and process Wikipedia articles. | No |
| **ComposioTool** | CrewAI | Gateway to integrate with over 200 third-party apps. | `COMPOSIO_API_KEY` |

## 3. Multi-Crew Protocol (MCP)

> **Note**: The integration of MCP is currently experimental and not fully implemented. This section is for future reference.

### 3.1. Overview

The Multi-Crew Protocol (MCP) is designed to enable:

- Cross-crew communication and data sharing.
- Distributed workflow orchestration.
- Scalable multi-agent system architecture.

### 3.2. Key Features

- **Crew Interconnectivity**: Seamless communication between different crews.
- **State Synchronization**: Shared state management across crew boundaries.
- **Event Propagation**: Real-time event broadcasting and handling.

### 3.3. Integration with epic_news

MCP could enhance our project by:

- Enabling deeper crew specialization (e.g., separate research and analysis crews).
- Improving scalability for larger workloads.
- Facilitating real-time collaboration between different analysis domains.
