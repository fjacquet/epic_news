
from unittest.mock import patch

from faker import Faker

from epic_news.models.rss_weekly_models import ArticleSummary, FeedDigest, RssWeeklyReport
from epic_news.utils.content_extractors import ContentExtractorFactory, RssWeeklyExtractor

fake = Faker()

def test_get_extractor():
    # Test that the factory returns the correct extractor for a given crew type
    extractor = ContentExtractorFactory.get_extractor("RSS_WEEKLY")
    assert isinstance(extractor, RssWeeklyExtractor)

@patch('epic_news.utils.content_extractors.RssWeeklyReport.model_validate')
def test_extract_content(mock_model_validate):
    # Test that the factory correctly extracts content using the appropriate extractor
    mock_report = RssWeeklyReport(
        title="Test Report",
        summary="Test Summary",
        feeds=[],
        total_feeds=0,
        total_articles=0
    )
    mock_model_validate.return_value = mock_report
    state_data = {
        "rss_weekly_report": {
            "raw": '{"title": "Test Report", "summary": "Test Summary", "feeds": []}'
        }
    }
    content = ContentExtractorFactory.extract_content(state_data, "RSS_WEEKLY")
    assert content["title"] == "Test Report"

@patch('epic_news.utils.content_extractors.RssWeeklyReport.model_validate')
def test_rss_weekly_extractor(mock_model_validate):
    # Test the RssWeeklyExtractor
    mock_report = RssWeeklyReport(
        title=fake.sentence(),
        summary=fake.paragraph(),
        feeds=[
            FeedDigest(
                feed_url=fake.url(),
                feed_name=fake.company(),
                articles=[
                    ArticleSummary(
                        title=fake.sentence(),
                        link=fake.url(),
                        published=fake.date(),
                        summary=fake.paragraph(),
                        source_feed=fake.url()
                    )
                ],
                total_articles=1
            )
        ],
        total_feeds=1,
        total_articles=1
    )
    mock_model_validate.return_value = mock_report

    extractor = RssWeeklyExtractor()
    state_data = {
        "rss_weekly_report": {
            "raw": '{"title": "Test Report", "summary": "Test Summary", "feeds": []}'
        }
    }
    content = extractor.extract(state_data)
    assert content["title"] == mock_report.title
