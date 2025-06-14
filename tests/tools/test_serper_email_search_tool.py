import pytest
import json
import os
from unittest.mock import patch, MagicMock

from epic_news.tools.serper_email_search_tool import SerperEmailSearchTool, SerperSearchInput # Will be updated next
from epic_news.tools.email_base import EmailSearchTool

TEST_SERPER_API_KEY = "test_serper_key_for_email_search"
SERPER_API_URL = "https://google.serper.dev/search"

# --- Fixtures ---
@pytest.fixture
def mock_env_serper_key():
    with patch.dict(os.environ, {"SERPER_API_KEY": TEST_SERPER_API_KEY}, clear=True):
        yield

@pytest.fixture
def mock_env_no_serper_key():
    with patch.dict(os.environ, {"SERPER_API_KEY": ""}, clear=True):
        yield

# --- Instantiation Tests ---
def test_instantiation_success(mock_env_serper_key):
    tool = SerperEmailSearchTool()
    assert tool.name == "serper_email_search"
    assert "Search the web for publicly available email addresses" in tool.description
    assert tool.args_schema == SerperSearchInput
    assert isinstance(tool.searcher, EmailSearchTool)
    assert tool.searcher.api_key == TEST_SERPER_API_KEY

def test_instantiation_no_api_key(mock_env_no_serper_key):
    with pytest.raises(ValueError, match="SERPER_API_KEY environment variable not set"):
        SerperEmailSearchTool()

def test_instantiation_with_searcher_instance():
    mock_searcher = MagicMock(spec=EmailSearchTool)
    mock_searcher.api_key = "custom_key"
    tool = SerperEmailSearchTool(searcher=mock_searcher)
    assert tool.searcher == mock_searcher
    assert tool.searcher.api_key == "custom_key"

# --- _run Method Tests ---
@patch.object(EmailSearchTool, '_extract_emails')
@patch.object(EmailSearchTool, '_make_request')
def test_run_success_emails_found(mock_make_request, mock_extract_emails, mock_env_serper_key):
    tool = SerperEmailSearchTool()
    query = "Comp Inc"
    expected_search_q = '"comp inc" "@compinc" email'

    mock_api_response_data = {
        "organic": [
            {"snippet": "info1@comp.com some text", "link": "comp.com/page1"},
            {"snippet": "other text sales1@comp.com", "link": "comp.com/page2"}
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_data
    mock_make_request.return_value = mock_response

    # Simulate _extract_emails behavior
    mock_extract_emails.side_effect = [
        {"info1@comp.com"}, # From first organic result
        {"sales1@comp.com"}  # From second organic result
    ]

    result_str = tool._run(query=query)
    result_data = json.loads(result_str)

    mock_make_request.assert_called_once_with(
        "POST",
        SERPER_API_URL,
        headers={"X-API-KEY": TEST_SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": expected_search_q}
    )
    assert mock_extract_emails.call_count == 2
    assert result_data == [{"emails": sorted(["info1@comp.com", "sales1@comp.com"])}]

@patch.object(EmailSearchTool, '_extract_emails')
@patch.object(EmailSearchTool, '_make_request')
def test_run_success_no_emails_found_from_extraction(mock_make_request, mock_extract_emails, mock_env_serper_key):
    tool = SerperEmailSearchTool()
    mock_api_response_data = {"organic": [{"snippet": "text", "link": "link"}]}
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_data
    mock_make_request.return_value = mock_response
    mock_extract_emails.return_value = set() # No emails extracted

    result_str = tool._run(query="NoMail Corp")
    result_data = json.loads(result_str)
    assert result_data == [{"message": "No emails found"}]

@patch.object(EmailSearchTool, '_extract_emails')
@patch.object(EmailSearchTool, '_make_request')
def test_run_success_empty_organic_results(mock_make_request, mock_extract_emails, mock_env_serper_key):
    tool = SerperEmailSearchTool()
    mock_api_response_data = {"organic": []} # Empty organic results
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_data
    mock_make_request.return_value = mock_response

    result_str = tool._run(query="ZeroResults Ltd")
    result_data = json.loads(result_str)

    mock_extract_emails.assert_not_called()
    assert result_data == [{"message": "No emails found"}]

@patch.object(EmailSearchTool, '_make_request')
def test_run_api_call_fails(mock_make_request, mock_env_serper_key):
    tool = SerperEmailSearchTool()
    mock_make_request.return_value = None # Simulate request failure

    result_str = tool._run(query="FailSearch Co")
    result_data = json.loads(result_str)
    assert result_data == [{"error": "Failed to fetch data from Serper API"}]

@patch.object(EmailSearchTool, '_make_request')
def test_run_query_cleaning_and_formatting(mock_make_request, mock_env_serper_key):
    tool = SerperEmailSearchTool()
    query = "  My Test  Company  "
    expected_search_q = '"my test  company" "@mytestcompany" email'
    
    # Setup mock response to avoid error during json parsing
    mock_api_response_data = {"organic": []}
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response_data
    mock_make_request.return_value = mock_response

    tool._run(query=query)
    mock_make_request.assert_called_once_with(
        "POST",
        SERPER_API_URL,
        headers=unittest.mock.ANY, # Headers checked in other tests
        json={"q": expected_search_q}
    )

# Need to import unittest.mock for ANY if not already done
import unittest.mock
