"""Unit tests for the WikipediaSearchTool."""

import json

from src.epic_news.tools.wikipedia_search_tool import WikipediaSearchTool


def test_wikipedia_search_success(mocker):
    """Test that WikipediaSearchTool returns search results successfully."""
    mock_search = mocker.patch("src.epic_news.tools.wikipedia_search_tool.wikipedia.search")
    tool = WikipediaSearchTool()
    query = "Artificial Intelligence"
    limit = 3
    expected_results = [
        "Artificial intelligence",
        "History of artificial intelligence",
        "Applications of artificial intelligence",
    ]
    mock_search.return_value = expected_results

    result_str = tool._run(query=query, limit=limit)

    mock_search.assert_called_once_with(query, results=limit)
    assert result_str == json.dumps(expected_results)


def test_wikipedia_search_api_error(mocker):
    """Test that WikipediaSearchTool handles API errors gracefully."""
    mock_search = mocker.patch("src.epic_news.tools.wikipedia_search_tool.wikipedia.search")
    tool = WikipediaSearchTool()
    query = "Error Prone Query"
    error_message = "Wikipedia API is down"
    mock_search.side_effect = Exception(error_message)

    result_str = tool._run(query=query)

    assert f"An error occurred while searching Wikipedia: {error_message}" in result_str
