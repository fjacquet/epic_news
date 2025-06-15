# tests/tools/test_coinmarketcap_historical_tool.py
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from epic_news.tools.coinmarketcap_historical_tool import (
    CoinMarketCapHistoricalTool,
    CryptocurrencyHistoricalInput,
)

TEST_CMC_API_KEY = "test_cmc_api_key_123"
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Test Instantiation - Uses a simple fixture as _run is not called
@pytest.fixture
def tool_for_instantiation_test():
    # This patch is for instantiation time if the tool read env vars in __init__
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
    return tool

def test_instantiation_success(tool_for_instantiation_test):
    """Test successful instantiation of CoinMarketCapHistoricalTool."""
    assert tool_for_instantiation_test.name == "CoinMarketCap Historical Data"
    assert tool_for_instantiation_test.description is not None
    assert tool_for_instantiation_test.args_schema == CryptocurrencyHistoricalInput

# Test _run method
@patch('requests.get')
def test_run_successful_response(mock_requests_get): # No fixture for the tool here
    """Test _run method with a successful API response for both ID and historical data."""
    mock_id_response = MagicMock()
    mock_id_response.status_code = 200
    mock_id_response.json.return_value = {
        "status": {"timestamp": "2023-10-27T00:00:00.000Z", "error_code": 0, "error_message": None, "elapsed": 10, "credit_count": 1},
        "data": [{"id": 1, "name": "Bitcoin", "symbol": "BTC", "slug": "bitcoin"}]
    }
    
    mock_historical_response = MagicMock()
    mock_historical_response.status_code = 200
    mock_historical_response.json.return_value = {
        "status": {"timestamp": "2023-10-27T00:00:00.000Z", "error_code": 0, "error_message": None, "elapsed": 10, "credit_count": 1},
        "data": {
            "id": 1, "name": "Bitcoin", "symbol": "BTC",
            "quotes": [
                {
                    "time_open": "2023-09-27T00:00:00.000Z", "time_close": "2023-09-27T23:59:59.999Z", "time_high": "2023-09-27T12:00:00.000Z", "time_low": "2023-09-27T06:00:00.000Z",
                    "quote": {
                        "USD": {"price": 26000.00, "volume_24h": 15000000000, "market_cap": 500000000000, "timestamp": "2023-09-27T23:59:59.999Z", "percent_change_24h": 0.5}
                    }
                }
            ]
        }
    }
    mock_requests_get.side_effect = [mock_id_response, mock_historical_response]

    # Patch environment and instantiate/run tool INSIDE this context
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool() 
        result_json = tool._run(symbol="BTC", time_period="30d")
    
    result_data = json.loads(result_json)

    assert result_data["symbol"] == "BTC"
    assert result_data["time_period"] == "30d"
    assert result_data["interval"] == "daily"
    assert len(result_data["historical_data"]) == 1
    assert result_data["historical_data"][0]["price_usd"] == 26000.00

    expected_id_url = f"{CMC_BASE_URL}/cryptocurrency/map"
    expected_id_params = {"symbol": "BTC"}
    expected_headers = {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY, "Accept": "application/json"}
    
    expected_historical_url = f"{CMC_BASE_URL}/cryptocurrency/quotes/historical"
    expected_historical_params = {"id": 1, "convert": "USD", "interval": "daily", "time_period": "30d"}

    assert mock_requests_get.call_count == 2
    call_args_list = mock_requests_get.call_args_list
    
    # Call 1: ID lookup
    assert call_args_list[0].args[0] == expected_id_url
    assert call_args_list[0].kwargs['headers'] == expected_headers
    assert call_args_list[0].kwargs['params'] == expected_id_params
    
    # Call 2: Historical data
    assert call_args_list[1].args[0] == expected_historical_url
    assert call_args_list[1].kwargs['headers'] == expected_headers # Should use the same patched headers
    assert call_args_list[1].kwargs['params'] == expected_historical_params

