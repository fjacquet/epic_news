from unittest.mock import call

from epic_news.rag_config import DEFAULT_RAG_CONFIG
from scripts.update_knowledge_base import main, prune_outdated_knowledge, update_market_data
from tests.utils.context_managers import mock_knowledge_base_dependencies

# Sample yfinance info data for mocking
SAMPLE_YF_INFO_AAPL = {
    "shortName": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "marketCap": 3000000000000,
    "currentPrice": 170.00,
    "trailingPE": 30.0,
    "dividendYield": 0.005,
}

SAMPLE_YF_INFO_MSFT = {
    "shortName": "Microsoft Corp.",
    "sector": "Technology",
    "industry": "Software - Infrastructure",
    "marketCap": 2500000000000,
    "regularMarketPrice": 300.00,  # Test fallback for currentPrice
    "trailingPE": 35.0,
    "dividendYield": 0.008,
}

SAMPLE_YF_INFO_NODATA = {}


def test_update_market_data_success(mocker):
    """Test successful market data update for multiple tickers."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        # Configure side_effect for yf.Ticker to return different mocks based on ticker
        def yf_ticker_side_effect(ticker_symbol):
            mock_ticker = mocker.MagicMock()
            if ticker_symbol == "AAPL":
                mock_ticker.info = SAMPLE_YF_INFO_AAPL
            elif ticker_symbol == "MSFT":
                mock_ticker.info = SAMPLE_YF_INFO_MSFT
            else:
                mock_ticker.info = {}
            return mock_ticker

        mocks["yf_ticker"].side_effect = yf_ticker_side_effect

        tickers_to_update = ["AAPL", "MSFT"]
        update_market_data(tickers_to_update, collection_suffix="test_stocks")

        # Assertions for yf.Ticker calls
        assert mocks["yf_ticker"].call_count == len(tickers_to_update)
        mocks["yf_ticker"].assert_any_call("AAPL")
        mocks["yf_ticker"].assert_any_call("MSFT")

        # Assertions for RagTool instantiation
        mocks["rag_tool"].assert_called_once()
        rag_config_arg = mocks["rag_tool"].call_args[1]["config"]
        assert rag_config_arg["vectordb"]["config"]["collection_name"] == "epic_news-test_stocks"

        # Assertions for SaveToRagTool instantiation
        mocks["save_tool"].assert_called_once_with(rag_tool=mocks["rag_tool"].return_value)

        # Assertions for save_tool._run calls
        assert mocks["save_tool"].return_value._run.call_count == len(tickers_to_update)

        # Check content of one of the calls (e.g., for AAPL)
        aapl_call_args = None
        for call_arg in mocks["save_tool"].return_value._run.call_args_list:
            if "Apple Inc. (AAPL)" in call_arg[0][0]:
                aapl_call_args = call_arg[0][0]
                break
        assert aapl_call_args is not None, "Save call for AAPL not found"
        assert "Current Price: 170.0" in aapl_call_args
        assert "Market Cap: 3000000000000" in aapl_call_args
        assert "Sector: Technology" in aapl_call_args
        assert "Dividend Yield: 0.50%" in aapl_call_args  # 0.005 * 100

        # Check content for MSFT (testing regularMarketPrice fallback)
        msft_call_args = None
        for call_arg in mocks["save_tool"].return_value._run.call_args_list:
            if "Microsoft Corp. (MSFT)" in call_arg[0][0]:
                msft_call_args = call_arg[0][0]
                break
        assert msft_call_args is not None, "Save call for MSFT not found"
        assert "Current Price: 300.0" in msft_call_args
        assert "Dividend Yield: 0.80%" in msft_call_args


def test_update_market_data_no_suffix(mocker):
    """Test market data update without a collection suffix."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        mock_ticker_aapl = mocker.MagicMock()
        mock_ticker_aapl.info = SAMPLE_YF_INFO_AAPL
        mocks["yf_ticker"].return_value = mock_ticker_aapl  # Only one ticker for simplicity

        update_market_data(["AAPL"])

        mocks["rag_tool"].assert_called_once()
        rag_config_arg = mocks["rag_tool"].call_args[1]["config"]
        # Should use the default collection name from DEFAULT_RAG_CONFIG
        assert (
            rag_config_arg["vectordb"]["config"]["collection_name"]
            == DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"]
        )
        mocks["save_tool"].return_value._run.assert_called_once()


def test_update_market_data_incomplete_info(mocker):
    """Test handling of incomplete info from yfinance."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        mock_ticker_nodata = mocker.MagicMock()
        mock_ticker_nodata.info = SAMPLE_YF_INFO_NODATA  # Empty info dict
        mocks["yf_ticker"].return_value = mock_ticker_nodata

        update_market_data(["NODATA"])

        mocks["save_tool"].return_value._run.assert_not_called()  # Should not save if info is incomplete
        mocks["logger"].warning.assert_called_once_with("Could not retrieve complete information for NODATA")


def test_update_market_data_yfinance_exception(mocker):
    """Test handling of exceptions from yfinance."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        error_message = "Test yfinance error"
        mocks["yf_ticker"].side_effect = Exception(error_message)

        update_market_data(["ERROR"])

        mocks["save_tool"].return_value._run.assert_not_called()
        mocks["logger"].error.assert_called_once_with(f"Error updating ERROR: {error_message}")


def test_prune_outdated_knowledge(mocker):
    """Test the prune_outdated_knowledge function (currently a placeholder)."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        prune_outdated_knowledge(max_age_days=30, collection_suffix="test_prune")
        mocks["logger"].info.assert_any_call(
            "Pruning outdated knowledge (older than 30 days) is not yet implemented"
        )


def test_main_script_flow(mocker):
    """Test the main function's overall flow."""
    with mock_knowledge_base_dependencies(mocker) as mocks:
        main()

        # Check that update_market_data is called for stocks, etfs, crypto
        expected_update_calls = [
            call(["AAPL", "MSFT", "GOOGL", "AMZN", "META"], collection_suffix="stock"),
            call(["SPY", "QQQ", "VTI", "ARKK", "XLF"], collection_suffix="etf"),
            call(["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOT-USD"], collection_suffix="crypto"),
        ]
        mocks["update"].assert_has_calls(expected_update_calls, any_order=False)
        assert mocks["update"].call_count == 3

        # Check that prune_outdated_knowledge is called
        mocks["prune"].assert_called_once_with(max_age_days=30)

        # Check logging messages
        mocks["logger"].info.assert_any_call("Starting knowledge base update")
        mocks["logger"].info.assert_any_call("Knowledge base update completed")
