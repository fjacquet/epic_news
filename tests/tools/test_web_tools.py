from crewai_tools import (
    SerperDevTool,
    YoutubeVideoSearchTool,
)

from epic_news.tools.scrape_ninja_tool import ScrapeNinjaTool
from epic_news.tools.web_tools import (
    get_news_tools,
    get_scrape_tools,
    get_search_tools,
    get_youtube_tools,
)


def test_get_search_tools():
    tools = get_search_tools()
    assert len(tools) == 1
    serper_tool = tools[0]
    assert isinstance(serper_tool, SerperDevTool)
    assert serper_tool.n_results == 25
    assert serper_tool.search_type == "search"



def test_get_news_tools():
    tools = get_news_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], SerperDevTool)
    assert tools[0].n_results == 25
    assert tools[0].search_type == "news"


def test_get_scrape_tools():
    tools = get_scrape_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], ScrapeNinjaTool)
    # Similar to FirecrawlSearchTool, 'limit' and 'save_file' are not easily verifiable instance attributes.


def test_get_youtube_tools():
    tools = get_youtube_tools()
    assert len(tools) == 1
    assert isinstance(tools[0], YoutubeVideoSearchTool)
