import pytest
from pydantic import ValidationError

# Import all models with their correct names
from epic_news.models.content_state import ContentState
from epic_news.models.crews.cooking_recipe import PaprikaRecipe
from epic_news.models.extracted_info import ExtractedInfo
from epic_news.models.rss_models import Article, FeedWithArticles, RssFeeds


def test_content_state_valid():
    # Test with default values and ensure no validation error
    model = ContentState()
    assert model.user_request == "Get the RSS Weekly Report"
    # Test with an ExtractedInfo object
    info = ExtractedInfo(target_company="TestCorp")
    model_with_info = ContentState(extracted_info=info)
    assert model_with_info.extracted_info.target_company == "TestCorp"


def test_paprika_recipe_valid():
    recipe = PaprikaRecipe(name="Test Recipe", ingredients="1 cup flour", directions="Mix it.")
    assert recipe.name == "Test Recipe"


def test_paprika_recipe_invalid():
    with pytest.raises(ValidationError):
        PaprikaRecipe(name="Incomplete Recipe")  # Missing ingredients and directions


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
