import datetime
import json

import pytest

from epic_news.tools.yahoo_finance_news_tool import GetTickerNewsInput, YahooFinanceNewsTool


@pytest.fixture
def tool_instance():
    return YahooFinanceNewsTool()


# --- Instantiation Tests ---
def test_instantiation(tool_instance):
    assert tool_instance.name == "Yahoo Finance News Tool"
    assert "Get recent news articles for stocks" in tool_instance.description
    assert tool_instance.args_schema == GetTickerNewsInput


# --- _run Method Tests ---
def test_run_successful_news_retrieval_with_limit(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "GOODNEWS"
    limit = 2
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance

    timestamp1 = int(datetime.datetime(2023, 1, 1, 10, 0, 0).timestamp())
    timestamp2 = int(datetime.datetime(2023, 1, 1, 12, 0, 0).timestamp())
    timestamp3 = int(datetime.datetime(2023, 1, 1, 14, 0, 0).timestamp())

    mock_ticker_instance.news = [
        {"title": "News 1", "publisher": "Pub A", "link": "link1.com", "providerPublishTime": timestamp1},
        {"title": "News 2", "publisher": "Pub B", "link": "link2.com", "providerPublishTime": timestamp2},
        {"title": "News 3", "publisher": "Pub C", "link": "link3.com", "providerPublishTime": timestamp3},
    ]

    result_str = tool_instance._run(ticker=ticker_symbol, limit=limit)
    result_data = json.loads(result_str)

    mock_yfinance_ticker.assert_called_once_with(ticker_symbol)
    assert result_data["ticker"] == ticker_symbol
    assert len(result_data["news"]) == limit
    assert result_data["news"][0]["title"] == "News 1"
    assert result_data["news"][0]["published_date"] == "2023-01-01 10:00"
    assert result_data["news"][1]["title"] == "News 2"
    assert result_data["news"][1]["published_date"] == "2023-01-01 12:00"


def test_run_successful_news_retrieval_fewer_than_limit(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "FEWNEWS"
    limit = 5
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    timestamp1 = int(datetime.datetime(2023, 2, 1, 10, 0, 0).timestamp())
    mock_ticker_instance.news = [
        {
            "title": "Only News",
            "publisher": "Pub X",
            "link": "link_only.com",
            "providerPublishTime": timestamp1,
        }
    ]

    result_str = tool_instance._run(ticker=ticker_symbol, limit=limit)
    result_data = json.loads(result_str)

    assert len(result_data["news"]) == 1
    assert result_data["news"][0]["title"] == "Only News"


def test_run_successful_news_retrieval_default_limit(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "DEFAULTLIMITNEWS"
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    # Create 7 news items
    mock_ticker_instance.news = [
        {
            "title": f"News {i}",
            "publisher": "Pub",
            "link": f"link{i}.com",
            "providerPublishTime": int(datetime.datetime.now().timestamp()),
        }
        for i in range(7)
    ]

    result_str = tool_instance._run(ticker=ticker_symbol)  # Default limit is 5
    result_data = json.loads(result_str)
    assert len(result_data["news"]) == 5


def test_run_no_news_found(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "NONEWS"
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.news = []

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)

    assert result_data == {"message": f"No recent news found for {ticker_symbol}."}


def test_run_news_item_missing_fields(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "MISSINGFIELDSNEWS"
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.news = [
        {"title": None, "publisher": "Pub D", "link": "link4.com", "providerPublishTime": None},
        {
            "title": "News E",
            "publisher": None,
            "link": None,
            "providerPublishTime": int(datetime.datetime.now().timestamp()),
        },
    ]

    result_str = tool_instance._run(ticker=ticker_symbol, limit=2)
    result_data = json.loads(result_str)

    assert len(result_data["news"]) == 2
    assert result_data["news"][0]["title"] == "No title"
    assert result_data["news"][0]["publisher"] == "Pub D"
    assert result_data["news"][0]["link"] == "link4.com"
    assert result_data["news"][0]["published_date"] == "Unknown date"

    assert result_data["news"][1]["title"] == "News E"
    assert result_data["news"][1]["publisher"] == "Unknown publisher"
    assert result_data["news"][1]["link"] == "#"
    assert isinstance(
        result_data["news"][1]["published_date"], str
    )  # Check it's a string, actual date will vary


def test_run_yfinance_exception(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "ERRORNEWS"
    error_message = "Test yfinance news error"

    # Test error on .news access
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    type(mock_ticker_instance).news = property(mocker.MagicMock(side_effect=Exception(error_message)))

    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"Error retrieving news for {ticker_symbol}: {error_message}"}

    # Test error on Ticker instantiation
    mock_yfinance_ticker.reset_mock()
    mock_yfinance_ticker.side_effect = Exception(error_message)
    result_str = tool_instance._run(ticker=ticker_symbol)
    result_data = json.loads(result_str)
    assert result_data == {"error": f"Error retrieving news for {ticker_symbol}: {error_message}"}


def test_run_with_zero_limit(tool_instance, mocker):
    mock_yfinance_ticker = mocker.patch("src.epic_news.tools.yahoo_finance_news_tool.yf.Ticker")
    ticker_symbol = "ZEROLIMITNEWS"
    mock_ticker_instance = mocker.MagicMock()
    mock_yfinance_ticker.return_value = mock_ticker_instance
    mock_ticker_instance.news = [
        {
            "title": "News 1",
            "publisher": "Pub A",
            "link": "link1.com",
            "providerPublishTime": int(datetime.datetime.now().timestamp()),
        }
    ]

    result_str = tool_instance._run(ticker=ticker_symbol, limit=0)
    result_data = json.loads(result_str)

    assert result_data["ticker"] == ticker_symbol
    assert len(result_data["news"]) == 0
