# Agent Tools Handbook

This handbook provides a comprehensive overview of the tools available to agents within the epic_news project. Each tool is designed to perform specific tasks, from data retrieval to content generation, and follows the project's core design principles of simplicity, elegance, and modularity.

---

## 🌐 Web & Search Tools

### WebSearchFactory

**Description:**
A factory for creating web search tools from different providers. Use this to get an instance of a specific search tool provider.

### TavilyTool

**Description:**
A tool for performing web searches using the Tavily API.

**Prerequisites:**

- The `TAVILY_API_KEY` environment variable must be set.

### SerpApiTool

**Description:**
A tool for performing web searches using the SerpAPI.

**Prerequisites:**

- The `SERPAPI_API_KEY` environment variable must be set.

### FirecrawlScrapeWebsiteTool

**Description:**
Use when you have a specific URL and need to extract its full content for detailed analysis. This is ideal for deep dives into articles, reports, or documentation pages.

**Prerequisites:**

- `FIRECRAWL_API_KEY` must be set in the environment.

**Parameters:**

- `url` (string, required): The URL of the website to scrape.

### FirecrawlSearchTool

**Description:**
Use to perform a targeted search within a specific website. This is useful when you know a site contains the information you need but you have to find the exact page.

**Prerequisites:**

- `FIRECRAWL_API_KEY` must be set in the environment.

**Parameters:**

- `query` (string, required): The search query.
- `site` (string, required): The specific website URL to search within (e.g., `example.com`).

### ScrapeNinja Web Scraper

**Description:**
Use to scrape website content using the ScrapeNinja API. This tool offers advanced options like custom headers, geolocation, proxy usage, and JavaScript-based data extraction.

**Prerequisites:**

- Requires `RAPIDAPI_KEY` (for ScrapeNinja via RapidAPI) to be set in the environment.

**Parameters:**

- `url` (string, required): The URL of the website to scrape.
- `headers` (list of strings, optional): Custom headers for the request.
- `retry_num` (integer, optional, default: 1): Number of retry attempts.
- `geo` (string, optional): Geolocation for the request (e.g., 'us', 'eu').
- `proxy` (string, optional): Proxy server to use (format: `http://user:pw@host:port`).
- `follow_redirects` (integer, optional, default: 1): Whether to follow redirects (0 for no, 1 for yes).
- `timeout` (integer, optional, default: 8): Request timeout in seconds.
- `text_not_expected` (list of strings, optional): Text patterns that should not appear in the response.
- `status_not_expected` (list of integers, optional): HTTP status codes that should not appear in the response.
- `extractor` (string, optional): Custom JavaScript function for data extraction.

### SeleniumScrapingTool

**Description:**
Browser automation scraping for JavaScript-heavy sites.

**Note**: `ScrapeNinjaTool` is preferred for performance.

### EXASearchTool

**Description:**
Advanced search capabilities for specialized search queries.

**Prerequisites:**

- `EXA_API_KEY` must be set in the environment.

### BrowserbaseLoadTool

**Description:**
Browser-based content loading for dynamic content extraction.

**Prerequisites:**

- `BROWSERBASE_API_KEY` must be set in the environment.

### YoutubeVideoSearchTool

**Description:**
Use to find relevant video content, such as interviews, financial news reports, or technical analysis tutorials.

**Prerequisites:**

- Typically requires a YouTube Data API key (e.g., `YOUTUBE_API_KEY`) to be set in the environment.

**Parameters:**

- `query` (string, required): The search query for YouTube videos.

---

## 📂 File & Directory Management Tools

### FileReadTool

**Description:**
Read file contents.

**Use Case:**
Document processing workflows.

### FileWriteTool

**Description:**
Write content to files.

**Use Case:**
Content generation and export.

### DirectorySearchTool

**Description:**
Search within directories.

**Use Case:**
Code analysis, file discovery.

### DirectoryReadTool

**Description:**
Read directory contents.

**Use Case:**
Project structure analysis.

---

## 📄 Document Processing Tools

### PDFSearchTool

**Description:**
PDF content extraction and search.

### DOCXSearchTool

**Description:**
Microsoft Word document search.

### CSVSearchTool

**Description:**
CSV file search and analysis.

### JSONSearchTool

