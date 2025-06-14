# epic_news Information Retrieval Strategy

## Overview

This document outlines epic_news's strategy for information retrieval. Unlike systems that rely on a static, pre-populated knowledge base, epic_news is designed to use a **real-time information retrieval** approach. This ensures that all financial analysis is based on the most current and relevant data available.

## Core Principle: Data Freshness

Financial markets are highly dynamic, and data can become stale in minutes. Our core principle is to prioritize **data freshness** to provide accurate, timely, and actionable insights. A static knowledge base would be perpetually out-of-date for our primary use cases.

## Real-Time Retrieval via Tools

Instead of querying an internal database, epic_news agents are equipped with a suite of powerful tools to fetch information on demand from the live web. This approach ensures that every analysis is conducted with up-to-the-minute data.

### Key Tools and Their Roles

- **`SerperDevTool`**: Used for broad, general-purpose web searches. It's the first step for gathering diverse information on a company, asset, or market trend.
- **`FirecrawlScrapeWebsiteTool`**: Used to extract the complete content from a specific URL. This is essential for in-depth analysis of news articles, company reports, or blog posts.
- **`YahooFinanceNewsTool`**: A specialized tool for fetching the latest financial news for a specific ticker (stock, ETF, or cryptocurrency). It is the go-to source for timely market-moving information.
- **`YoutubeVideoSearchTool`**: Used to find relevant video content, which can provide qualitative insights from interviews, news segments, or expert analysis.

## Why Not a Traditional RAG?

A traditional Retrieval-Augmented Generation (RAG) model using a vector database is excellent for many applications, but it presents challenges for real-time financial analysis:

- **Data Staleness**: The knowledge base would require constant, resource-intensive updates to avoid providing outdated information.
- **Scope Limitation**: A pre-populated database is limited to the data it has been fed, whereas real-time tools can access the entire public web.

By using live tools, epic_news bypasses these limitations, ensuring its analysis is always current and comprehensive.

## Future Considerations

To optimize performance and manage costs, a **caching layer** may be implemented in the future. This would temporarily store the results of recent, expensive tool calls to avoid redundant queries for the same information within a short time frame. However, the fundamental strategy will remain focused on retrieving live data as the primary source of truth.
