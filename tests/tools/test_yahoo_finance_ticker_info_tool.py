import json
from unittest.mock import MagicMock, patch

import pytest

from epic_news.tools.yahoo_finance_ticker_info_tool import (
    GetTickerInfoInput,
    YahooFinanceTickerInfoTool,
)


@pytest.fixture
def ticker_info_tool_instance():
    """Provides a fresh instance of YahooFinanceTickerInfoTool."""
    return YahooFinanceTickerInfoTool()


# --- Test Instantiation ---
def test_tool_instantiation(ticker_info_tool_instance):
    assert ticker_info_tool_instance.name == "Yahoo Finance Ticker Info Tool"
    assert (
        "Get current information about stocks, ETFs, or cryptocurrencies"
        in ticker_info_tool_instance.description
    )
    assert ticker_info_tool_instance.args_schema == GetTickerInfoInput


# --- Test _run Method ---
@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_success_stock(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Apple Inc.",
        "currency": "USD",
        "currentPrice": 150.00,
        "previousClose": 149.00,
        "marketCap": 2500000000000,
        "volume": 100000000,
        "averageVolume": 90000000,
        "fiftyTwoWeekHigh": 180.00,
        "fiftyTwoWeekLow": 120.00,
        "trailingPE": 25.5,
        "dividendYield": 0.006,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="AAPL")
    result_data = json.loads(result_str)

    expected_data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "currency": "USD",
        "current_price": 150.00,
        "previous_close": 149.00,
        "market_cap": 2500000000000,
        "volume": 100000000,
        "average_volume": 90000000,
        "52wk_high": 180.00,
        "52wk_low": 120.00,
        "pe_ratio": 25.5,
        "dividend_yield": 0.006,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }
    assert result_data == expected_data
    mock_yfinance_ticker.assert_called_once_with("AAPL")


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_success_etf(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Vanguard Total Stock Market ETF",
        "currency": "USD",
        "regularMarketPrice": 230.50, # Using regularMarketPrice
        "previousClose": 229.80,
        "marketCap": 1300000000000, # ETFs can have marketCap (Net Assets)
        "volume": 3000000,
        "averageVolume": 2500000,
        "fiftyTwoWeekHigh": 250.00,
        "fiftyTwoWeekLow": 200.00,
        # ETFs typically don't have PE, dividendYield directly, sector, industry
    }
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="VTI")
    result_data = json.loads(result_str)

    expected_data = {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "currency": "USD",
        "current_price": 230.50,
        "previous_close": 229.80,
        "market_cap": 1300000000000,
        "volume": 3000000,
        "average_volume": 2500000,
        "52wk_high": 250.00,
        "52wk_low": 200.00,
    }
    assert result_data == expected_data
    mock_yfinance_ticker.assert_called_once_with("VTI")


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_success_crypto(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Bitcoin USD",
        "currency": "USD",
        "currentPrice": 40000.00,
        "previousClose": 39000.00,
        "marketCap": 750000000000,
        "volume": 25000000000,
        # Crypto might not have averageVolume, 52wk high/low from some sources or yf
        "fiftyTwoWeekHigh": 69000.00, # Assuming it's available
        "fiftyTwoWeekLow": 28000.00,  # Assuming it's available
    }
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="BTC-USD")
    result_data = json.loads(result_str)

    expected_data = {
        "symbol": "BTC-USD",
        "name": "Bitcoin USD",
        "currency": "USD",
        "current_price": 40000.00,
        "previous_close": 39000.00,
        "market_cap": 750000000000,
        "volume": 25000000000,
        "52wk_high": 69000.00,
        "52wk_low": 28000.00,
    }
    assert result_data == expected_data
    mock_yfinance_ticker.assert_called_once_with("BTC-USD")


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_success_with_regular_market_price(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Test Ticker",
        "currency": "USD",
        "regularMarketPrice": 99.00, # No currentPrice
        "previousClose": 98.00,
    }
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="TEST")
    result_data = json.loads(result_str)

    assert result_data["current_price"] == 99.00
    assert result_data["name"] == "Test Ticker"


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_minimal_data(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Minimal Corp",
        "currency": "EUR",
        # All other expected fields are missing
    }
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="MINI")
    result_data = json.loads(result_str)

    expected_data = {
        "symbol": "MINI",
        "name": "Minimal Corp",
        "currency": "EUR",
    }
    # Check that only expected keys are present (others were "N/A" and removed)
    assert result_data == expected_data
    assert len(result_data.keys()) == 3


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_yfinance_exception(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_yfinance_ticker.side_effect = Exception("Test yfinance error")

    result_str = ticker_info_tool_instance._run(ticker="ERROR")
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert (
        result_data["error"] == "Failed to get ticker info for ERROR: Test yfinance error"
    )


@patch("epic_news.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
def test_run_invalid_ticker_empty_info(mock_yfinance_ticker, ticker_info_tool_instance):
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.info = {}  # yfinance returns empty dict for some invalid tickers
    mock_yfinance_ticker.return_value = mock_ticker_instance

    result_str = ticker_info_tool_instance._run(ticker="INVALID")
    result_data = json.loads(result_str)

    # Only symbol should be present as all other fields default to N/A and are removed
    expected_data = {"symbol": "INVALID"}
    assert result_data == expected_data