**Description:**
JSON data search and manipulation.

### XMLSearchTool

**Description:**
XML document processing.

### TXTSearchTool

**Description:**
Plain text file search.

### ExcelSearchTool

**Description:**
Excel spreadsheet analysis.

### MDXSearchTool

**Description:**
MDX file processing.

---

## 💻 Code & Development Tools

### GithubSearchTool

**Description:**
GitHub repository and code searches.

### CodeDocsSearchTool

**Description:**
Search code documentation.

### CodeInterpreterTool

**Description:**
Execute and interpret code.

---

## 📊 Data & Analytics Tools

### Alpha Vantage Company Overview Tool

**Description:**
Use to fetch fundamental data and a company overview for a specific stock ticker from Alpha Vantage. This tool helps get detailed financial metrics like Market Cap, P/E Ratio, EPS, and more.

**Prerequisites:**

- The `ALPHA_VANTAGE_API_KEY` environment variable must be set.

**Parameters:**

- `ticker` (string, required): The stock ticker symbol to get information for (e.g., AAPL, MSFT).

### CoinMarketCap Tools

#### CoinMarketCap Cryptocurrency Historical Data

**Description:**
Use to get historical price, volume, and market cap data for a specific cryptocurrency.

**Prerequisites:**

- `COINMARKETCAP_API_KEY` must be set in the environment.

**Parameters:**

- `symbol` (string, required): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug.
- `time_period` (string, optional, default: '30d'): The time period for historical data (e.g., '7d', '30d', '1y').

#### CoinMarketCap Cryptocurrency Info

**Description:**
Use to get detailed information about a specific cryptocurrency including price, market cap, volume, circulating supply, and other key metrics.

**Prerequisites:**

- `COINMARKETCAP_API_KEY` must be set in the environment.

**Parameters:**

- `symbol` (string, required): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug.

#### CoinMarketCap Cryptocurrency List

**Description:**
Use to get a list of top cryptocurrencies.

**Prerequisites:**

- `COINMARKETCAP_API_KEY` must be set in the environment.

**Parameters:**

- `limit` (integer, optional, default: 25): Number of results to return (max 100).
- `sort` (string, optional, default: 'market_cap'): Sort criteria (e.g., 'market_cap', 'volume_24h').

#### CoinMarketCap Cryptocurrency News

**Description:**
Use to get the latest cryptocurrency news articles.

**Prerequisites:**

- `COINMARKETCAP_API_KEY` must be set in the environment.

**Parameters:**

- `symbol` (string, optional): The cryptocurrency symbol (e.g., 'BTC', 'ETH') or slug to filter news.
- `limit` (integer, optional, default: 10): Number of news articles to return (max 50).

### Yahoo Finance Tools

#### Yahoo Finance Company Info

**Description:**
Use to get detailed company information from Yahoo Finance, including business summary, industry, sector, key financial metrics, and valuation metrics.

**Parameters:**

- `ticker` (string, required): The stock ticker symbol (e.g., 'AAPL', 'MSFT').

#### Yahoo Finance ETF Holdings

**Description:**
Use to retrieve detailed holdings information for an Exchange-Traded Fund (ETF) from Yahoo Finance. This includes top holdings, sector allocations, and asset breakdown.

**Parameters:**

- `ticker` (string, required): The ETF ticker symbol (e.g., 'VTI', 'SPY').

#### Yahoo Finance History

**Description:**
Use to get historical price data (Open, High, Low, Close, Volume) for stocks, ETFs, or cryptocurrencies from Yahoo Finance.

**Parameters:**

- `ticker` (string, required): The ticker symbol (e.g., 'AAPL', 'BTC-USD').
- `period` (string, optional, default: "1y"): The period for historical data (e.g., '1d', '5d', '1mo', '1y', 'max').
- `interval` (string, optional, default: "1d"): The data interval (e.g., '1m', '1h', '1d', '1wk').

#### Yahoo Finance NewsTool

**Description:**
Use specifically for fetching the latest financial news related to a stock, ETF, or cryptocurrency. This is the primary tool for timely market updates.

**Parameters:**

- `ticker` (string, required): The stock, ETF, or cryptocurrency ticker symbol (e.g., 'AAPL', 'SPY', 'BTC-USD').

