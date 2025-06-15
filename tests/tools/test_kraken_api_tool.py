import json
from unittest.mock import MagicMock, patch

import requests

from epic_news.tools.kraken_api_tool import KrakenTickerInfoTool, TickerInfoInput

KRAKEN_API_TICKER_URL_TEMPLATE = "https://api.kraken.com/0/public/Ticker?pair={pair}"

# --- Instantiation Tests ---
def test_instantiation():
    tool = KrakenTickerInfoTool()
    assert tool.name == "Kraken Ticker Information"
    assert "Fetches real-time ticker information" in tool.description
    assert tool.args_schema == TickerInfoInput

# --- _run Method Tests ---
@patch('requests.get')
def test_run_success(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    mock_response_data = {
        "error": [],
        "result": {
            pair_to_search: {
                "a": ["50000.0", "1", "1.000"],
                "b": ["49999.0", "1", "1.000"],
                "c": ["50000.0", "0.001"],
            }
        }
    }
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = mock_response_data
    mock_api_response.raise_for_status.return_value = None # No HTTP error
    mock_requests_get.return_value = mock_api_response

    result_str = tool._run(pair=pair_to_search)
    expected_output = json.dumps(mock_response_data["result"][pair_to_search], indent=2)

    mock_requests_get.assert_called_once_with(
        KRAKEN_API_TICKER_URL_TEMPLATE.format(pair=pair_to_search),
        timeout=10
    )
    assert result_str == expected_output

@patch('requests.get')
def test_run_api_returns_error_in_json(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "INVALIDPAIR"
    mock_response_data = {"error": ["EGeneral:Invalid arguments"], "result": {}}
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = mock_response_data
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    result_str = tool._run(pair=pair_to_search)
    expected_error_message = f"Error from Kraken API: {mock_response_data['error']}"
    assert result_str == expected_error_message

@patch('requests.get')
def test_run_api_returns_empty_result(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "UNKNOWNPAIR"
    mock_response_data = {"error": [], "result": {}}
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = mock_response_data
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"No data found for pair {pair_to_search}. It may be an invalid pair."
    assert result_str == expected_message

@patch('requests.get')
def test_run_requests_exception(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    error_message = "Network error"
    mock_requests_get.side_effect = requests.exceptions.RequestException(error_message)

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"Error fetching data from Kraken: {error_message}"
    assert result_str == expected_message

@patch('requests.get')
def test_run_http_error(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    error_message = "404 Client Error"
    mock_api_response = MagicMock()
    mock_api_response.raise_for_status.side_effect = requests.exceptions.HTTPError(error_message)
    mock_requests_get.return_value = mock_api_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"Error fetching data from Kraken: {error_message}"
    assert result_str == expected_message

@patch('requests.get')
def test_run_json_decode_error(mock_requests_get):
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    mock_api_response = MagicMock()
    mock_api_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = "Error: Failed to parse JSON response from Kraken."
    assert result_str == expected_message
