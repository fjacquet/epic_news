import json

import pandas as pd
import pytest

from epic_news.tools.yahoo_finance_etf_holdings_tool import GetETFHoldingsInput, YahooFinanceETFHoldingsTool


@pytest.fixture
def tool_instance():
    return YahooFinanceETFHoldingsTool()


@pytest.fixture
def mock_etf_data_all_present(mocker):
    mock_ticker_instance = mocker.MagicMock()
    mock_ticker_instance.info = {
        "shortName": "Good ETF Full",
        "categoryName": "Large Cap Blend",
        "annualReportExpenseRatio": 0.0003,  # yfinance often returns float for this
        "totalAssets": 300000000000,
    }

    holdings_list = []
    for i in range(15):
        holdings_list.append(
            {
                "symbol": f"SYM{i}",
                "Name": f"Company {i}",
                "% Assets": 0.05 - (i * 0.001),
                "Shares": 1000 + i * 10,
            }
        )
    # Create DataFrame with symbols as index
    mock_ticker_instance.get_holdings.return_value = pd.DataFrame(
        [{k: v for k, v in h.items() if k != "symbol"} for h in holdings_list],
        index=[h["symbol"] for h in holdings_list],
    )

    mock_ticker_instance.get_sector_data.return_value = {
        "Technology": 0.25,
        "Healthcare": 0.15,
        "Financial Services": 0.20,
    }
    return mock_ticker_instance


# --- Instantiation Tests ---
def test_instantiation(tool_instance):
    assert tool_instance.name == "Yahoo Finance ETF Holdings Tool"
    assert "Get detailed holdings information for ETFs" in tool_instance.description
    assert tool_instance.args_schema == GetETFHoldingsInput


# --- _run Method Tests ---
def test_run_successful_all_data(tool_instance, mock_etf_data_all_present, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "GOODETF"
    mock_yf_ticker.return_value = mock_etf_data_all_present

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    mock_yf_ticker.assert_called_once_with(ticker_symbol)
    assert result_data["symbol"] == ticker_symbol
    assert result_data["name"] == "Good ETF Full"
    assert result_data["asset_class"] == "Large Cap Blend"
    assert result_data["expense_ratio"] == 0.0003
    assert result_data["aum"] == 300000000000
    assert len(result_data["top_holdings"]) == 10
    assert result_data["top_holdings"][0]["symbol"] == "SYM0"
    assert result_data["top_holdings"][0]["name"] == "Company 0"
    assert result_data["top_holdings"][0]["weight"] == 0.05
    assert result_data["sector_breakdown"] == {
        "Technology": 0.25,
        "Healthcare": 0.15,
        "Financial Services": 0.20,
    }


def test_run_missing_data_empty_collections(tool_instance, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "EMPTYETF"
    mock_ticker_instance = mocker.MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance

    mock_ticker_instance.info = {
        "shortName": "Emptyish ETF",
        "categoryName": "N/A",  # This should be removed
        "annualReportExpenseRatio": None,  # This will be N/A, then removed
        "totalAssets": 10000,
    }
    mock_ticker_instance.get_holdings.return_value = pd.DataFrame()  # Empty holdings
    mock_ticker_instance.get_sector_data.return_value = {}  # Empty sector data

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    expected_data = {
        "symbol": ticker_symbol,
        "name": "Emptyish ETF",
        "expense_ratio": None,  # Kept as it's not "N/A" or []
        "aum": 10000,
        "sector_breakdown": {},  # Empty dict for sectors is kept if other data present
    }
    assert result_data == expected_data
    assert "asset_class" not in result_data  # Was N/A
    # expense_ratio being None is now checked by the expected_data comparison
    assert "top_holdings" not in result_data  # Was []


def test_run_get_holdings_fails(tool_instance, mock_etf_data_all_present, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "FAILHOLDETF"
    # Use the all_present mock but override get_holdings
    mock_ticker_instance = mock_etf_data_all_present
    mock_yf_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.get_holdings.side_effect = Exception("Holdings fetch failed")
    # Ensure info is not from the fixture for this specific test path if needed, or use parts of it
    mock_ticker_instance.info = {"shortName": "ETF With Failing Holdings"}

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert result_data["symbol"] == ticker_symbol
    assert result_data["name"] == "ETF With Failing Holdings"
    assert "top_holdings" not in result_data
    # Sector data should still be there from the original mock_etf_data_all_present if not overridden
    assert "sector_breakdown" in result_data


def test_run_get_sector_data_fails(tool_instance, mock_etf_data_all_present, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "FAILSECTETF"
    mock_ticker_instance = mock_etf_data_all_present
    mock_yf_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.get_sector_data.side_effect = Exception("Sector fetch failed")
    mock_ticker_instance.info = {"shortName": "ETF With Failing Sectors"}

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert result_data["symbol"] == ticker_symbol
    assert result_data["name"] == "ETF With Failing Sectors"
    assert result_data["sector_breakdown"] == {}  # Should default to empty dict
    assert "top_holdings" in result_data  # Holdings should be there


def test_run_holdings_df_missing_internal_fields(tool_instance, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "PARTIALHOLDETF"
    mock_ticker_instance = mocker.MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.info = {"shortName": "Partial Holdings ETF"}

    # DataFrame with missing Name, % Assets, Shares in different rows
    data = {
        "SYM1": {"Name": "Company 1", "% Assets": 0.1, "Shares": 100},
        "SYM2": {"% Assets": 0.05, "Shares": 50},  # Missing Name
        "SYM3": {"Name": "Company 3", "Shares": 30},  # Missing % Assets
        "SYM4": {"Name": "Company 4", "% Assets": 0.02},  # Missing Shares
    }
    mock_ticker_instance.get_holdings.return_value = pd.DataFrame.from_dict(data, orient="index")
    mock_ticker_instance.get_sector_data.return_value = {}

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert len(result_data["top_holdings"]) == 4

    # Find holdings by symbol to make assertions robust to order
    holdings_by_symbol = {h["symbol"]: h for h in result_data["top_holdings"]}

    assert holdings_by_symbol["SYM1"]["name"] == "Company 1"
    assert holdings_by_symbol["SYM1"]["weight"] == 0.1
    assert holdings_by_symbol["SYM1"]["shares"] == 100

    assert holdings_by_symbol["SYM2"]["name"] == "N/A"
    assert holdings_by_symbol["SYM2"]["weight"] == 0.05
    assert holdings_by_symbol["SYM2"]["shares"] == 50

    assert holdings_by_symbol["SYM3"]["name"] == "Company 3"
    assert holdings_by_symbol["SYM3"]["weight"] == "N/A"
    assert holdings_by_symbol["SYM3"]["shares"] == 30

    assert holdings_by_symbol["SYM4"]["name"] == "Company 4"
    assert holdings_by_symbol["SYM4"]["weight"] == 0.02
    assert holdings_by_symbol["SYM4"]["shares"] == "N/A"


def test_run_yfinance_ticker_instantiation_fails(tool_instance, mocker):
    mock_yf_ticker = mocker.patch("yfinance.Ticker")
    ticker_symbol = "BADETF"
    error_message = "Failed to create Ticker"
    mock_yf_ticker.side_effect = Exception(error_message)

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert result_data == {"error": f"Failed to get ETF holdings for {ticker_symbol}: {error_message}"}
