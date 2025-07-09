import json

import pytest
import requests

from src.epic_news.tools.cache_manager import get_cache_manager
from src.epic_news.tools.kraken_api_tool import KrakenTickerInfoTool


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test to prevent interference."""
    cache = get_cache_manager()
    cache.clear()
    yield
    cache.clear()


# --- Instantiation Tests ---
def test_instantiation():
    tool = KrakenTickerInfoTool()
    assert tool.name == "Kraken Ticker Information"
    assert "Kraken" in tool.description


# --- _run Method Tests ---
def test_run_success(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
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
        },
    }
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_requests_get.return_value = mock_response

    result_str = tool._run(pair=pair_to_search)
    expected_output = json.dumps(mock_response_data["result"][pair_to_search], indent=2)
    assert result_str == expected_output


def test_run_api_returns_error_in_json(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
    tool = KrakenTickerInfoTool()
    pair_to_search = "INVALIDPAIR"
    mock_response_data = {"error": ["EQuery:Unknown asset pair"]}
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_requests_get.return_value = mock_response

    result_str = tool._run(pair=pair_to_search)
    expected_error_message = f"Error from Kraken API: {mock_response_data['error']}"
    assert result_str == expected_error_message


def test_run_api_returns_empty_result(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
    tool = KrakenTickerInfoTool()
    pair_to_search = "UNKNOWNPAIR"
    mock_response_data = {"error": [], "result": {}}
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_requests_get.return_value = mock_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"No data found for pair {pair_to_search}. It may be an invalid pair."
    assert result_str == expected_message


def test_run_requests_exception(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    error_message = "Network error"
    mock_requests_get.side_effect = requests.exceptions.RequestException(error_message)

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"Error fetching data from Kraken: {error_message}"
    assert result_str == expected_message


def test_run_http_error(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    error_message = "404 Client Error"
    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(error_message)
    mock_requests_get.return_value = mock_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = f"Error fetching data from Kraken: {error_message}"
    assert result_str == expected_message


def test_run_json_decode_error(mocker):
    mock_requests_get = mocker.patch("src.epic_news.tools.kraken_api_tool.requests.get")
    tool = KrakenTickerInfoTool()
    pair_to_search = "XXBTZUSD"
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_requests_get.return_value = mock_response

    result_str = tool._run(pair=pair_to_search)
    expected_message = "Error: Failed to parse JSON response from Kraken."
    assert result_str == expected_message
