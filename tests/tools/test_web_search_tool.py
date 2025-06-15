import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from epic_news.tools.web_search_tool import WebSearchInput, WebSearchTool

# Assuming logger is correctly mocked or not essential for output validation here

TEST_SERPAPI_API_KEY = "test_serpapi_key_for_web_search"
SERPAPI_SEARCH_URL = "https://serpapi.com/search"

# --- Fixtures ---
@pytest.fixture
def mock_env_serpapi_key():
    with patch.dict(os.environ, {"SERPAPI_API_KEY": TEST_SERPAPI_API_KEY}, clear=True):
        yield

@pytest.fixture
def mock_env_no_serpapi_key():
    with patch.dict(os.environ, {"SERPAPI_API_KEY": ""}, clear=True):
        yield

@pytest.fixture
@patch('epic_news.utils.logger.get_logger') # Mock the logger
def tool_instance(mock_get_logger, mock_env_serpapi_key):
    mock_get_logger.return_value = MagicMock() # Ensure logger calls don't break tests
    return WebSearchTool()

# --- Instantiation Tests ---
def test_instantiation_success(mock_env_serpapi_key):
    with patch('epic_news.utils.logger.get_logger') as mock_get_logger:
        mock_get_logger.return_value = MagicMock()
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert "Perform a web search" in tool.description
        assert tool.args_schema == WebSearchInput
        assert tool.api_key == TEST_SERPAPI_API_KEY

def test_instantiation_no_api_key(mock_env_no_serpapi_key):
    with patch('epic_news.utils.logger.get_logger') as mock_get_logger:
        mock_get_logger.return_value = MagicMock()
        with pytest.raises(ValueError, match="SERPAPI_API_KEY environment variable not set"):
            WebSearchTool()

# --- _run Method - Input Validation ---
@pytest.mark.parametrize("invalid_query", ["", "a", " "])
def test_run_invalid_query(tool_instance, invalid_query):
    result_str = tool_instance._run(query=invalid_query)
    expected_error = {"error": "Search query must be a non-empty string with at least 2 characters", "query": invalid_query}
    assert json.loads(result_str) == expected_error

# --- _run Method - API Interaction and Response Handling ---
@patch('requests.get')
def test_run_successful_search_results_found(mock_requests_get, tool_instance):
    query = "test query"
    num_results = 2
    country = "ca"
    language = "fr"
    page = 1

    mock_api_response_data = {
        "organic_results": [
            {"title": "Result 1", "link": "link1.com", "snippet": "Snippet 1"},
            {"title": "Result 2", "link": "link2.com", "snippet": "Snippet 2"}
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_api_response_data
    mock_requests_get.return_value = mock_response

    result_str = tool_instance._run(query=query, num_results=num_results, country=country, language=language, page=page)
    result_data = json.loads(result_str)

    expected_params = {
        "q": query,
        "api_key": TEST_SERPAPI_API_KEY,
        "num": num_results,
        "start": (page - 1) * num_results + 1,
        "hl": language,
        "gl": country,
        "safe": "active"
    }
    mock_requests_get.assert_called_once_with(SERPAPI_SEARCH_URL, params=expected_params, timeout=30)

    expected_results = [
        {"title": "Result 1", "link": "link1.com", "snippet": "Snippet 1", "source": "web_search"},
        {"title": "Result 2", "link": "link2.com", "snippet": "Snippet 2", "source": "web_search"}
    ]
    assert result_data == {"query": query, "results": expected_results, "count": len(expected_results)}

@patch('requests.get')
def test_run_successful_search_no_organic_results(mock_requests_get, tool_instance):
    query = "no results query"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"organic_results": []}
    result_str = tool_instance._run(query=query)
    expected_error = {
        "error": f"No results found for query: {query}", 
        "query": query,
        "suggestion": "Try a different search query or check your API key's search quota"
    }
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_api_returns_error_in_json(mock_requests_get, tool_instance):
    query = "api error query"
    api_error_msg = "Your API key is invalid."
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"error": api_error_msg}
    result_str = tool_instance._run(query=query)
    expected_error = {"error": f"API error: {api_error_msg}", "query": query}
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_http_error(mock_requests_get, tool_instance):
    query = "http error query"
    mock_requests_get.return_value.status_code = 401
    mock_requests_get.return_value.text = "Unauthorized access"
    result_str = tool_instance._run(query=query)
    expected_error = {
        "error": "API request failed with status 401", 
        "query": query,
        "response": "Unauthorized access"
    }
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_request_timeout(mock_requests_get, tool_instance):
    query = "timeout query"
    mock_requests_get.side_effect = requests.exceptions.Timeout
    result_str = tool_instance._run(query=query)
    expected_error = {
        "error": "Request timed out. The SerpAPI server took too long to respond.",
        "query": query,
        "suggestion": "Try again later or with a simpler query."
    }
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_connection_error(mock_requests_get, tool_instance):
    query = "connection error query"
    mock_requests_get.side_effect = requests.exceptions.ConnectionError
    result_str = tool_instance._run(query=query)
    expected_error = {
        "error": "Connection error. Could not connect to the SerpAPI server.",
        "query": query,
        "suggestion": "Check your internet connection or try again later."
    }
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_other_request_exception(mock_requests_get, tool_instance):
    query = "request exception query"
    error_msg = "Some other request error"
    mock_requests_get.side_effect = requests.exceptions.RequestException(error_msg)
    result_str = tool_instance._run(query=query)
    expected_error = {"error": f"Error performing search: {error_msg}", "query": query}
    assert json.loads(result_str) == expected_error

@patch('requests.get')
def test_run_invalid_json_response(mock_requests_get, tool_instance):
    query = "json error query"
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
    result_str = tool_instance._run(query=query)
    # The exact message from json.JSONDecodeError can vary slightly, check for key parts
    result_data = json.loads(result_str)
    assert result_data["query"] == query
    assert "Error parsing API response" in result_data["error"]
    assert "Expecting value" in result_data["error"]

@patch('requests.get')
def test_run_pagination_logic(mock_requests_get, tool_instance):
    query = "page test"
    num_results = 5
    page = 3
    # Mock successful response to avoid other errors
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"organic_results": [{"title": "p1"}]}
    
    tool_instance._run(query=query, num_results=num_results, page=page)
    args, kwargs = mock_requests_get.call_args
    assert kwargs['params']['start'] == (page - 1) * num_results + 1 # (3-1)*5 + 1 = 11

@patch('requests.get')
def test_run_default_parameters(mock_requests_get, tool_instance):
    query = "default params test"
    # Mock successful response
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"organic_results": [{"title": "d1"}]}

    tool_instance._run(query=query)
    args, kwargs = mock_requests_get.call_args
    params = kwargs['params']
    assert params['num'] == 5
    assert params['start'] == 1
    assert params['hl'] == 'en'
    assert params['gl'] == 'us'
    assert params['safe'] == 'active'
