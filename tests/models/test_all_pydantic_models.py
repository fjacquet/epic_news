import pytest
from pydantic import ValidationError

# Import all models with their correct names
from epic_news.models.content_state import ContentState
from epic_news.models.crews.cooking_recipe import PaprikaRecipe

# Tests for data_metrics models
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
from epic_news.models.extracted_info import ExtractedInfo

# Tests for report, report_models, and rss_models
from epic_news.models.report import ReportHTMLOutput
from epic_news.models.report_models import RenderReportToolSchema, ReportImage, ReportSection
from epic_news.models.rss_models import Article, FeedWithArticles, RssFeedParserToolInput, RssFeeds


def test_content_state_valid():
    # Test with default values and ensure no validation error
    model = ContentState()
    assert model.user_request == "Get the RSS Weekly Report"
    # Test with an ExtractedInfo object
    info = ExtractedInfo(target_company="TestCorp")
    model_with_info = ContentState(extracted_info=info)
    assert model_with_info.extracted_info.target_company == "TestCorp"


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
