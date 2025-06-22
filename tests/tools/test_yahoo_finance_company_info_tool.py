import json
from unittest.mock import MagicMock, patch

import pytest

from epic_news.tools.yahoo_finance_company_info_tool import GetCompanyInfoInput, YahooFinanceCompanyInfoTool


@pytest.fixture
def tool_instance():
    return YahooFinanceCompanyInfoTool()

# --- Instantiation Tests ---
def test_instantiation(tool_instance):
    assert tool_instance.name == "Yahoo Finance Company Info Tool"
    assert "Get detailed company information" in tool_instance.description
    assert tool_instance.args_schema == GetCompanyInfoInput

# --- _run Method Tests ---
@patch('yfinance.Ticker')
def test_run_successful_info_retrieval_all_fields(mock_yf_ticker, tool_instance):
    ticker_symbol = "GOODTICKER"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance

    mock_ticker_instance.info = {
        "longName": "Good Company Inc.",
        "industry": "Tech",
        "sector": "Software",
        "website": "goodcompany.com",
        "country": "USA",
        "fullTimeEmployees": 1000,
        "longBusinessSummary": "A great company.",
        "totalRevenue": 500000000,
        "profitMargins": 0.2,
        "ebitda": 100000000,
        "debtToEquity": 0.5,
        "returnOnEquity": 0.15,
        "revenueGrowth": 0.1,
        "earningsGrowth": 0.12,
        "marketCap": 1000000000,
        "trailingPE": 20,
        "forwardPE": 18,
        "priceToBook": 3,
        "priceToSalesTrailing12Months": 2
    }

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    mock_yf_ticker.assert_called_once_with(ticker_symbol)

    expected_data = {
        "symbol": ticker_symbol,
        "name": "Good Company Inc.",
        "industry": "Tech",
        "sector": "Software",
        "website": "goodcompany.com",
        "country": "USA",
        "employees": 1000,
        "business_summary": "A great company.",
        "financial_metrics": {
            "revenue": 500000000,
            "profit_margin": 0.2,
            "ebitda": 100000000,
            "debt_to_equity": 0.5,
            "return_on_equity": 0.15,
            "revenue_growth": 0.1,
            "earnings_growth": 0.12,
        },
        "valuation_metrics": {
            "market_cap": 1000000000,
            "pe_ratio": 20,
            "forward_pe": 18,
            "price_to_book": 3,
            "price_to_sales": 2,
        },
    }
    assert result_data == expected_data

@patch('yfinance.Ticker')
def test_run_successful_info_retrieval_some_fields_na(mock_yf_ticker, tool_instance):
    ticker_symbol = "MIXEDTICKER"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance

    mock_ticker_instance.info = {
        "longName": "Mixed Corp",
        "industry": "Retail",
        # sector is missing -> will be N/A and then removed
        "website": "mixed.com",
        "country": "Canada",
        "fullTimeEmployees": None, # -> will be N/A and then removed
        "longBusinessSummary": "A mixed bag.",
        "totalRevenue": 200000,
        "profitMargins": "N/A", # -> will be N/A and then removed from financial_metrics
        "ebitda": 50000,
        # debtToEquity is missing
        "returnOnEquity": 0.05,
        "marketCap": 1000000,
        "trailingPE": "N/A", # -> will be N/A and then removed from valuation_metrics
        "forwardPE": 15
        # priceToBook, priceToSalesTrailing12Months missing
    }

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    mock_yf_ticker.assert_called_once_with(ticker_symbol)

    expected_data = {
        "symbol": ticker_symbol,
        "name": "Mixed Corp",
        "industry": "Retail",
        "website": "mixed.com",
        "country": "Canada",
        "employees": None, # Added to reflect tool's behavior with None values
        "business_summary": "A mixed bag.",
        "financial_metrics": {
            "revenue": 200000,
            "ebitda": 50000,
            "return_on_equity": 0.05,
        },
        "valuation_metrics": {
            "market_cap": 1000000,
            "forward_pe": 15,
        },
    }
    # Check if financial_metrics or valuation_metrics are empty, they should be removed
    if not expected_data["financial_metrics"]:
        del expected_data["financial_metrics"]
    if not expected_data["valuation_metrics"]:
        del expected_data["valuation_metrics"]

    assert result_data == expected_data

@patch('yfinance.Ticker')
def test_run_empty_info_object(mock_yf_ticker, tool_instance):
    ticker_symbol = "EMPTYINFOTICKER"
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.info = {} # Empty info

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    # Expect only symbol as other fields would be N/A and removed
    # financial_metrics and valuation_metrics would be empty and thus removed by the tool's logic
    assert result_data == {"symbol": ticker_symbol}

@patch('yfinance.Ticker')
def test_run_yfinance_exception(mock_yf_ticker, tool_instance):
    ticker_symbol = "ERRORTICKER"
    error_message = "Test yfinance error"
    # Test two ways yfinance might raise an error related to .info
    # 1. Error on .info access
    mock_ticker_instance = MagicMock()
    mock_yf_ticker.return_value = mock_ticker_instance
    type(mock_ticker_instance).info = property(MagicMock(side_effect=Exception(error_message)))

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"Failed to get company info for {ticker_symbol}: {error_message}"}

    # 2. Error on Ticker instantiation
    mock_yf_ticker.reset_mock()
    mock_yf_ticker.side_effect = Exception(error_message)
    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"Failed to get company info for {ticker_symbol}: {error_message}"}
