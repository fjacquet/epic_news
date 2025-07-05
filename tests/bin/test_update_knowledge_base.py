import datetime

import pytest
from loguru import logger
from pydantic import BaseModel

from epic_news.bin.update_knowledge_base import (
    prune_outdated_knowledge,
    update_market_data,
)


class KnowledgeEntry(BaseModel):
    """Pydantic model to validate the structure of the knowledge entry."""

    content: str

    @property
    def ticker(self) -> str:
        return self.content.split("(")[1].split(")")[0]

    @property
    def current_price(self) -> float:
        return float(self.content.split("Current Price: ")[1].split("\n")[0])


@pytest.fixture
def mock_yfinance_ticker(mocker):
    """Fixture to mock yfinance.Ticker."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        "shortName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3000000000000,
        "currentPrice": 195.00,
        "trailingPE": 30.5,
        "dividendYield": 0.005,
    }
    return mock_ticker


def test_update_market_data_success(
    mock_yfinance_ticker,
    caplog,
    mocker,
):
    """Test successful update of market data for a single ticker."""
    mock_ticker_cls = mocker.patch("epic_news.bin.update_knowledge_base.yf.Ticker")
    mock_ticker_cls.return_value = mock_yfinance_ticker
    mock_rag_tool_cls = mocker.patch("epic_news.bin.update_knowledge_base.RagTool")
    mock_save_tool_cls = mocker.patch("epic_news.bin.update_knowledge_base.SaveToRagTool")
    mock_save_tool_instance = mock_save_tool_cls.return_value

    tickers = ["AAPL"]
    update_market_data(tickers, collection_suffix="test-stocks")

    # Verify RagTool was configured correctly
    rag_config = mock_rag_tool_cls.call_args.kwargs["config"]
    assert rag_config["vectordb"]["config"]["collection_name"] == "epic_news-test-stocks"

    # Verify SaveToRagTool was called with a valid knowledge entry
    mock_save_tool_instance._run.assert_called_once()
    call_args = mock_save_tool_instance._run.call_args[0]
    entry = KnowledgeEntry(content=call_args[0])

    assert entry.ticker == "AAPL"
    assert entry.current_price == 195.00
    assert "Dividend Yield: 0.50%" in entry.content
    assert (
        f"Market Data Update for Apple Inc. (AAPL) - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        in entry.content
    )
    assert "Updated knowledge base with data for AAPL" in caplog.text


def test_update_market_data_incomplete_info(
    caplog,
    mocker,
):
    """Test update when yfinance returns incomplete info."""
    mock_ticker_cls = mocker.patch("epic_news.bin.update_knowledge_base.yf.Ticker")
    mocker.patch("epic_news.bin.update_knowledge_base.RagTool")
    mock_save_tool_cls = mocker.patch("epic_news.bin.update_knowledge_base.SaveToRagTool")
    mock_incomplete_ticker = mocker.MagicMock()
    mock_incomplete_ticker.info = {"symbol": "FAIL"}  # Missing 'shortName'
    mock_ticker_cls.return_value = mock_incomplete_ticker
    mock_save_tool_instance = mock_save_tool_cls.return_value

    update_market_data(["FAIL"])

    mock_save_tool_instance._run.assert_not_called()
    assert "Could not retrieve complete information for FAIL" in caplog.text


def test_update_market_data_exception(
    caplog,
    mocker,
):
    """Test update when yfinance raises an exception."""
    mock_ticker_cls = mocker.patch("epic_news.bin.update_knowledge_base.yf.Ticker")
    mock_ticker_cls.side_effect = Exception("Network Error")

    update_market_data(["ERROR"])

    assert "Error updating ERROR: Network Error" in caplog.text


def test_prune_outdated_knowledge(caplog):
    """Test that the prune function logs its unimplemented status."""
    prune_outdated_knowledge(max_age_days=90)

    assert "Pruning outdated knowledge (older than 90 days) is not yet implemented" in caplog.text
