"""
Web tools for epic_news crews.

This module provides functions to get various web-based research tools
for use by the epic_news crews.
"""

from crewai_tools import (
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)


def get_search_tools():
    """
    Get web search tools.

    Returns:
        list: A list of web search tool instances.
    """
    return [
        SerperDevTool(n_results=25, search_type="search"),
        FirecrawlSearchTool(limit=25, save_file=True),
    ]


def get_news_tools():
    """
    Get news search tools.

    Returns:
        list: A list of news search tool instances.
    """
    return [
        SerperDevTool(n_results=25, search_type="news"),
    ]


def get_scrape_tools():
    """
    Get web scraping tools.

    Returns:
        list: A list of web scraping tool instances.
    """
    return [
        FirecrawlScrapeWebsiteTool(limit=25, save_file=True),
    ]


def get_youtube_tools():
    """
    Get YouTube search tools.

    Returns:
        list: A list of YouTube search tool instances.
    """
    return [
        YoutubeVideoSearchTool(),
    ]