#### Yahoo Finance Ticker Info

**Description:**
Use to get current summary information for a stock, ETF, or cryptocurrency from Yahoo Finance. This includes current price, market cap, P/E ratio, volume, 52-week range, and other key stats.

**Parameters:**

- `ticker` (string, required): The ticker symbol (e.g., 'AAPL', 'BTC-USD').

### Kraken Ticker Information

**Description:**
Use to fetch real-time ticker information (like price, volume, ask/bid) for a specific cryptocurrency pair from the Kraken exchange.

**Parameters:**

- `pair` (string, required): The cryptocurrency trading pair (e.g., 'XXBTZUSD' for BTC/USD, 'ETHXBT' for ETH/BTC).

---

## 🗄️ Database Integration Tools

### PGSearchTool

**Description:**
PostgreSQL database search.

**Prerequisites:**
- Connection String

### MySQLSearchTool

**Description:**
MySQL database search.

**Prerequisites:**
- Connection String

### SQLSearchTool

**Description:**
Generic SQL database queries.

**Prerequisites:**
- Connection String

---

## 🤖 AI-Powered Tools

### DallETool

**Description:**
DALL-E image generation.

**Prerequisites:**
- `OPENAI_API_KEY`

### VisionTool

**Description:**
Computer vision and image analysis.

**Prerequisites:**
- `OPENAI_API_KEY`

### StagehandTool

**Description:**
Advanced AI workflow management.

**Prerequisites:**
- Varies

### MultiModalRagTool

**Description:**
Multi-modal RAG system.

**Prerequisites:**
- Varies

### RagTool

**Description:**
Generic RAG implementation.

**Prerequisites:**
- Varies

### Save To RAG

**Description:**
Use to persist a piece of text (e.g., research finding, summary, user preference) into the project's Retrieval Augmented Generation (RAG) vector database. This allows the information to be retrieved by RAG-enabled tools or agents later.

**Parameters:**

- `text` (string, required): The text content to store in the RAG database.

---

## 🌍 Specialized Domain Tools

### AccuWeatherTool

**Description:**
A tool to get the current weather conditions for a specific location. It first finds the location key for the given city name and then uses it to fetch the current weather data.

**Prerequisites:**

- The `ACCUWEATHER_API_KEY` environment variable must be set with a valid AccuWeather API key.

**Parameters:**

- `location` (str): The city name to get the current weather for (e.g., 'London').

### AirtableTool

**Description:**
A tool for creating a new record in a specified Airtable table. It requires the base ID, table name, and the data for the new record.

**Prerequisites:**

- The `AIRTABLE_API_KEY` environment variable must be set with a valid Airtable API key.

**Parameters:**

- `base_id` (str): The ID of the Airtable base.
- `table_name` (str): The name of the table within the base.
- `data` (dict): A dictionary representing the data for the new record.

### Delegating Email Search Tool

**Description:**
Routes email search queries to Hunter.io or Serper based on the specified provider. Use 'hunter' for domain-specific searches (e.g., 'example.com'). Use 'serper' for company name or broader web searches (e.g., 'Example Inc').

**Prerequisites:**

- `HUNTER_API_KEY` if `provider` is 'hunter'.
- `SERPER_API_KEY` if `provider` is 'serper'.

**Parameters:**

- `provider` (string, required): Email search provider: 'hunter' or 'serper'.
- `query` (string, required): Domain name for 'hunter' (e.g., 'example.com'), or company name/general query for 'serper' (e.g., 'Example Inc').

### Geoapify Places Search Tool

**Description:**
Use to search for points of interest (POIs) using the Geoapify Places API. Supports searching by categories, conditions, and location filters.

**Prerequisites:**

- `GEOAPIFY_API_KEY` must be set in the environment.

**Parameters:**

- `categories` (list of strings, optional): List of category IDs to search for (e.g., `['catering.restaurant', 'commercial.supermarket']`).
- `conditions` (list of strings, optional): List of conditions to filter results (e.g., `['vegetarian', 'wheelchair']`).
- `filter_type` (string, optional): Type of filter to apply. Options: 'circle', 'rect', 'place', or 'geometry'.
- `filter_value` (string, optional): Filter values based on filter_type.
- `bias` (string, optional): Bias results by proximity to a point as 'lon,lat'.
- `limit` (integer, optional, default: 20): Maximum number of results to return (1-100).
- `offset` (integer, optional, default: 0): Offset for pagination.
- `lang` (string, optional, default: 'en'): Language code for results.

