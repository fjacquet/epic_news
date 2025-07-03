import pytest
from pydantic import ValidationError

# Import all models with their correct names
from epic_news.models.accuweather_models import AccuWeatherToolInput
from epic_news.models.airtable_models import (
    AirtableReaderToolInput,
    AirtableToolInput,
)
from epic_news.models.alpha_vantage_models import CompanyOverviewInput
from epic_news.models.coinmarketcap_models import (
    CoinInfoInput,
    CryptocurrencyHistoricalInput,
    CryptocurrencyListInput,
    CryptocurrencyNewsInput,
)
from epic_news.models.content_state import ContentState
from epic_news.models.custom_tool_models import MyCustomToolInput

# New tests for data_metrics, email_search, and finance models
from epic_news.models.data_metrics import (
    KPI,
    DataPoint,
    DataSeries,
    DataTable,
    Metric,
    MetricType,
    MetricValue,
    StructuredDataReport,
    TrendDirection,
)
from epic_news.models.email_search_models import (
    DelegatingEmailSearchInput,
    HunterIOInput,
    SerperSearchInput,
)
from epic_news.models.extracted_info import ExtractedInfo
from epic_news.models.finance_models import (
    ExchangeRateToolInput,
    GetCompanyInfoInput,
    GetETFHoldingsInput,
    GetTickerHistoryInput,
    GetTickerInfoInput,
    GetTickerNewsInput,
    KrakenAssetListInput,
    KrakenTickerInfoInput,
)

# New tests for github, google_fact_check, and paprika_recipe models
from epic_news.models.github_models import GitHubSearchInput
from epic_news.models.google_fact_check_tool import GoogleFactCheckInput
from epic_news.models.paprika_recipe import PaprikaRecipe

# New tests for report, report_models, and rss_models
from epic_news.models.report import ReportHTMLOutput
from epic_news.models.report_models import RenderReportToolSchema, ReportImage, ReportSection
from epic_news.models.rss_models import Article, FeedWithArticles, RssFeedParserToolInput, RssFeeds

# New tests for tavily, todoist, and web_search models
from epic_news.models.tavily_models import TavilyToolInput
from epic_news.models.todoist_models import TodoistToolInput
from epic_news.models.web_search_models import ScrapeNinjaInput, SerpApiInput

# Final tests for wikipedia_models
from epic_news.models.wikipedia_models import WikipediaToolInput


def test_accuweather_tool_input_valid():
    model = AccuWeatherToolInput(location="London")
    assert model.location == "London"


def test_airtable_reader_tool_input_valid():
    model = AirtableReaderToolInput(base_id="abc", table_name="Table 1")
    assert model.base_id == "abc"
    assert model.table_name == "Table 1"


def test_airtable_tool_input_valid():
    model = AirtableToolInput(base_id="abc", table_name="Table 1", data={"key": "value"})
    assert model.data == {"key": "value"}


def test_company_overview_input_valid():
    model = CompanyOverviewInput(ticker="MSFT")
    assert model.ticker == "MSFT"


def test_coin_info_input_valid():
    model = CoinInfoInput(symbol="BTC")
    assert model.symbol == "BTC"


def test_cryptocurrency_historical_input_valid():
    model = CryptocurrencyHistoricalInput(symbol="ETH", time_period="7d")
    assert model.symbol == "ETH"


def test_cryptocurrency_list_input_valid():
    model = CryptocurrencyListInput(limit=10)
    assert model.limit == 10


def test_cryptocurrency_news_input_valid():
    model = CryptocurrencyNewsInput(symbol="SOL")
    assert model.symbol == "SOL"


def test_content_state_valid():
    # Test with default values and ensure no validation error
    model = ContentState()
    assert model.user_request == "Get the RSS Weekly Report"
    # Test with an ExtractedInfo object
    info = ExtractedInfo(target_company="TestCorp")
    model_with_info = ContentState(extracted_info=info)
    assert model_with_info.extracted_info.target_company == "TestCorp"


def test_my_custom_tool_input_valid():
    model = MyCustomToolInput(argument="test_arg")
    assert model.argument == "test_arg"


def test_my_custom_tool_input_invalid():
    with pytest.raises(ValidationError):
        MyCustomToolInput()  # Missing required 'argument' field


def test_metric_value_valid():
    mv = MetricValue(value=110, previous_value=100)
    assert mv.change_percentage == 10.0
    assert mv.trend == TrendDirection.UP


def test_metric_valid():
    mv = MetricValue(value=50)
    metric = Metric(
        name="test_metric",
        display_name="Test Metric",
        description="A test metric.",
        value=mv,
        type=MetricType.NUMERIC,
    )
    assert metric.name == "test_metric"


def test_kpi_valid():
    mv = MetricValue(value=85)
    kpi = KPI(
        name="test_kpi",
        display_name="Test KPI",
        description="A test KPI.",
        value=mv,
        type=MetricType.NUMERIC,
        target=100,
    )
    assert kpi.name == "test_kpi"
    assert kpi.is_key_metric is True
    assert kpi.progress_percentage == 85.0
    assert kpi.status == "on track"


def test_data_point_valid():
    dp = DataPoint(label="Q1", value=100)
    assert dp.value == 100
    assert dp.label == "Q1"


def test_data_series_valid():
    ds = DataSeries(name="Sales", points=[DataPoint(label="Q1", value=100)])
    assert ds.name == "Sales"
    assert len(ds.points) == 1


def test_data_table_valid():
    table = DataTable(name="Financials", columns=["Quarter", "Sales"], rows=[["Q1", 100]])
    assert len(table.rows) == 1


