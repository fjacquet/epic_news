import datetime
import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from epic_news.tools.yahoo_finance_history_tool import GetTickerHistoryInput, YahooFinanceHistoryTool


@pytest.fixture
def tool_instance():
    return YahooFinanceHistoryTool()

@pytest.fixture
def mock_history_dataframe_generator():
    def _generator(num_rows=15, start_price=100.0, all_fields_present=True):
        data = []
        dates = pd.to_datetime([datetime.date(2023, 1, 1) + datetime.timedelta(days=i) for i in range(num_rows)])
        for i in range(num_rows):
            row = {}
            if all_fields_present or 'Open' in locals() or i % 2 == 0: # ensure some data
                row['Open'] = start_price + i * 0.5
            if all_fields_present or 'High' in locals() or i % 2 == 0:
                row['High'] = start_price + i * 0.5 + 0.2
            if all_fields_present or 'Low' in locals() or i % 2 == 0:
                row['Low'] = start_price + i * 0.5 - 0.2
            if all_fields_present or 'Close' in locals() or i % 2 == 0:
                row['Close'] = start_price + i * 0.5 + 0.1
            if all_fields_present or 'Volume' in locals() or i % 2 == 0:
                row['Volume'] = 10000 + i * 100
            data.append(row)
        return pd.DataFrame(data, index=dates)
    return _generator

# --- Instantiation Tests ---
def test_instantiation(tool_instance):
    assert tool_instance.name == "Yahoo Finance History Tool"
    assert "Get historical price data (open, high, low, close, volume)" in tool_instance.description
    assert tool_instance.args_schema == GetTickerHistoryInput

# --- _run Method Tests ---
@patch('yfinance.Ticker')
def test_run_successful_history_retrieval(mock_yf_ticker, tool_instance, mock_history_dataframe_generator):
    ticker_symbol = "GOODHIST"
    period = "1mo"
    interval = "1d"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance

    df = mock_history_dataframe_generator(num_rows=15)
    mock_ticker_instance.history.return_value = df

    result_str = tool_instance._run(ticker=ticker_symbol, period=period, interval=interval)
    result_data = json.loads(result_str)

    mock_yf_ticker.assert_called_once_with(ticker_symbol)
    mock_ticker_instance.history.assert_called_once_with(period=period, interval=interval)

    assert "summary" in result_data
    assert "history" in result_data
    assert len(result_data["history"]) == 10 # Last 10 data points

    summary = result_data["summary"]
    assert summary["symbol"] == ticker_symbol
    assert summary["period"] == period
    assert summary["interval"] == interval
    assert summary["data_points"] == 15
    assert summary["start_date"] == "2023-01-01"
    assert summary["end_date"] == "2023-01-15"
    # Example check for one history item
    last_hist_item = result_data["history"][-1]
    assert last_hist_item["date"] == "2023-01-15"
    assert isinstance(last_hist_item["open"], float)
    assert isinstance(last_hist_item["volume"], int)

@patch('yfinance.Ticker')
def test_run_fewer_than_10_data_points(mock_yf_ticker, tool_instance, mock_history_dataframe_generator):
    ticker_symbol = "FEWHIST"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    df = mock_history_dataframe_generator(num_rows=5)
    mock_ticker_instance.history.return_value = df

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert len(result_data["history"]) == 5
    assert result_data["summary"]["data_points"] == 5

@patch('yfinance.Ticker')
def test_run_history_df_missing_ohlcv_fields(mock_yf_ticker, tool_instance, mock_history_dataframe_generator):
    ticker_symbol = "PARTIALHIST"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    # Generate a DataFrame where some OHLCV might be NaN due to all_fields_present=False
    df = mock_history_dataframe_generator(num_rows=3, all_fields_present=False)
    # Ensure at least 'Close' and 'Volume' have some non-NaN for summary, or make them NaN to test defaults
    df.loc[df.index[0], 'Close'] = pd.NA # Test default for earliest close in summary
    df.loc[df.index[0], 'Open'] = pd.NA  # Test default for Open
    mock_ticker_instance.history.return_value = df

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    first_hist_item = result_data["history"][0]
    assert first_hist_item["open"] == 0.0 # Defaulted due to pd.NA
    assert first_hist_item["close"] == 0.0 # Defaulted due to pd.NA
    assert isinstance(first_hist_item["volume"], int) # Will be 0 if Volume was NA

@patch('yfinance.Ticker')
def test_run_no_historical_data_empty_df(mock_yf_ticker, tool_instance):
    ticker_symbol = "NOHIST"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.history.return_value = pd.DataFrame() # Empty DataFrame

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"No historical data available for {ticker_symbol}"}

@patch('yfinance.Ticker')
def test_run_yfinance_exception(mock_yf_ticker, tool_instance):
    ticker_symbol = "ERRORHIST"
    error_message = "Test yfinance history error"
    mock_yf_ticker.side_effect = Exception(error_message)

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"Failed to get history for {ticker_symbol}: {error_message}"}

@patch('yfinance.Ticker')
def test_run_price_change_percent_earliest_close_zero(mock_yf_ticker, tool_instance, mock_history_dataframe_generator):
    ticker_symbol = "ZEROCLOSEHIST"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    df = mock_history_dataframe_generator(num_rows=2)
    df.loc[df.index[0], 'Close'] = 0.0 # First day close is 0
    df.loc[df.index[1], 'Close'] = 10.0 # Second day close is 10
    mock_ticker_instance.history.return_value = df

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    # (10 / 1 - 1) * 100 = 900.0
    assert result_data["summary"]["price_change_percent"] == 900.00
    assert result_data["summary"]["price_change"] == 10.0 # 10 - 0
