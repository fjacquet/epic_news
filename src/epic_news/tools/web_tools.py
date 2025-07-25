"""
Web tools for epic_news crews.

This module provides functions to get various web-based research tools
for use by the epic_news crews.
"""

from crewai_tools import (
    GithubSearchTool,
    PDFSearchTool,
    ScrapeWebsiteTool,
    SerperDevTool,
    WebsiteSearchTool,
    YoutubeVideoSearchTool,
)

from epic_news.tools.hybrid_search_tool import HybridSearchTool
from epic_news.tools.rss_feed_tool import RSSFeedTool


def get_search_tools():
    """
    Get web search tools with hybrid approach (Brave Search + SerperDev fallback).

    Returns:
        list: A list of web search tool instances.
    """
    return [
        HybridSearchTool(),  # Primary: Brave Search + SerperDev fallback
        SerperDevTool(n_results=25, search_type="search"),  # Backup
    ]


def get_news_tools():
    """
    Get news search tools with RSS feeds and hybrid search for maximum reliability.

    Returns:
        list: A list of news search tool instances.
    """
    return [
        RSSFeedTool(),  # Primary: Direct RSS feeds from reliable sources
        HybridSearchTool(),  # Secondary: Brave Search + SerperDev fallback
        SerperDevTool(n_results=25, search_type="news"),  # Backup news-specific
    ]


def get_scrape_tools():
    """
    Get web scraping tools.

    Returns:
        list: A list of web scraping tool instances.
    """
    from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool

    return [
        ScrapeNinjaTool(),  # Primary scraping tool - fast and powerful
        ScrapeWebsiteTool(),  # Official CrewAI scraping tool as backup
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


def get_website_search_tools():
    """
    Get website-specific search tools.

    Returns:
        list: A list of website search tool instances.
    """
    return [
        WebsiteSearchTool(),  # Can search within specific websites
    ]


def get_github_tools():
    """
    Get GitHub-specific search tools.

    Returns:
        list: A list of GitHub search tool instances.
    """
    import os

    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        # Return empty list if no token is available
        return []

    try:
        # Try to create the GitHub tool
        github_tool = GithubSearchTool(
            gh_token=github_token,
            content_types=["code", "repo", "pr", "issue"],  # Search all content types
        )
        return [github_tool]
    except (ImportError, ValueError) as e:
        # Handle missing dependencies gracefully
        if "extra dependencies" in str(e) or "No module named" in str(e):
            # Dependencies not installed, return empty list
            return []
        # Re-raise other errors
        raise


def get_pdf_tools():
    """
    Get PDF processing tools.

    Returns:
        list: A list of PDF search tool instances.
    """
    return [
        PDFSearchTool(),  # Can search within PDF documents
    ]


def get_all_web_tools():
    """
    Get all web-related tools.

    Returns:
        list: A comprehensive list of all web tools.
    """
    return (
        get_search_tools()
        + get_news_tools()
        + get_scrape_tools()
        + get_website_search_tools()
        + get_github_tools()
        + get_pdf_tools()
        + get_youtube_tools()
    )