def test_structured_data_report_valid():
    mv = MetricValue(value=1500)
    metric = Metric(
        name="revenue",
        display_name="Revenue",
        description="Total revenue.",
        value=mv,
        type=MetricType.CURRENCY,
    )
    report = StructuredDataReport(
        title="Q1 Report", description="A summary of Q1 performance.", metrics=[metric]
    )
    assert report.title == "Q1 Report"


def test_hunter_io_input_valid():
    model = HunterIOInput(domain="example.com")
    assert model.domain == "example.com"


def test_serper_search_input_valid():
    model = SerperSearchInput(query="Example Inc")
    assert model.query == "Example Inc"


def test_delegating_email_search_input_valid():
    model = DelegatingEmailSearchInput(provider="hunter", query="example.com")
    assert model.provider == "hunter"


def test_exchange_rate_tool_input_valid():
    model = ExchangeRateToolInput(target_currencies=["USD"])
    assert model.base_currency == "USD"


def test_get_company_info_input_valid():
    model = GetCompanyInfoInput(ticker="AAPL")
    assert model.ticker == "AAPL"


def test_get_etf_holdings_input_valid():
    model = GetETFHoldingsInput(ticker="SPY")
    assert model.ticker == "SPY"


def test_get_ticker_history_input_valid():
    model = GetTickerHistoryInput(ticker="MSFT")
    assert model.ticker == "MSFT"


def test_get_ticker_news_input_valid():
    model = GetTickerNewsInput(ticker="GOOG")
    assert model.ticker == "GOOG"


def test_get_ticker_info_input_valid():
    model = GetTickerInfoInput(ticker="AMZN")
    assert model.ticker == "AMZN"


def test_kraken_ticker_info_input_valid():
    model = KrakenTickerInfoInput(pair="XBTUSD")
    assert model.pair == "XBTUSD"


def test_kraken_asset_list_input_valid():
    model = KrakenAssetListInput()
    assert model.asset_class == "currency"


def test_github_search_input_valid():
    model = GitHubSearchInput(query="crewai", search_type="repositories")
    assert model.query == "crewai"
    assert model.search_type == "repositories"


def test_github_search_input_invalid():
    with pytest.raises(ValidationError):
        GitHubSearchInput(query="crewai", max_results=11)  # max_results > 10


def test_google_fact_check_input_valid():
    model = GoogleFactCheckInput(query="elections")
    assert model.query == "elections"


def test_paprika_recipe_valid():
    recipe = PaprikaRecipe(name="Test Recipe", ingredients="1 cup flour", directions="Mix it.")
    assert recipe.name == "Test Recipe"


def test_paprika_recipe_invalid():
    with pytest.raises(ValidationError):
        PaprikaRecipe(name="Incomplete Recipe")  # Missing ingredients and directions


def test_report_html_output_valid():
    model = ReportHTMLOutput(html="<html></html>")
    assert model.html == "<html></html>"


def test_report_section_valid():
    model = ReportSection(heading="Test", content="<p>Test</p>")
    assert model.heading == "Test"


def test_report_image_valid():
    model = ReportImage(src="test.png", alt="A test image")
    assert model.src == "test.png"


def test_render_report_tool_schema_valid():
    section = ReportSection(heading="H1", content="C1")
    model = RenderReportToolSchema(title="Test Report", sections=[section])
    assert model.title == "Test Report"
    assert len(model.sections) == 1


def test_rss_feed_parser_tool_input_valid():
    model = RssFeedParserToolInput(feed_url="https://example.com/rss")
    assert model.feed_url == "https://example.com/rss"


def test_article_valid():
    model = Article(title="Test", link="http://a.com", published="today")
    assert model.title == "Test"


def test_feed_with_articles_valid():
    article = Article(title="T", link="l", published="p")
    model = FeedWithArticles(feed_url="f", articles=[article])
    assert len(model.articles) == 1


def test_rss_feeds_valid():
    article = Article(title="T", link="l", published="p")
    feed = FeedWithArticles(feed_url="f", articles=[article])
    model = RssFeeds(rss_feeds=[feed])
    assert len(model.rss_feeds) == 1


def test_tavily_tool_input_valid():
    model = TavilyToolInput(query="what is crewai?")
    assert model.query == "what is crewai?"


def test_todoist_tool_input_valid():
    model = TodoistToolInput(action="get_tasks")
    assert model.action == "get_tasks"


def test_todoist_tool_input_create_invalid():
    with pytest.raises(ValidationError):
        TodoistToolInput(action="create_task")  # Missing task_content


def test_todoist_tool_input_complete_invalid():
    with pytest.raises(ValidationError):
        TodoistToolInput(action="complete_task")  # Missing task_id


def test_serp_api_input_valid():
    model = SerpApiInput(query="latest news")
    assert model.query == "latest news"


def test_scrape_ninja_input_valid():
    model = ScrapeNinjaInput(url="https://www.google.com")
    assert model.url == "https://www.google.com"


def test_wikipedia_tool_input_search_valid():
    model = WikipediaToolInput(action="search_wikipedia", query="CrewAI")
    assert model.action == "search_wikipedia"
    assert model.query == "CrewAI"


def test_wikipedia_tool_input_get_article_valid():
    model = WikipediaToolInput(action="get_article", title="Artificial Intelligence")
    assert model.action == "get_article"
    assert model.title == "Artificial Intelligence"


def test_wikipedia_tool_input_get_article_invalid():
    with pytest.raises(ValidationError):
        WikipediaToolInput(action="get_article")  # Missing title


def test_wikipedia_tool_input_search_invalid():
    with pytest.raises(ValidationError):
        WikipediaToolInput(action="search_wikipedia")  # Missing query


def test_wikipedia_tool_input_summarize_section_invalid():
    with pytest.raises(ValidationError):
        WikipediaToolInput(action="summarize_article_section", title="Test")  # Missing section_title
