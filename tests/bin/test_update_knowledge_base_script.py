from unittest.mock import MagicMock, call, patch

from epic_news.bin.update_knowledge_base import main, prune_outdated_knowledge, update_market_data
from epic_news.rag_config import DEFAULT_RAG_CONFIG

# Sample yfinance info data for mocking
SAMPLE_YF_INFO_AAPL = {
    "shortName": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "marketCap": 3000000000000,
    "currentPrice": 170.00,
    "trailingPE": 30.0,
    "dividendYield": 0.005
}

SAMPLE_YF_INFO_MSFT = {
    "shortName": "Microsoft Corp.",
    "sector": "Technology",
    "industry": "Software - Infrastructure",
    "marketCap": 2500000000000,
    "regularMarketPrice": 300.00, # Test fallback for currentPrice
    "trailingPE": 35.0,
    "dividendYield": 0.008
}

SAMPLE_YF_INFO_NODATA = {}

@patch('epic_news.bin.update_knowledge_base.SaveToRagTool')
@patch('epic_news.bin.update_knowledge_base.RagTool')
@patch('epic_news.bin.update_knowledge_base.yf.Ticker')
def test_update_market_data_success(mock_yf_ticker, mock_rag_tool_class, mock_save_tool_class):
    """Test successful market data update for multiple tickers."""
    mock_save_instance = MagicMock()
    mock_save_tool_class.return_value = mock_save_instance

    mock_rag_instance = MagicMock()
    mock_rag_tool_class.return_value = mock_rag_instance

    # Configure side_effect for yf.Ticker to return different mocks based on ticker
    def yf_ticker_side_effect(ticker_symbol):
        mock_ticker = MagicMock()
        if ticker_symbol == "AAPL":
            mock_ticker.info = SAMPLE_YF_INFO_AAPL
        elif ticker_symbol == "MSFT":
            mock_ticker.info = SAMPLE_YF_INFO_MSFT
        else:
            mock_ticker.info = {}
        return mock_ticker
    mock_yf_ticker.side_effect = yf_ticker_side_effect

    tickers_to_update = ["AAPL", "MSFT"]
    update_market_data(tickers_to_update, collection_suffix="test_stocks")

    # Assertions for yf.Ticker calls
    assert mock_yf_ticker.call_count == len(tickers_to_update)
    mock_yf_ticker.assert_any_call("AAPL")
    mock_yf_ticker.assert_any_call("MSFT")

    # Assertions for RagTool instantiation
    mock_rag_tool_class.assert_called_once()
    rag_config_arg = mock_rag_tool_class.call_args[1]['config']
    assert rag_config_arg['vectordb']['config']['collection_name'] == "epic_news-test_stocks"

    # Assertions for SaveToRagTool instantiation
    mock_save_tool_class.assert_called_once_with(rag_tool=mock_rag_instance)

    # Assertions for save_tool._run calls
    assert mock_save_instance._run.call_count == len(tickers_to_update)

    # Check content of one of the calls (e.g., for AAPL)
    aapl_call_args = None
    for call_arg in mock_save_instance._run.call_args_list:
        if "Apple Inc. (AAPL)" in call_arg[0][0]:
            aapl_call_args = call_arg[0][0]
            break
    assert aapl_call_args is not None, "Save call for AAPL not found"
    assert "Current Price: 170.0" in aapl_call_args
    assert "Market Cap: 3000000000000" in aapl_call_args
    assert "Sector: Technology" in aapl_call_args
    assert "Dividend Yield: 0.50%" in aapl_call_args # 0.005 * 100

    # Check content for MSFT (testing regularMarketPrice fallback)
    msft_call_args = None
    for call_arg in mock_save_instance._run.call_args_list:
        if "Microsoft Corp. (MSFT)" in call_arg[0][0]:
            msft_call_args = call_arg[0][0]
            break
    assert msft_call_args is not None, "Save call for MSFT not found"
    assert "Current Price: 300.0" in msft_call_args
    assert "Dividend Yield: 0.80%" in msft_call_args

