# Agent Tools Handbook

## TodoistTool

**Description:**
A tool for interacting with the Todoist API. It allows you to manage tasks and projects in Todoist.

**Prerequisites:**

- You must have a Todoist account.
- You must obtain an API token from your Todoist settings (Integrations -> Developer).
- The API token must be set as an environment variable named `TODOIST_API_KEY`.

**Actions:**
The tool supports the following actions, specified via the `action` parameter:

1. `get_tasks`
    - **Description:** Retrieves a list of tasks.
    - **Parameters:**
        - `project_id` (optional): The ID of the project to filter tasks by. If not provided, it fetches all tasks.
    - **Example:** `tool._run(action="get_tasks", project_id="12345")`

2. `create_task`
    - **Description:** Creates a new task.
    - **Parameters:**
        - `task_content` (required): The content of the task (e.g., "Buy milk").
        - `project_id` (optional): The ID of the project to add the task to.
        - `due_string` (optional): A human-readable due date (e.g., "tomorrow at 10am", "every day").
        - `priority` (optional): The task priority from 1 (normal) to 4 (urgent).
    - **Example:** `tool._run(action="create_task", task_content="Finish report", due_string="Friday", priority=4)`

3. `complete_task`
    - **Description:** Marks a task as complete.
    - **Parameters:**
        - `task_id` (required): The ID of the task to complete.
    - **Example:** `tool._run(action="complete_task", task_id="67890")`

4. `get_projects`
    - **Description:** Retrieves a list of all your projects.
    - **Parameters:** None.
    - **Example:** `tool._run(action="get_projects")`

**Output:**
The tool returns a string indicating the result of the operation, which could be a success message, an error message, or the data requested (e.g., a list of tasks or projects).

This document provides a comprehensive list and detailed descriptions of all tools available to AI agents within the epic_news project.

---

- **`Alpha Vantage Company Overview`**: Use to fetch fundamental data and a company overview for a specific stock ticker from Alpha Vantage. This tool helps get detailed financial metrics like Market Cap, P/E Ratio, EPS, and more.
  - `Tool Identifier`: `AlphaVantageCompanyOverviewTool`
  - `Arguments`:
    - `ticker` (string, required): The stock ticker symbol to get information for (e.g., AAPL, MSFT).

---

