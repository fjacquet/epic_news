# tests/tools/test_coinmarketcap_news_tool.py
import json
import os
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests

from epic_news.tools.coinmarketcap_news_tool import (
    CoinMarketCapNewsTool,
    CryptocurrencyNewsInput,
)

TEST_CMC_API_KEY = "test_cmc_api_key_news_789"
CMC_PRO_API_BASE_URL = "https://pro-api.coinmarketcap.com"

@pytest.fixture
def news_tool():
    """Fixture for CoinMarketCapNewsTool instantiation with patched API key."""
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        return CoinMarketCapNewsTool()

def test_instantiation_success(news_tool):
    """Test successful instantiation of CoinMarketCapNewsTool."""
    assert news_tool.name == "CoinMarketCap Cryptocurrency News"
    assert "Get the latest cryptocurrency news articles." in news_tool.description
    assert news_tool.args_schema == CryptocurrencyNewsInput


def mock_successful_news_response(articles_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"error_code": 0},
        "data": articles_data
    }
    return mock_response

@patch('requests.get')
def test_run_successful_general_news_defaults(mock_requests_get):
    """Test _run for general news with default parameters."""
    articles_data = [
        {"title": "Crypto Soars", "source": {"name": "Crypto News Daily"}, "url": "http://example.com/1", "publishedAt": "2023-01-01T12:00:00Z", "description": "Big news!"},
        {"title": "Market Update", "source_name": "Finance Today", "url": "http://example.com/2", "published_at": "2023-01-01T11:00:00Z", "subtitle": "Market is volatile."}
    ]
    mock_requests_get.return_value = mock_successful_news_response(articles_data)

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run() # Defaults: symbol=None, limit=10
    result_data = json.loads(result_json)

    assert result_data["query_filter"] == "general"
    assert result_data["count"] == 2
    assert len(result_data["articles"]) == 2
    assert result_data["articles"][0]["title"] == "Crypto Soars"
    assert result_data["articles"][0]["source"] == "Crypto News Daily"
    assert result_data["articles"][1]["source"] == "Finance Today"

    expected_url = f"{CMC_PRO_API_BASE_URL}/v2/news/latest"
    expected_params = {"limit": 10, "sort_by": "published_at"}
    expected_headers = {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY, "Accept": "application/json"}
    mock_requests_get.assert_called_once_with(expected_url, headers=expected_headers, params=expected_params)

@patch('requests.get')
def test_run_successful_symbol_filter_uppercase(mock_requests_get):
    """Test _run with an uppercase symbol filter."""
    mock_requests_get.return_value = mock_successful_news_response([{"title": "BTC News"}])

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run(symbol="BTC", limit=5)
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "BTC"
    assert result_data["count"] == 1

    expected_params = {"symbol": "BTC", "limit": 5, "sort_by": "published_at"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_successful_slug_filter_lowercase_hyphen(mock_requests_get):
    """Test _run with a lowercase, hyphenated slug filter."""
    mock_requests_get.return_value = mock_successful_news_response([{"title": "BCH News"}])

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run(symbol="bitcoin-cash", limit=3)
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "bitcoin-cash"

    expected_params = {"slug": "bitcoin-cash", "limit": 3, "sort_by": "published_at"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_successful_slug_filter_lowercase_no_hyphen(mock_requests_get):
    """Test _run with a lowercase, non-hyphenated slug filter."""
    mock_requests_get.return_value = mock_successful_news_response([{"title": "ETH News"}])

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run(symbol="ethereum", limit=7)
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "ethereum"

    expected_params = {"slug": "ethereum", "limit": 7, "sort_by": "published_at"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_limit_capping(mock_requests_get):
    """Test that the news articles limit is capped at 50."""
    mock_requests_get.return_value = mock_successful_news_response([])
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        news_tool._run(limit=60)
    expected_params = {"limit": 50, "sort_by": "published_at"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_api_key_missing(mock_requests_get):
    """Test _run when API key is missing."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized - API Key missing"
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": ""}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error (News): 401" in result_data["error"]

    expected_headers_with_empty_key = {"X-CMC_PRO_API_KEY": "", "Accept": "application/json"}
    mock_requests_get.assert_called_once_with(ANY, headers=expected_headers_with_empty_key, params=ANY)

@patch('requests.get')
def test_run_api_error_non_200(mock_requests_get):
    """Test _run with a non-200 API error response."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error (News): 500" in result_data["error"]

@patch('requests.get')
def test_run_no_news_found_empty_data_list(mock_requests_get):
    """Test _run when API returns 200 but data list is empty."""
    mock_requests_get.return_value = mock_successful_news_response([])
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run(symbol="RARECOIN")
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "RARECOIN"
    assert result_data["count"] == 0
    assert result_data["articles"] == []

@patch('requests.get')
def test_run_malformed_response_no_data_key(mock_requests_get):
    """Test _run when API response is 200 but missing 'data' key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}} # No 'data' key
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "general"
    assert result_data["count"] == 0
    assert result_data["articles"] == []

@patch('requests.get')
def test_run_malformed_response_data_not_list(mock_requests_get):
    """Test _run when API response 'data' is not a list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}, "data": {"message": "not a list"}}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert result_data["query_filter"] == "general"
    assert result_data["count"] == 0
    assert result_data["articles"] == []

@patch('requests.get')
def test_run_requests_exception(mock_requests_get):
    """Test _run when requests.get raises a RequestException."""
    mock_requests_get.side_effect = requests.exceptions.Timeout("Connection timeout")
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "API Request failed for news: Connection timeout" in result_data["error"]

@patch('requests.get')
def test_run_json_decode_error(mock_requests_get):
    """Test _run when response.json() raises a JSONDecodeError."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "{}", 0)
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Error processing cryptocurrency news: Invalid JSON" in result_data["error"]

@patch('requests.get')
def test_run_varied_timestamp_formats(mock_requests_get):
    """Test handling of different timestamp keys in API response."""
    articles_data = [
        {"title": "T1", "timestamp": "2023-01-01T10:00:00Z"}, # Oldest format
        {"title": "T2", "published_at": "2023-01-01T11:00:00Z"}, # Preferred by historical
        {"title": "T3", "publishedAt": "2023-01-01T12:00:00Z"}  # Preferred by news
    ]
    mock_requests_get.return_value = mock_successful_news_response(articles_data)
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert result_data["articles"][0]["published_at"] == "2023-01-01T10:00:00Z"
    assert result_data["articles"][1]["published_at"] == "2023-01-01T11:00:00Z"
    assert result_data["articles"][2]["published_at"] == "2023-01-01T12:00:00Z"

@patch('requests.get')
def test_run_varied_description_formats(mock_requests_get):
    """Test handling of different description keys in API response."""
    articles_data = [
        {"title": "D1", "description": "Main desc"},
        {"title": "D2", "subtitle": "Sub desc"},
        {"title": "D3", "description": "Main desc wins", "subtitle": "Sub desc ignored"}
    ]
    mock_requests_get.return_value = mock_successful_news_response(articles_data)
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        news_tool = CoinMarketCapNewsTool()
        result_json = news_tool._run()
    result_data = json.loads(result_json)
    assert result_data["articles"][0]["description"] == "Main desc"
    assert result_data["articles"][1]["description"] == "Sub desc"
    assert result_data["articles"][2]["description"] == "Main desc wins"
