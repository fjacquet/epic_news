import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.epic_news.tools.tavily_tool import TavilyTool


@pytest.fixture
def tool():
    """Fixture to provide a TavilyTool instance."""
    return TavilyTool()


def test_tavily_search_success(tool, mocker):
    """Test a successful search with the TavilyTool."""
    mocker.patch.dict(os.environ, {"TAVILY_API_KEY": "fake_api_token"})
    mock_tavily_client = mocker.patch("src.epic_news.tools.tavily_tool.TavilyClient")
    mock_instance = mocker.MagicMock()
    mock_instance.search.return_value = {"results": "Search results for AI"}
    mock_tavily_client.return_value = mock_instance

    result = tool._run(query="What is AI?")

    assert result == "Search results for AI"
    mock_instance.search.assert_called_once_with(query="What is AI?", search_depth="basic")


def test_tavily_search_missing_api_key(tool, mocker):
    """Test that the tool handles a missing API key gracefully."""
    mocker.patch.dict(os.environ, {}, clear=True)
    result = tool._run(query="What is AI?")
    assert "TAVILY_API_KEY environment variable not set" in str(result)


def test_tavily_search_api_error(tool, mocker):
    """Test that the tool handles an API error gracefully."""
    mocker.patch.dict(os.environ, {"TAVILY_API_KEY": "fake_api_token"})
    mock_tavily_client = mocker.patch("src.epic_news.tools.tavily_tool.TavilyClient")
    mock_instance = mocker.MagicMock()
    mock_instance.search.side_effect = Exception("API Error")
    mock_tavily_client.return_value = mock_instance

    result = tool._run(query="What is AI?")

    assert "Error performing search with Tavily: API Error" in str(result)
