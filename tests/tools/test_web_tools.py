import os

from crewai_tools import (
    GithubSearchTool,
    PDFSearchTool,
    ScrapeWebsiteTool,
    WebsiteSearchTool,
    YoutubeVideoSearchTool,
)

from epic_news.tools.perplexity_search_tool import PerplexitySearchTool
from epic_news.tools.scraper_factory import get_scraper
from epic_news.tools.web_tools import (
    get_all_web_tools,
    get_github_tools,
    get_news_tools,
    get_pdf_tools,
    get_scrape_tools,
    get_search_tools,
    get_website_search_tools,
    get_youtube_tools,
)


def test_get_search_tools():
    tools = get_search_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], PerplexitySearchTool)


def test_get_news_tools():
    tools = get_news_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], PerplexitySearchTool)


def test_get_scrape_tools():
    tools = get_scrape_tools()
    assert len(tools) == 2  # Primary scraper (factory) + ScrapeWebsiteTool
    assert isinstance(tools[0], type(get_scraper()))  # Primary tool from factory
    assert isinstance(tools[1], ScrapeWebsiteTool)  # Backup tool


def test_get_youtube_tools():
    tools = get_youtube_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], YoutubeVideoSearchTool)


def test_get_website_search_tools():
    tools = get_website_search_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], WebsiteSearchTool)


def test_get_github_tools():
    tools = get_github_tools()

    # If GITHUB_TOKEN is not available, the function should return an empty list
    if not os.getenv("GITHUB_TOKEN"):
        assert len(tools) == 0
        return

    # If GITHUB_TOKEN is available, we should get one tool
    assert len(tools) == 1
    github_tool = tools[0]
    assert isinstance(github_tool, GithubSearchTool)
    # Verify the content types are set correctly
    assert github_tool.content_types == ["code", "repo", "pr", "issue"]


def test_get_pdf_tools():
    tools = get_pdf_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], PDFSearchTool)


def test_get_all_web_tools():
    import os

    all_tools = get_all_web_tools()

    # Verify we get tools from all categories
    assert len(all_tools) > 0

    # Check for presence of different tool types
    tool_types = {type(tool) for tool in all_tools}
    primary_scraper_type = type(get_scraper())
    expected_types = {
        PerplexitySearchTool,
        primary_scraper_type,
        ScrapeWebsiteTool,
        WebsiteSearchTool,
        PDFSearchTool,
        YoutubeVideoSearchTool,
    }

    # Add GithubSearchTool to expected types only if GITHUB_TOKEN is available
    if os.getenv("GITHUB_TOKEN"):
        expected_types.add(GithubSearchTool)

    # Verify all expected tool types are present
    assert expected_types.issubset(tool_types)
