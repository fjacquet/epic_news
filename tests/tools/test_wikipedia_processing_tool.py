"""Unit tests for the WikipediaProcessingTool."""

from unittest.mock import MagicMock, patch

import pytest

from src.epic_news.tools.wikipedia_processing_tool import ProcessingAction, WikipediaProcessingTool


@pytest.fixture
def mock_wikipedia_page():
    """Fixture to create a mock WikipediaPage object."""
    page = MagicMock()
    page.title = "Test Title"
    page.summary = "First sentence. Second sentence. Third sentence."
    page.content = "This is the full article content with the query term."
    page.section.return_value = "This is the section content."
    return page


@patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
def test_extract_key_facts_success(mock_page_func, mock_wikipedia_page):
    """Test successfully extracting key facts."""
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.EXTRACT_KEY_FACTS, count=2)
    assert result == "First sentence. Second sentence."


@patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
def test_summarize_for_query_success(mock_page_func, mock_wikipedia_page):
    """Test successfully summarizing an article for a query."""
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.SUMMARIZE_FOR_QUERY, query="query term")
    assert "full article content with the query term" in result


@patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
def test_summarize_section_success(mock_page_func, mock_wikipedia_page):
    """Test successfully summarizing a section."""
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(
        title="Test Title", action=ProcessingAction.SUMMARIZE_SECTION, section_title="Test Section"
    )
    assert result == "This is the section content."
    mock_wikipedia_page.section.assert_called_once_with("Test Section")


@patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
def test_summarize_for_query_missing_query(mock_page_func, mock_wikipedia_page):
    """Test that an error is returned when query is missing."""
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.SUMMARIZE_FOR_QUERY)
    assert "'query' is required" in result
