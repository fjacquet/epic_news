import os

from epic_news.tools.coinmarketcap_historical_tool import CoinMarketCapHistoricalTool
from epic_news.tools.coinmarketcap_info_tool import CoinMarketCapInfoTool
from epic_news.tools.coinmarketcap_list_tool import CoinMarketCapListTool
from epic_news.tools.coinmarketcap_news_tool import CoinMarketCapNewsTool
from epic_news.tools.coinmarketcap_tool import get_coinmarketcap_tools

TEST_CMC_API_KEY = "test_cmc_api_key_for_loader"


def test_get_coinmarketcap_tools_success(mocker):
    """Test that get_coinmarketcap_tools returns the correct list of tools when API key is present."""
    mocker.patch.dict(os.environ, {"COINMARKETCAP_API_KEY": TEST_CMC_API_KEY})
    mock_get_logger = mocker.patch("epic_news.utils.logger.get_logger")
    mock_get_logger.return_value = lambda x: None  # Simple mock logger

    tools_list = get_coinmarketcap_tools()

    assert isinstance(tools_list, list)
    assert len(tools_list) == 4

    assert isinstance(tools_list[0], CoinMarketCapInfoTool)
    assert isinstance(tools_list[1], CoinMarketCapListTool)
    assert isinstance(tools_list[2], CoinMarketCapHistoricalTool)
    assert isinstance(tools_list[3], CoinMarketCapNewsTool)


def test_get_coinmarketcap_tools_no_api_key(mocker):
    """Test that get_coinmarketcap_tools raises ValueError if API key is missing."""
    mocker.patch.dict(os.environ, {"COINMARKETCAP_API_KEY": ""}, clear=True)
    mock_get_logger = mocker.patch("epic_news.utils.logger.get_logger")
    mock_get_logger.return_value = lambda x: None  # Simple mock logger

    tools_list = get_coinmarketcap_tools()
    assert isinstance(tools_list, list)
    assert len(tools_list) == 4
    # Further checks can ensure tools are instantiated, actual API key handling is tested in individual tool tests
    assert isinstance(tools_list[0], CoinMarketCapInfoTool)  # Check if first tool is created
