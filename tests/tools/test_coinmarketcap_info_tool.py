# tests/tools/test_coinmarketcap_info_tool.py
import json
import os

import pytest
import requests

from epic_news.tools.coinmarketcap_info_tool import (
    CoinInfoInput,
    CoinMarketCapInfoTool,
)

TEST_CMC_API_KEY = "test_cmc_api_key_info_123"
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


@pytest.fixture
def tool_for_instantiation_test(mocker):
    """Fixture for CoinMarketCapInfoTool instantiation testing."""
    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    return CoinMarketCapInfoTool()


def test_instantiation_success(tool_for_instantiation_test):
    """Test successful instantiation of CoinMarketCapInfoTool."""
    assert tool_for_instantiation_test.name == "CoinMarketCap Cryptocurrency Info"
    assert (
        "Get detailed information about a specific cryptocurrency" in tool_for_instantiation_test.description
    )
    assert tool_for_instantiation_test.args_schema == CoinInfoInput


def test_run_successful_response(mocker):
    """Test _run method with a successful API response."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {
            "timestamp": "2023-10-27T00:00:00.000Z",
            "error_code": 0,
            "error_message": None,
            "elapsed": 10,
            "credit_count": 1,
        },
        "data": {
            "BTC": {
                "id": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "slug": "bitcoin",
                "circulating_supply": 19000000,
                "max_supply": 21000000,
                "cmc_rank": 1,
                "platform": None,
                "tags": ["mineable", "pow", "sha-256"],
                "quote": {
                    "USD": {
                        "price": 30000.00,
                        "volume_24h": 25000000000,
                        "percent_change_24h": 1.5,
                        "percent_change_7d": -2.3,
                        "market_cap": 570000000000,
                        "last_updated": "2023-10-27T10:00:00.000Z",
                    }
                },
            }
        },
    }
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="BTC")

    result_data = json.loads(result_json)

    assert result_data["name"] == "Bitcoin"
    assert result_data["symbol"] == "BTC"
    assert result_data["price_usd"] == 30000.00
    assert result_data["market_cap_usd"] == 570000000000
    assert result_data["circulating_supply"] == 19000000
    assert result_data["cmc_rank"] == 1
    assert "mineable" in result_data["tags"]

    expected_url = f"{CMC_BASE_URL}/cryptocurrency/quotes/latest"
    expected_params = {"symbol": "BTC", "convert": "USD"}
    expected_headers = {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY, "Accept": "application/json"}

    mock_requests_get.assert_called_once_with(expected_url, headers=expected_headers, params=expected_params)


def test_run_api_key_missing(mocker):
    """Test _run when API key is missing (simulated by empty string)."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 401  # Simulate unauthorized due to bad/missing key
    mock_response.text = "Unauthorized - API Key missing or invalid"
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": ""}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="ETH")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error: 401" in result_data["error"]

    expected_headers_with_empty_key = {"X-CMC_PRO_API_KEY": "", "Accept": "application/json"}
    mock_requests_get.assert_called_once_with(
        f"{CMC_BASE_URL}/cryptocurrency/quotes/latest",
        headers=expected_headers_with_empty_key,
        params={"symbol": "ETH", "convert": "USD"},
    )


def test_run_api_error_non_200(mocker):
    """Test _run with a non-200 API error response."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="ADA")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "CoinMarketCap API error: 500" in result_data["error"]
    assert "Internal Server Error" in result_data["error"]


def test_run_symbol_not_found(mocker):
    """Test _run when the API returns 200 but the symbol data is missing."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"error_code": 0},
        "data": {},  # Empty data, symbol 'XYZ' won't be found
    }
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="XYZ")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "No data found for cryptocurrency symbol: XYZ" in result_data["error"]


def test_run_malformed_response_no_data_key(mocker):
    """Test _run when API response is 200 but missing the 'data' key."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": {"error_code": 0}
        # Missing 'data' key entirely
    }
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="LTC")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "No data found for cryptocurrency symbol: LTC" in result_data["error"]


def test_run_requests_exception(mocker):
    """Test _run when requests.get raises an exception."""
    mock_requests_get = mocker.patch("requests.get")
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network Error")

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="DOT")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Error retrieving cryptocurrency data for DOT: Network Error" in result_data["error"]


def test_run_json_decode_error(mocker):
    """Test _run when response.json() raises a JSONDecodeError."""
    mock_requests_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "{}", 0)
    mock_requests_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"X-CMC_PRO_API_KEY": TEST_CMC_API_KEY}, clear=True)
    tool = CoinMarketCapInfoTool()
    result_json = tool._run(symbol="SOL")

    result_data = json.loads(result_json)
    assert "error" in result_data
    assert "Error retrieving cryptocurrency data for SOL: Invalid JSON" in result_data["error"]