### TodoistTool

**Description:**
A tool for interacting with the Todoist API. It allows you to manage tasks and projects in Todoist.

**Prerequisites:**

- The `TODOIST_API_KEY` environment variable must be set.

**Actions:**

- `get_tasks`: Retrieves a list of tasks.
- `create_task`: Creates a new task.
- `complete_task`: Marks a task as complete.
- `get_projects`: Retrieves a list of all your projects.

**Parameters:**

- See tool for detailed parameters for each action.

### Wikipedia Tools

#### WikipediaArticleTool

**Description:**
A tool to fetch various types of content from a Wikipedia article. Actions include getting a summary, full content, links, sections, or related topics.

**Prerequisites:**

- The `wikipedia` python package must be installed.

**Actions:**

- `get_summary`: Retrieves a concise summary of a Wikipedia article.
- `get_article`: Fetches the full plain text content of a Wikipedia article.
- `get_links`: Gets all the links contained within a Wikipedia article.
- `get_sections`: Retrieves the table of contents (all section titles) for an article.
- `get_related_topics`: Gets a list of topics related to an article, based on its outgoing links.

**Parameters:**

- `title` (str, required): The title of the Wikipedia article.
- `action` (str, required): The action to perform on the article.
- `limit` (int, optional, default: 10): Limit for actions like 'get_related_topics'.

#### WikipediaProcessingTool

**Description:**
A tool to process content from a Wikipedia article, such as extracting key facts or creating query-specific summaries.

**Prerequisites:**

- The `wikipedia` python package must be installed.

**Actions:**

- `extract_key_facts`: Extracts the first few sentences from an article's summary or a specific section.
- `summarize_article_for_query`: Creates a summary of an article focused on paragraphs relevant to a specific query.
- `summarize_article_section`: Provides a summary of a specific section within an article.

**Parameters:**

- `title` (str, required): The title of the Wikipedia article.
- `action` (str, required): The processing action to perform.
- `query` (str, optional): The query to tailor the summary for.
- `section_title` (str, optional): The title of the section to summarize or extract facts from.
- `max_length` (int, optional, default: 150): The maximum length of the summary.
- `count` (int, optional, default: 5): The number of key facts to extract.

#### WikipediaSearchTool

**Description:**
A tool to search for articles on Wikipedia.

**Prerequisites:**

- The `wikipedia` python package must be installed.

**Parameters:**

- `query` (str, required): The search query for Wikipedia.
- `limit` (int, optional, default: 5): The maximum number of results to return.

### Fact-Checking Tools

#### FactCheckingToolsFactory

**Description:**
A factory for creating fact-checking tools from different providers. Use this to get an instance of a specific fact-checking tool provider.

#### GoogleFactCheckTool

**Description:**
A tool for searching for fact-checked claims using the Google Fact Check API. It returns a list of claims and their reviews for a given query. This tool can be instantiated via the `FactCheckingToolsFactory`.

**Prerequisites:**

- The `GOOGLE_API_KEY` environment variable must be set with a valid Google API key.

**Parameters:**

- `query` (str): The search query for fact-checked claims.
- `review_publisher_site_filter` (str, optional): The review publisher site to filter results by (e.g., 'nytimes.com').
- `language_code` (str, optional): The BCP-47 language code to restrict results by (e.g., 'en-US').
- `max_age_days` (int, optional): The maximum age of the returned search results in days.
- `page_size` (int, optional, default: 10): The number of results to return per page.
- `page_token` (str, optional): The pagination token for retrieving the next page of results.

### Tech Stack Analysis

**Description:**
Use to analyze and identify the technology stack (frameworks, CMS, analytics, hosting) used by a given website domain. It queries services like BuiltWith and Wappalyzer via web search.

**Prerequisites:**

- Requires `SERPER_API_KEY` to be set in the environment.

**Parameters:**

- `domain` (string, required): The domain name of the website to analyze (e.g., 'example.com').
- `detailed` (boolean, optional, default: false): Set to true to attempt a more detailed categorization of found technologies.