import pytest
from crewai_tools import (
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)

from epic_news.tools.web_tools import (
    get_search_tools,
    get_news_tools,
    get_scrape_tools,
    get_youtube_tools,
)

def test_get_search_tools():
    tools = get_search_tools()
    assert len(tools) == 2

    serper_tool = next((t for t in tools if isinstance(t, SerperDevTool)), None)
    firecrawl_search_tool = next((t for t in tools if isinstance(t, FirecrawlSearchTool)), None)

    assert serper_tool is not None
    assert serper_tool.n_results == 25
    assert serper_tool.search_type == "search"

    assert firecrawl_search_tool is not None
    # Cannot directly check 'limit' and 'save_file' as they are passed to the API call, not stored as easily accessible attributes on the instance for FirecrawlSearchTool.
    # We trust that crewai_tools handles these parameters correctly.
    # We are primarily testing that the correct tool is instantiated.


def test_get_news_tools():
    tools = get_news_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], SerperDevTool)
    assert tools[0].n_results == 25
    assert tools[0].search_type == "news"


def test_get_scrape_tools():
    tools = get_scrape_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], FirecrawlScrapeWebsiteTool)
    # Similar to FirecrawlSearchTool, 'limit' and 'save_file' are not easily verifiable instance attributes.


def test_get_youtube_tools():
    tools = get_youtube_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], YoutubeVideoSearchTool)