@patch('requests.get')
def test_run_api_key_missing_simulated_by_id_failure(mock_requests_get):
    mock_id_response_fail = MagicMock()
    mock_id_response_fail.status_code = 401
    mock_id_response_fail.text = "Unauthorized - API Key issue"
    mock_requests_get.return_value = mock_id_response_fail
    
    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": ""}, clear=True): 
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="BTC", time_period="7d")
    
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error retrieving ID: 401" in result_data["error"]
    
    expected_headers_with_empty_key = {"X-CMC_PRO_API_KEY": "", "Accept": "application/json"} 
    mock_requests_get.assert_called_once_with(
        f"{CMC_BASE_URL}/cryptocurrency/map", 
        headers=expected_headers_with_empty_key, 
        params={"symbol": "BTC"}
    )

@patch('requests.get')
def test_run_id_lookup_fails_not_200(mock_requests_get):
    mock_id_response_fail = MagicMock()
    mock_id_response_fail.status_code = 500
    mock_id_response_fail.text = "Server Error"
    mock_requests_get.return_value = mock_id_response_fail

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="FAIL", time_period="24h")
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error retrieving ID: 500 - Server Error" in result_data["error"]

@patch('requests.get')
def test_run_id_not_found_for_symbol(mock_requests_get):
    mock_id_response_no_data = MagicMock()
    mock_id_response_no_data.status_code = 200
    mock_id_response_no_data.json.return_value = {"status": {}, "data": []} 
    mock_requests_get.return_value = mock_id_response_no_data

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="UNKNOWN", time_period="30d")
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "No ID found for cryptocurrency symbol: UNKNOWN" in result_data["error"]

@patch('requests.get')
def test_run_id_unexpected_data_format(mock_requests_get):
    mock_id_response_bad_format = MagicMock()
    mock_id_response_bad_format.status_code = 200
    mock_id_response_bad_format.json.return_value = {"status": {}, "data": {"id": 1}} 
    mock_requests_get.return_value = mock_id_response_bad_format

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="BADFORMAT", time_period="30d")
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Unexpected ID data format for symbol: BADFORMAT" in result_data["error"]

@patch('requests.get')
def test_run_historical_lookup_fails_not_200(mock_requests_get):
    mock_id_response = MagicMock()
    mock_id_response.status_code = 200
    mock_id_response.json.return_value = {"data": [{"id": 1, "symbol": "BTC"}]}

    mock_historical_fail = MagicMock()
    mock_historical_fail.status_code = 503
    mock_historical_fail.text = "Service Unavailable"
    mock_requests_get.side_effect = [mock_id_response, mock_historical_fail]

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="BTC", time_period="30d")
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error retrieving historical data: 503" in result_data["error"]

@patch('requests.get')
def test_run_no_historical_data_found(mock_requests_get):
    mock_id_response = MagicMock()
    mock_id_response.status_code = 200
    mock_id_response.json.return_value = {"data": [{"id": 1, "symbol": "BTC"}]}

    mock_historical_no_data = MagicMock()
    mock_historical_no_data.status_code = 200
    mock_historical_no_data.json.return_value = {"status": {}, "data": {"id": 1}} 
    mock_requests_get.side_effect = [mock_id_response, mock_historical_no_data]

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="BTC", time_period="1y")
    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "No historical data found for BTC over 1y" in result_data["error"]

@patch('requests.get')
def test_run_general_exception_during_processing(mock_requests_get):
    mock_id_response = MagicMock()
    mock_id_response.status_code = 200
    mock_id_response.json.return_value = {"data": [{"id": 1, "symbol": "BTC"}]}
    
    # Simulate an unexpected error during the second call's processing within the tool
    # or by the requests.get call itself for the second call.
    mock_requests_get.side_effect = [mock_id_response, Exception("Unexpected general error")]

    with patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True):
        tool = CoinMarketCapHistoricalTool()
        result_json = tool._run(symbol="BTC", time_period="30d")
    result_data = json.loads(result_json)
    assert "error" in result_data
    # Check that the error message includes the symbol and the specific exception message
    assert "Error retrieving historical data for BTC: Unexpected general error" in result_data["error"]