@patch('epic_news.bin.update_knowledge_base.SaveToRagTool')
@patch('epic_news.bin.update_knowledge_base.RagTool')
@patch('epic_news.bin.update_knowledge_base.yf.Ticker')
def test_update_market_data_no_suffix(mock_yf_ticker, mock_rag_tool_class, mock_save_tool_class):
    """Test market data update without a collection suffix."""
    mock_save_instance = MagicMock()
    mock_save_tool_class.return_value = mock_save_instance
    mock_rag_instance = MagicMock()
    mock_rag_tool_class.return_value = mock_rag_instance

    mock_ticker_aapl = MagicMock()
    mock_ticker_aapl.info = SAMPLE_YF_INFO_AAPL
    mock_yf_ticker.return_value = mock_ticker_aapl # Only one ticker for simplicity

    update_market_data(["AAPL"])

    mock_rag_tool_class.assert_called_once()
    rag_config_arg = mock_rag_tool_class.call_args[1]['config']
    # Should use the default collection name from DEFAULT_RAG_CONFIG
    assert rag_config_arg['vectordb']['config']['collection_name'] == DEFAULT_RAG_CONFIG['vectordb']['config']['collection_name']
    mock_save_instance._run.assert_called_once()

@patch('epic_news.bin.update_knowledge_base.SaveToRagTool')
@patch('epic_news.bin.update_knowledge_base.RagTool')
@patch('epic_news.bin.update_knowledge_base.yf.Ticker')
@patch('epic_news.bin.update_knowledge_base.logger') # Mock logger
def test_update_market_data_incomplete_info(mock_logger, mock_yf_ticker, mock_rag_tool_class, mock_save_tool_class):
    """Test handling of incomplete info from yfinance."""
    mock_save_instance = MagicMock()
    mock_save_tool_class.return_value = mock_save_instance
    mock_rag_instance = MagicMock()
    mock_rag_tool_class.return_value = mock_rag_instance

    mock_ticker_nodata = MagicMock()
    mock_ticker_nodata.info = SAMPLE_YF_INFO_NODATA # Empty info dict
    mock_yf_ticker.return_value = mock_ticker_nodata

    update_market_data(["NODATA"])

    mock_save_instance._run.assert_not_called() # Should not save if info is incomplete
    mock_logger.warning.assert_called_once_with("Could not retrieve complete information for NODATA")

@patch('epic_news.bin.update_knowledge_base.SaveToRagTool')
@patch('epic_news.bin.update_knowledge_base.RagTool')
@patch('epic_news.bin.update_knowledge_base.yf.Ticker')
@patch('epic_news.bin.update_knowledge_base.logger') # Mock logger
def test_update_market_data_yfinance_exception(mock_logger, mock_yf_ticker, mock_rag_tool_class, mock_save_tool_class):
    """Test handling of exceptions from yfinance."""
    mock_save_instance = MagicMock()
    mock_save_tool_class.return_value = mock_save_instance
    mock_rag_instance = MagicMock()
    mock_rag_tool_class.return_value = mock_rag_instance

    error_message = "Test yfinance error"
    mock_yf_ticker.side_effect = Exception(error_message)

    update_market_data(["ERROR"])

    mock_save_instance._run.assert_not_called()
    mock_logger.error.assert_called_once_with(f"Error updating ERROR: {error_message}")

@patch('epic_news.bin.update_knowledge_base.logger')
def test_prune_outdated_knowledge(mock_logger):
    """Test the prune_outdated_knowledge function (currently a placeholder)."""
    prune_outdated_knowledge(max_age_days=30, collection_suffix="test_prune")
    mock_logger.info.assert_any_call("Pruning outdated knowledge (older than 30 days) is not yet implemented")

@patch('epic_news.bin.update_knowledge_base.update_market_data')
@patch('epic_news.bin.update_knowledge_base.prune_outdated_knowledge')
@patch('epic_news.bin.update_knowledge_base.logger')
def test_main_script_flow(mock_logger, mock_prune, mock_update):
    """Test the main function's overall flow."""
    main()

    # Check that update_market_data is called for stocks, etfs, crypto
    expected_update_calls = [
        call(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'], collection_suffix='stock'),
        call(['SPY', 'QQQ', 'VTI', 'ARKK', 'XLF'], collection_suffix='etf'),
        call(['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'DOT-USD'], collection_suffix='crypto')
    ]
    mock_update.assert_has_calls(expected_update_calls, any_order=False)
    assert mock_update.call_count == 3

    # Check that prune_outdated_knowledge is called
    mock_prune.assert_called_once_with(max_age_days=30)

    # Check logging messages
    mock_logger.info.assert_any_call("Starting knowledge base update")
    mock_logger.info.assert_any_call("Knowledge base update completed")
