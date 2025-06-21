import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.epic_news.tools.tavily_tool import TavilyTool


@pytest.fixture
def tool():
    """Fixture to provide a TavilyTool instance."""
    return TavilyTool()

@patch.dict(os.environ, {"TAVILY_API_KEY": "fake_api_token"})
@patch('src.epic_news.tools.tavily_tool.TavilyClient')
def test_tavily_search_success(mock_tavily_client, tool):
    """Test a successful search with the TavilyTool."""
    mock_instance = MagicMock()
    mock_instance.search.return_value = {'results': 'Search results for AI'}
    mock_tavily_client.return_value = mock_instance

    result = tool._run(query="What is AI?")

    assert result == 'Search results for AI'
    mock_instance.search.assert_called_once_with(query="What is AI?", search_depth="basic")

@patch.dict(os.environ, {}, clear=True)
def test_tavily_search_missing_api_key(tool):
    """Test that the tool handles a missing API key gracefully."""
    result = tool._run(query="What is AI?")
    assert "TAVILY_API_KEY environment variable not set" in str(result)

@patch.dict(os.environ, {"TAVILY_API_KEY": "fake_api_token"})
@patch('src.epic_news.tools.tavily_tool.TavilyClient')
def test_tavily_search_api_error(mock_tavily_client, tool):
    """Test that the tool handles an API error gracefully."""
    mock_instance = MagicMock()
    mock_instance.search.side_effect = Exception("API Error")
    mock_tavily_client.return_value = mock_instance

    result = tool._run(query="What is AI?")

    assert "Error performing search with Tavily: API Error" in str(result)