- **`Geoapify Places Search`**: Use to search for points of interest (POIs) using the Geoapify Places API. Supports searching by categories, conditions, and location filters.
  - `Tool Identifier`: `GeoapifyPlacesTool`
  - `Arguments`:
    - `categories` (list of strings, optional): List of category IDs to search for (e.g., `['catering.restaurant', 'commercial.supermarket']`). See [Geoapify Categories](https://apidocs.geoapify.com/docs/places/) for full list.
    - `conditions` (list of strings, optional): List of conditions to filter results (e.g., `['vegetarian', 'wheelchair']`).
    - `filter_type` (string, optional): Type of filter to apply. Options: 'circle' (lon,lat,radiusM), 'rect' (lon1,lat1,lon2,lat2), 'place' (place ID), or 'geometry' (geometry ID).
    - `filter_value` (string, optional): Filter values as comma-separated string based on filter_type. Example for circle: `'-0.1,51.5,1000'` (lon,lat,radiusM).
    - `bias` (string, optional): Bias results by proximity to a point as 'lon,lat'. Results will be sorted by distance from this point.
    - `limit` (integer, optional, default: 20): Maximum number of results to return (1-100).
    - `offset` (integer, optional, default: 0): Offset for pagination.
    - `lang` (string, optional, default: 'en'): Language code (ISO 639-1) for results.
  - `API Key(s)`: Requires `GEOAPIFY_API_KEY` to be set in the environment.
  - `Example`:

    ```python
    tool = GeoapifyPlacesTool()
    result = tool._run(
        categories=["catering.restaurant"],
        conditions=["vegetarian"],
        filter_type="circle",
        filter_value="-0.1,51.5,1000",  # lon,lat,radiusM
        bias="-0.1,51.5",  # Sort by proximity to this point
        limit=5,
        lang="en"
    )
    ```

---

- **`Alpha Vantage Company Overview`**: Use to fetch fundamental data and a company overview for a specific stock ticker from Alpha Vantage. This tool helps get detailed financial metrics like Market Cap, P/E Ratio, EPS, and more.
  - `Tool Identifier`: `AlphaVantageCompanyOverviewTool`
  - `Arguments`:
    - `ticker` (string, required): The stock ticker symbol to get information for (e.g., AAPL, MSFT).
  - `API Key(s)`: Requires `ALPHA_VANTAGE_API_KEY` to be set in the environment.

---

- **`CoinMarketCap Cryptocurrency Historical Data`**: Use to get historical price, volume, and market cap data for a specific cryptocurrency.
  - `Tool Identifier`: `CoinMarketCapHistoricalTool`
  - `Arguments`:
    - `symbol` (string, required): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug.
    - `time_period` (string, optional, default: '30d'): The time period for historical data (e.g., '7d', '30d', '1y').
  - `API Key(s)`: Requires `COINMARKETCAP_API_KEY` to be set in the environment.

---

- **`CoinMarketCap Cryptocurrency Info`**: Use to get detailed information about a specific cryptocurrency including price, market cap, volume, circulating supply, and other key metrics.
  - `Tool Identifier`: `CoinMarketCapInfoTool`
  - `Arguments`:
    - `symbol` (string, required): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug.
  - `API Key(s)`: Requires `COINMARKETCAP_API_KEY` to be set in the environment.

---

- **`CoinMarketCap Cryptocurrency List`**: Use to get a list of top cryptocurrencies.
  - `Tool Identifier`: `CoinMarketCapListTool`
  - `Arguments`:
    - `limit` (integer, optional, default: 25): Number of results to return (max 100).
    - `sort` (string, optional, default: 'market_cap'): Sort criteria (e.g., 'market_cap', 'volume_24h').
  - `API Key(s)`: Requires `COINMARKETCAP_API_KEY` to be set in the environment.

---

- **`CoinMarketCap Cryptocurrency News`**: Use to get the latest cryptocurrency news articles.
  - `Tool Identifier`: `CoinMarketCapNewsTool`
  - `Arguments`:
    - `symbol` (string, optional): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug to filter news.
    - `limit` (integer, optional, default: 10): Number of news articles to return (max 50).
  - `API Key(s)`: Requires `COINMARKETCAP_API_KEY` to be set in the environment.

---

- **`Delegating Email Search Tool`**: Routes email search queries to Hunter.io or Serper based on the specified provider. Use 'hunter' for domain-specific searches (e.g., 'example.com'). Use 'serper' for company name or broader web searches (e.g., 'Example Inc').
  - `Tool Identifier`: `DelegatingEmailSearchTool` (from `email_search.py`, uses name `email_search_router`)
  - `Arguments`:
    - `provider` (string, required): Email search provider: 'hunter' or 'serper'.
    - `query` (string, required): Domain name for 'hunter' (e.g., 'example.com'), or company name/general query for 'serper' (e.g., 'Example Inc').
  - `API Key(s)`: Requires `HUNTER_API_KEY` if `provider` is 'hunter'; `SERPER_API_KEY` if `provider` is 'serper'.

---

- **`FirecrawlScrapeWebsiteTool`**: Use when you have a specific URL and need to extract its full content for detailed analysis. This is ideal for deep dives into articles, reports, or documentation pages.
  - `Tool Identifier`: `FirecrawlScrapeWebsiteTool` (from `crewai_tools`, configured in `web_tools.py`)
  - `Arguments`:
    - `url` (string, required): The URL of the website to scrape.
  - `API Key(s)`: Requires `FIRECRAWL_API_KEY` to be set in the environment.
  - `Configuration` (in `get_scrape_tools()`):
    - `limit`: 25
    - `save_file`: True

---

- **`FirecrawlSearchTool`**: Use to perform a targeted search within a specific website. This is useful when you know a site contains the information you need but you have to find the exact page.
  - `Tool Identifier`: `FirecrawlSearchTool` (from `crewai_tools`, configured in `web_tools.py`)
  - `Arguments`:
    - `query` (string, required): The search query.
    - `site` (string, required): The specific website URL to search within (e.g., `example.com`).
  - `API Key(s)`: Requires `FIRECRAWL_API_KEY` to be set in the environment.
  - `Configuration` (in `get_search_tools()`):
    - `limit`: 25
    - `save_file`: True

---

- **`GitHub Organization Search`**: Use to search for a GitHub organization and retrieve its basic information, including description, URL, and top public repositories.
  - `Tool Identifier`: `GitHubOrgSearchTool`
  - `Arguments`:
    - `org_name` (string, required): The name of the GitHub organization (e.g., 'microsoft', 'google').
  - `API Key(s)`: Uses `GITHUB_TOKEN` for direct API access (preferred). Falls back to `SERPER_API_KEY` for web search if `GITHUB_TOKEN` is unavailable.

---

- **`GitHub Repository Search`**: Use to search GitHub for repositories, code, issues, or users based on a query.
  - `Tool Identifier`: `GitHubRepositorySearchTool`
  - `Arguments`:
    - `query` (string, required): The search term or query.
    - `search_type` (string, optional, default: "repositories"): The type of search. Options: 'repositories', 'code', 'issues', 'users'.
    - `max_results` (integer, optional, default: 5): Maximum number of results to return (1-10).
  - `API Key(s)`: Requires `GITHUB_TOKEN` to be set in the environment.

---

- **`Hunter.io Email Finder`**: Use to find professional email addresses for a given domain using Hunter.io.
  - `Tool Identifier`: `HunterIOTool` (from `hunter_io_tool.py`)
  - `Arguments`:
    - `domain` (string, required): The domain name to search for emails (e.g., example.com).
  - `API Key(s)`: Requires `HUNTER_API_KEY` to be set in the environment.

---

- **`Kraken Ticker Information`**: Use to fetch real-time ticker information (like price, volume, ask/bid) for a specific cryptocurrency pair from the Kraken exchange.
  - `Tool Identifier`: `KrakenTickerInfoTool`
  - `Arguments`:
    - `pair` (string, required): The cryptocurrency trading pair (e.g., 'XXBTZUSD' for BTC/USD, 'ETHXBT' for ETH/BTC).
  - `API Key(s)`: None (uses a public Kraken API endpoint).

---

- **`Save To RAG`**: Use to persist a piece of text (e.g., research finding, summary, user preference) into the project's Retrieval Augmented Generation (RAG) vector database. This allows the information to be retrieved by RAG-enabled tools or agents later.
  - `Tool Identifier`: `SaveToRagTool`
  - `Arguments`:
    - `text` (string, required): The text content to store in the RAG database.
  - `API Key(s)`: None.

---

- **`ScrapeNinja Web Scraper`**: Use to scrape website content using the ScrapeNinja API. This tool offers advanced options like custom headers, geolocation, proxy usage, and JavaScript-based data extraction.
  - `Tool Identifier`: `ScrapeNinjaTool`
  - `Arguments`:
    - `url` (string, required): The URL of the website to scrape.
    - `headers` (list of strings, optional): Custom headers for the request.
    - `retry_num` (integer, optional, default: 1): Number of retry attempts.
    - `geo` (string, optional): Geolocation for the request (e.g., 'us', 'eu').
    - `extractor` (string, optional): Custom JavaScript function for data extraction.
    - `proxy` (string, optional): Proxy configuration (e.g., `'http://user:pass@host:port'`).
    - `follow_redirects` (boolean, optional, default: true): Whether to follow HTTP redirects.
    - `timeout` (integer, optional, default: 60): Request timeout in seconds.
    - `text_not_expected` (string, optional): A text pattern that, if found in the response, indicates the scrape failed.
    - `status_not_expected` (integer, optional): An HTTP status code that, if received, indicates the scrape failed.
  - `API Key(s)`: Requires `RAPIDAPI_KEY` (for ScrapeNinja via RapidAPI) to be set in the environment.

---

- **`SerperDevTool (General Web Search)`**: Use for general-purpose web searches to gather a broad range of information on a topic.
  - `Tool Identifier`: `SerperDevTool` (from `crewai_tools`, configured in `web_tools.py` for general search)
  - `Arguments`:
    - `query` (string, required): The search query.
  - `API Key(s)`: Requires `SERPER_API_KEY` to be set in the environment.
  - `Configuration` (in `get_search_tools()`):
    - `n_results`: 25
    - `search_type`: "search"

---

- **`SerperDevTool (News Search)`**: Use specifically for searching news articles using Serper.dev.
  - `Tool Identifier`: `SerperDevTool` (from `crewai_tools`, configured in `web_tools.py` for news search)
  - `Arguments`:
    - `query` (string, required): The news search query.
  - `API Key(s)`: Requires `SERPER_API_KEY` to be set in the environment.
  - `Configuration` (in `get_news_tools()`):
    - `n_results`: 25
    - `search_type`: "news"

---

- **`Serper Email Search`**: Use to search the web for publicly available email addresses related to a company or domain using Serper.
  - `Tool Identifier`: `SerperEmailSearchTool` (from `serper_email_search_tool.py`)
  - `Arguments`:
    - `query` (string, required): The company name or domain name to search for emails.
  - `API Key(s)`: Requires `SERPER_API_KEY` to be set in the environment.

---

- **`Tech Stack Analysis`**: Use to analyze and identify the technology stack (frameworks, CMS, analytics, hosting) used by a given website domain. It queries services like BuiltWith and Wappalyzer via web search.
  - `Tool Identifier`: `TechStackAnalysisTool`
  - `Arguments`:
    - `domain` (string, required): The domain name of the website to analyze (e.g., 'example.com').
    - `detailed` (boolean, optional, default: false): Set to true to attempt a more detailed categorization of found technologies.
  - `API Key(s)`: Requires `SERPER_API_KEY` to be set in the environment.

---

- **`Web Search (SerpAPI)`**: Use for performing general web searches using the SerpAPI service. This is a custom implementation.
  - `Tool Identifier`: `WebSearchTool` (aliased as `SearchTool` in `web_search_tool.py`)
  - `Arguments`:
    - `query` (string, required): The search query.
    - `num_results` (integer, optional, default: 5): Number of results to return (1-10).
    - `country` (string, optional): Country code for localized results (e.g., 'us', 'gb').
    - `language` (string, optional): Language code for results (e.g., 'en', 'fr').
    - `page` (integer, optional, default: 1): Page number for pagination.
  - `API Key(s)`: Requires `SERPAPI_API_KEY` to be set in the environment.

---

- **`Yahoo Finance Company Info`**: Use to get detailed company information from Yahoo Finance, including business summary, industry, sector, key financial metrics, and valuation metrics.
  - `Tool Identifier`: `YahooFinanceCompanyInfoTool`
  - `Arguments`:
    - `ticker` (string, required): The stock ticker symbol (e.g., 'AAPL', 'MSFT').
  - `API Key(s)`: None (uses `yfinance` library).

---

- **`Yahoo Finance ETF Holdings`**: Use to retrieve detailed holdings information for an Exchange-Traded Fund (ETF) from Yahoo Finance. This includes top holdings, sector allocations, and asset breakdown.
  - `Tool Identifier`: `YahooFinanceEtfHoldingsTool`
  - `Arguments`:
    - `ticker` (string, required): The ETF ticker symbol (e.g., 'VTI', 'SPY').
  - `API Key(s)`: None (uses `yfinance` library).

---

- **`Yahoo Finance History`**: Use to get historical price data (Open, High, Low, Close, Volume) for stocks, ETFs, or cryptocurrencies from Yahoo Finance.
  - `Tool Identifier`: `YahooFinanceHistoryTool`
  - `Arguments`:
    - `ticker` (string, required): The ticker symbol (e.g., 'AAPL', 'BTC-USD').
    - `period` (string, optional, default: "1y"): The period for historical data (e.g., '1d', '5d', '1mo', '1y', 'max').
    - `interval` (string, optional, default: "1d"): The data interval (e.g., '1m', '1h', '1d', '1wk').
  - `API Key(s)`: None (uses `yfinance` library).

---

- **`Yahoo Finance NewsTool`**: Use specifically for fetching the latest financial news related to a stock, ETF, or cryptocurrency. This is the primary tool for timely market updates.
  - `Tool Identifier`: `YahooFinanceNewsTool`
  - `Arguments`:
    - `ticker` (string, required): The stock, ETF, or cryptocurrency ticker symbol (e.g., 'AAPL', 'SPY', 'BTC-USD').
  - `API Key(s)`: None (uses `yfinance` library).

---

- **`Yahoo Finance Ticker Info`**: Use to get current summary information for a stock, ETF, or cryptocurrency from Yahoo Finance. This includes current price, market cap, P/E ratio, volume, 52-week range, and other key stats.
  - `Tool Identifier`: `YahooFinanceTickerInfoTool`
  - `Arguments`:
    - `ticker` (string, required): The ticker symbol (e.g., 'AAPL', 'BTC-USD').
  - `API Key(s)`: None (uses `yfinance` library).

---

- **`YoutubeVideoSearchTool`**: Use to find relevant video content, such as interviews, financial news reports, or technical analysis tutorials.
  - `Tool Identifier`: `YoutubeVideoSearchTool` (from `crewai_tools`, configured in `web_tools.py`)
  - `Arguments`:
    - `query` (string, required): The search query for YouTube videos.
  - `API Key(s)`: Typically requires a YouTube Data API key (e.g., `YOUTUBE_API_KEY`) to be set in the environment.
