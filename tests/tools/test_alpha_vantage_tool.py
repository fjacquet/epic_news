# tests/tools/test_alpha_vantage_tool.py
import json
import os
import pytest
import requests # Added import
from unittest.mock import patch, MagicMock

from epic_news.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool, CompanyOverviewInput

TEST_ALPHA_VANTAGE_API_KEY = "test_alpha_vantage_key_123"

# Test Instantiation
def test_alpha_vantage_tool_instantiation_success():
    """Test successful instantiation of AlphaVantageCompanyOverviewTool."""
    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
    assert tool.name == "Alpha Vantage Company Overview"
    assert tool.description is not None
    assert tool.args_schema == CompanyOverviewInput

def test_alpha_vantage_tool_instantiation_no_api_key_env():
    """
    Test tool behavior during _run when ALPHA_VANTAGE_API_KEY is not set.
    Instantiation itself should pass, but _run should fail gracefully.
    """
    # Ensure API key is not in environ for this test
    with patch.dict(os.environ, {}, clear=True):
        tool = AlphaVantageCompanyOverviewTool()
        # Instantiation should not fail, the check is in _run
        assert tool is not None
        result = tool._run(ticker="AAPL")
        assert "ALPHA_VANTAGE_API_KEY environment variable not set" in result

# Test _run method
@patch('requests.get')
def test_run_successful_response(mock_requests_get):
    """Test _run method with a successful API response."""
    mock_response = MagicMock()
    mock_api_data = {"Symbol": "AAPL", "CompanyName": "Apple Inc.", "MarketCapitalization": "2000B"}
    mock_response.json.return_value = mock_api_data
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock() # Ensure it doesn't raise for 200
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
        result_json = tool._run(ticker="AAPL")
    
    result_data = json.loads(result_json)
    assert result_data == mock_api_data
    
    expected_url = (
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL"
        f"&apikey={TEST_ALPHA_VANTAGE_API_KEY}"
    )
    mock_requests_get.assert_called_once_with(expected_url, timeout=10)


@patch('requests.get')
def test_run_api_http_error(mock_requests_get):
    """Test _run method when Alpha Vantage API returns an HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
        result = tool._run(ticker="FAIL")
    
    assert "Error fetching data from Alpha Vantage: Server Error" in result
    expected_url = (
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=FAIL"
        f"&apikey={TEST_ALPHA_VANTAGE_API_KEY}"
    )
    mock_requests_get.assert_called_once_with(expected_url, timeout=10)

@patch('requests.get')
def test_run_invalid_json_response(mock_requests_get):
    """Test _run method when Alpha Vantage API returns invalid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError("Error decoding JSON", "doc", 0)
    mock_requests_get.return_value = mock_response

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
        result = tool._run(ticker="JSONERR")
        
    assert "Error: Failed to parse JSON response from Alpha Vantage" in result

@patch('requests.get')
def test_run_api_returns_note_or_empty(mock_requests_get):
    """Test _run method when API returns a 'Note' (e.g. rate limit) or empty data."""
    # Scenario 1: API returns a "Note"
    mock_response_note = MagicMock()
    mock_response_note.status_code = 200
    mock_response_note.raise_for_status = MagicMock()
    mock_response_note.json.return_value = {"Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."}
    mock_requests_get.return_value = mock_response_note

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
        result_note = tool._run(ticker="NOTE")
    assert "No data found for ticker NOTE. It might be an invalid symbol." in result_note
    mock_requests_get.assert_called_with(
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=NOTE&apikey={TEST_ALPHA_VANTAGE_API_KEY}",
        timeout=10
    )
    
    # Scenario 2: API returns empty data
    mock_requests_get.reset_mock() # Reset for the next call
    mock_response_empty = MagicMock()
    mock_response_empty.status_code = 200
    mock_response_empty.raise_for_status = MagicMock()
    mock_response_empty.json.return_value = {} # Empty dictionary
    mock_requests_get.return_value = mock_response_empty

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool() # Re-instantiate or ensure state is clean if needed
        result_empty = tool._run(ticker="EMPTY")
    assert "No data found for ticker EMPTY. It might be an invalid symbol." in result_empty
    mock_requests_get.assert_called_with(
        f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=EMPTY&apikey={TEST_ALPHA_VANTAGE_API_KEY}",
        timeout=10
    )


@patch('requests.get')
def test_run_network_request_exception(mock_requests_get):
    """Test _run method when a requests.exceptions.RequestException occurs."""
    network_error_message = "Simulated network error"
    mock_requests_get.side_effect = requests.exceptions.RequestException(network_error_message)

    with patch.dict(os.environ, {"ALPHA_VANTAGE_API_KEY": TEST_ALPHA_VANTAGE_API_KEY}):
        tool = AlphaVantageCompanyOverviewTool()
        result = tool._run(ticker="NETERR")
        
    assert f"Error fetching data from Alpha Vantage: {network_error_message}" in result

# More tests will follow for API errors, invalid ticker, network issues etc.
