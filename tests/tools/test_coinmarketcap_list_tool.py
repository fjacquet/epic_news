# tests/tools/test_coinmarketcap_list_tool.py
import json
import os
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests

from epic_news.tools.coinmarketcap_list_tool import (
    CoinMarketCapListTool,
    CryptocurrencyListInput,
)

TEST_CMC_API_KEY = "test_cmc_api_key_list_456"
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

@pytest.fixture
def tool_for_instantiation_test():
    """Fixture for CoinMarketCapListTool instantiation testing."""
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
    return tool

def test_instantiation_success(tool_for_instantiation_test):
    """Test successful instantiation of CoinMarketCapListTool."""
    assert tool_for_instantiation_test.name == "CoinMarketCap Cryptocurrency List"
    assert "Get a list of top cryptocurrencies sorted by market cap" in tool_for_instantiation_test.description
    assert tool_for_instantiation_test.args_schema == CryptocurrencyListInput

@patch('requests.get')
def test_run_successful_response_defaults(mock_requests_get):
    """Test _run with a successful API response using default parameters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"error_code": 0},
        "data": [
            {
                "cmc_rank": 1, "name": "Bitcoin", "symbol": "BTC",
                "quote": {"USD": {"price": 30000, "percent_change_24h": 1.0, "market_cap": 600e9, "volume_24h": 20e9}}
            },
            {
                "cmc_rank": 2, "name": "Ethereum", "symbol": "ETH",
                "quote": {"USD": {"price": 2000, "percent_change_24h": 0.5, "market_cap": 240e9, "volume_24h": 10e9}}
            }
        ]
    }
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run() # Use defaults

    result_data = json.loads(result_json)
    assert isinstance(result_data, list)
    assert len(result_data) == 2
    assert result_data[0]["name"] == "Bitcoin"
    assert result_data[1]["symbol"] == "ETH"

    expected_url = f"{CMC_BASE_URL}/cryptocurrency/listings/latest"
    expected_params = {"limit": 25, "sort": "market_cap", "convert": "USD"}
    expected_headers = {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY, "Accept": "application/json"}
    mock_requests_get.assert_called_once_with(expected_url, headers=expected_headers, params=expected_params)

@patch('requests.get')
def test_run_successful_response_custom_params(mock_requests_get):
    """Test _run with custom limit and sort parameters."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}, "data": [{"cmc_rank": 1, "name": "TestCoin", "symbol": "TC", "quote": {"USD": {}}}]}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        tool._run(limit=5, sort="volume_24h")

    expected_params = {"limit": 5, "sort": "volume_24h", "convert": "USD"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params) # ANY for url and headers as they are tested elsewhere

@patch('requests.get')
def test_run_limit_capping(mock_requests_get):
    """Test that limit is capped at 100."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}, "data": []}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        tool._run(limit=120, sort="price")

    expected_params = {"limit": 100, "sort": "price", "convert": "USD"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_invalid_sort_parameter(mock_requests_get):
    """Test that an invalid sort parameter defaults to market_cap."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}, "data": []}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        tool._run(limit=10, sort="invalid_sort_value")

    expected_params = {"limit": 10, "sort": "market_cap", "convert": "USD"}
    mock_requests_get.assert_called_once_with(ANY, headers=ANY, params=expected_params)

@patch('requests.get')
def test_run_api_key_missing(mock_requests_get):
    """Test _run when API key is missing (simulated by empty string)."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized - API Key missing"
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": ""}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error: 401" in result_data["error"]

    expected_headers_with_empty_key = {"X-CMC_PRO_API_KEY": "", "Accept": "application/json"}
    mock_requests_get.assert_called_once_with(ANY, headers=expected_headers_with_empty_key, params=ANY)

@patch('requests.get')
def test_run_api_error_non_200(mock_requests_get):
    """Test _run with a non-200 API error response."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error: 503" in result_data["error"]

@patch('requests.get')
def test_run_no_data_found_empty_list(mock_requests_get):
    """Test _run when API returns 200 but the data list is empty."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}, "data": []}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert isinstance(result_data, list)
    assert len(result_data) == 0

@patch('requests.get')
def test_run_malformed_response_no_data_key(mock_requests_get):
    """Test _run when API response is 200 but missing the 'data' key."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": {"error_code": 0}}
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "No cryptocurrency data found" in result_data["error"]

@patch('requests.get')
def test_run_requests_exception(mock_requests_get):
    """Test _run when requests.get raises an exception."""
    mock_requests_get.side_effect = requests.exceptions.Timeout("Connection Timed Out")

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Error retrieving cryptocurrency list: Connection Timed Out" in result_data["error"]

@patch('requests.get')
def test_run_json_decode_error(mock_requests_get):
    """Test _run when response.json() raises a JSONDecodeError."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Malformed JSON", "{}", 0)
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapListTool()
        result_json = tool._run()

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Error retrieving cryptocurrency list: Malformed JSON" in result_data["error"]


