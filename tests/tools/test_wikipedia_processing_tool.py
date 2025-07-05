"""Unit tests for the WikipediaProcessingTool."""

import pytest

from src.epic_news.tools.wikipedia_processing_tool import ProcessingAction, WikipediaProcessingTool


@pytest.fixture
def mock_wikipedia_page(mocker):
    """Fixture to create a mock WikipediaPage object."""
    page = mocker.MagicMock()
    page.title = "Test Title"
    page.summary = "First sentence. Second sentence. Third sentence."
    page.content = "This is the full article content with the query term."
    page.section.return_value = "This is the section content."
    return page


def test_extract_key_facts_success(mock_wikipedia_page, mocker):
    """Test successfully extracting key facts."""
    mock_page_func = mocker.patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.EXTRACT_KEY_FACTS, count=2)
    assert result == "First sentence. Second sentence."


def test_summarize_for_query_success(mock_wikipedia_page, mocker):
    """Test successfully summarizing an article for a query."""
    mock_page_func = mocker.patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.SUMMARIZE_FOR_QUERY, query="query term")
    assert "full article content with the query term" in result


def test_summarize_section_success(mock_wikipedia_page, mocker):
    """Test successfully summarizing a section."""
    mock_page_func = mocker.patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(
        title="Test Title", action=ProcessingAction.SUMMARIZE_SECTION, section_title="Test Section"
    )
    assert result == "This is the section content."
    mock_wikipedia_page.section.assert_called_once_with("Test Section")


def test_summarize_for_query_missing_query(mock_wikipedia_page, mocker):
    """Test that an error is returned when query is missing."""
    mock_page_func = mocker.patch("src.epic_news.tools.wikipedia_processing_tool.wikipedia.page")
    mock_page_func.return_value = mock_wikipedia_page
    tool = WikipediaProcessingTool()
    result = tool._run(title="Test Title", action=ProcessingAction.SUMMARIZE_FOR_QUERY)
    assert "'query' is required" in result
