"""Unit tests for the WikipediaArticleTool."""

import json

import pytest
import wikipedia

from epic_news.tools.wikipedia_article_tool import ArticleAction, WikipediaArticleTool


@pytest.fixture
def mock_wikipedia_page(mocker):
    """Fixture to create a mock WikipediaPage object."""
    page = mocker.MagicMock()
    page.summary = "This is a summary."
    page.content = "This is the full article content."
    page.links = ["Link 1", "Link 2"]
    page.sections = ["Section 1", "Section 2"]
    return page


def test_get_summary_success(mock_wikipedia_page, mocker):
    """Test successfully getting an article summary."""
    mock_page_func = mocker.patch("epic_news.tools.wikipedia_article_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaArticleTool()
    result = tool._run(title="Test Title", action=ArticleAction.GET_SUMMARY)
    assert result == mock_wikipedia_page.summary
    mock_page_func.assert_called_once_with("Test Title", auto_suggest=True, redirect=True)


def test_get_full_article_success(mock_wikipedia_page, mocker):
    """Test successfully getting full article content."""
    mock_page_func = mocker.patch("epic_news.tools.wikipedia_article_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaArticleTool()
    result = tool._run(title="Test Title", action=ArticleAction.GET_ARTICLE)
    assert result == mock_wikipedia_page.content


def test_get_links_success(mock_wikipedia_page, mocker):
    """Test successfully getting article links."""
    mock_page_func = mocker.patch("epic_news.tools.wikipedia_article_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaArticleTool()
    result = tool._run(title="Test Title", action=ArticleAction.GET_LINKS)
    assert result == json.dumps(mock_wikipedia_page.links)


def test_page_not_found_error(mocker):
    """Test handling of PageError when a page is not found."""
    mock_page_func = mocker.patch("epic_news.tools.wikipedia_article_tool.wikipedia.page")
    mock_page_func.side_effect = wikipedia.exceptions.PageError(pageid="NonExistentPage")
    tool = WikipediaArticleTool()
    result = tool._run(title="NonExistentPage", action=ArticleAction.GET_SUMMARY)
    assert "Could not find a Wikipedia page for 'NonExistentPage'" in result


def test_disambiguation_error(mocker):
    """Test handling of DisambiguationError."""
    mock_page_func = mocker.patch("epic_news.tools.wikipedia_article_tool.wikipedia.page")
    options = ["Option 1", "Option 2"]
    mock_page_func.side_effect = wikipedia.exceptions.DisambiguationError("Ambiguous", options)
    tool = WikipediaArticleTool()
    result = tool._run(title="Ambiguous", action=ArticleAction.GET_SUMMARY)
    assert "'Ambiguous' is ambiguous. Did you mean one of these?" in result
    assert "Option 1" in result
