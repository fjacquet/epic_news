import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from epic_news.tools.exchange_rate_tool import ExchangeRateTool


@pytest.fixture
@patch.dict(os.environ, {"OPENEXCHANGERATES_API_KEY": "test_api_key"})
def tool():
    return ExchangeRateTool()


@patch.dict(os.environ, {}, clear=True)
def test_run_missing_api_key():
    tool_no_key = ExchangeRateTool()
    expected_error = "Error: OPENEXCHANGERATES_API_KEY environment variable not set. Please get an API key from openexchangerates.org."
    assert tool_no_key.run(base_currency="USD", target_currencies=["EUR"]) == expected_error


@patch('requests.get')
def test_run_successful_all_rates(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "disclaimer": "...",
        "license": "...",
        "timestamp": 1678886400,
        "base": "USD",
        "rates": {
            "EUR": 0.93,
            "CHF": 0.91,
            "GBP": 0.82
        }
    }
    mock_get.return_value = mock_response

    result = tool.run(base_currency="USD", target_currencies=None)
    assert "Exchange rates based on USD at timestamp 1678886400" in result
    assert "'EUR': 0.93" in result
    assert "'CHF': 0.91" in result
    assert "'GBP': 0.82" in result
    mock_get.assert_called_once_with(
        "https://openexchangerates.org/api/latest.json",
        params={'app_id': 'test_api_key', 'base': 'USD'}
    )


@patch('requests.get')
def test_run_successful_specific_currencies(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "timestamp": 1678886400,
        "base": "USD",
        "rates": {
            "EUR": 0.93,
            "CHF": 0.91,
            # GBP is intentionally omitted by API due to 'symbols' param
        }
    }
    mock_get.return_value = mock_response

    result = tool.run(base_currency="USD", target_currencies=["EUR", "CHF"])
    assert "Exchange rates based on USD at timestamp 1678886400" in result
    assert "'EUR': 0.93" in result
    assert "'CHF': 0.91" in result
    assert "GBP" not in result
    mock_get.assert_called_once_with(
        "https://openexchangerates.org/api/latest.json",
        params={'app_id': 'test_api_key', 'base': 'USD', 'symbols': 'EUR,CHF'}
    )


@patch('requests.get')
def test_run_api_error_in_response(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 200  # API can return 200 but still have an error in JSON
    mock_response.json.return_value = {
        "error": True,
        "status": 401,
        "message": "invalid_app_id",
        "description": "Invalid App ID provided."
    }
    mock_get.return_value = mock_response

    result = tool.run(base_currency="USD")
    assert result == "API Error: Invalid App ID provided."


@patch('requests.get')
def test_run_http_error(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    mock_get.return_value = mock_response

    result = tool.run(base_currency="USD")
    assert "HTTP error occurred: 500 Server Error" in result
    assert "Response: Internal Server Error" in result


@patch('requests.get')
def test_run_request_exception(mock_get, tool):
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
    result = tool.run(base_currency="USD")
    assert result == "Request error occurred: Connection timed out"


@patch('requests.get')
def test_run_no_rates_in_response(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "timestamp": 1678886400,
        "base": "USD"
        # 'rates' key is missing
    }
    mock_get.return_value = mock_response
    result = tool.run(base_currency="USD")
    assert result == "Error: Could not retrieve exchange rates from the API response."


@patch('requests.get')
def test_run_no_rates_for_specified_targets(mock_get, tool):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "timestamp": 1678886400,
        "base": "USD",
        "rates": {"XYZ": 1.0}  # None of the target currencies are present
    }
    mock_get.return_value = mock_response
    target_currencies = ["EUR", "CHF"]
    result = tool.run(base_currency="USD", target_currencies=target_currencies)
    expected_msg = f"Error: No rates found for the specified target currencies: {target_currencies} with base USD"
    assert result == expected_msg
