from crewai.tools import BaseTool

from epic_news.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from epic_news.tools.finance_tools import (
    get_crypto_research_tools,
    get_etf_research_tools,
    get_stock_research_tools,
    get_yahoo_finance_tools,
)
from epic_news.tools.kraken_api_tool import KrakenTickerInfoTool
from epic_news.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
from epic_news.tools.yahoo_finance_etf_holdings_tool import YahooFinanceETFHoldingsTool
from epic_news.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from epic_news.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
from epic_news.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool


def test_get_yahoo_finance_tools():
    tools = get_yahoo_finance_tools()
    assert isinstance(tools, list)
    assert len(tools) == 5
    for tool in tools:
        assert isinstance(tool, BaseTool)
    assert any(isinstance(t, YahooFinanceTickerInfoTool) for t in tools)
    assert any(isinstance(t, YahooFinanceHistoryTool) for t in tools)
    assert any(isinstance(t, YahooFinanceCompanyInfoTool) for t in tools)
    assert any(isinstance(t, YahooFinanceETFHoldingsTool) for t in tools)
    assert any(isinstance(t, YahooFinanceNewsTool) for t in tools)

def test_get_stock_research_tools():
    tools = get_stock_research_tools()
    assert isinstance(tools, list)
    assert len(tools) == 5
    for tool in tools:
        assert isinstance(tool, BaseTool)
    assert any(isinstance(t, YahooFinanceTickerInfoTool) for t in tools)
    assert any(isinstance(t, YahooFinanceHistoryTool) for t in tools)
    assert any(isinstance(t, YahooFinanceCompanyInfoTool) for t in tools)
    assert any(isinstance(t, YahooFinanceNewsTool) for t in tools)
    assert any(isinstance(t, AlphaVantageCompanyOverviewTool) for t in tools)

def test_get_crypto_research_tools():
    tools = get_crypto_research_tools()
    assert isinstance(tools, list)
    assert len(tools) == 4
    for tool in tools:
        assert isinstance(tool, BaseTool)
    assert any(isinstance(t, YahooFinanceHistoryTool) for t in tools)
    assert any(isinstance(t, YahooFinanceNewsTool) for t in tools)
    assert any(isinstance(t, YahooFinanceTickerInfoTool) for t in tools)
    assert any(isinstance(t, KrakenTickerInfoTool) for t in tools)

def test_get_etf_research_tools():
    tools = get_etf_research_tools()
    assert isinstance(tools, list)
    assert len(tools) == 4
    for tool in tools:
        assert isinstance(tool, BaseTool)
    assert any(isinstance(t, YahooFinanceTickerInfoTool) for t in tools)
    assert any(isinstance(t, YahooFinanceHistoryTool) for t in tools)
    assert any(isinstance(t, YahooFinanceETFHoldingsTool) for t in tools)
    assert any(isinstance(t, YahooFinanceNewsTool) for t in tools)
