"""Tests for PerplexitySearchTool."""

import json
import os

import pytest
import requests

from epic_news.tools.perplexity_search_tool import (
    PerplexitySearchInput,
    PerplexitySearchTool,
)

TEST_PERPLEXITY_API_KEY = "test_perplexity_key"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# --- Fixtures ---
@pytest.fixture
def mock_env_perplexity_key(mocker):
    """Mock environment with Perplexity API key."""
    mocker.patch.dict(os.environ, {"PERPLEXITY_API_KEY": TEST_PERPLEXITY_API_KEY}, clear=True)
    yield


@pytest.fixture
def mock_env_no_perplexity_key(mocker):
    """Mock environment without Perplexity API key."""
    mocker.patch.dict(os.environ, {"PERPLEXITY_API_KEY": ""}, clear=True)
    yield


# --- Instantiation Tests ---
def test_instantiation_success(mock_env_perplexity_key):
    """Test successful tool instantiation with API key."""
    tool = PerplexitySearchTool()
    assert tool.name == "perplexity_search"
    assert "AI-powered web search" in tool.description
    assert tool.args_schema == PerplexitySearchInput
    assert tool.api_key == TEST_PERPLEXITY_API_KEY


def test_instantiation_no_api_key(mock_env_no_perplexity_key):
    """Test tool instantiation without API key."""
    tool = PerplexitySearchTool()
    # API key is None when not set or empty
    assert tool.api_key is None


# --- _run Method Tests ---
def test_run_no_api_key(mock_env_no_perplexity_key):
    """Test _run returns error when API key is missing."""
    tool = PerplexitySearchTool()
    result_str = tool._run(query="test query")
    result_data = json.loads(result_str)

    assert result_data["success"] is False
    assert "not configured" in result_data["error"]


def test_run_success(mock_env_perplexity_key, mocker):
    """Test successful search execution."""
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test answer about Python."}}],
        "citations": ["https://python.org", "https://docs.python.org"],
        "model": "sonar",
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    tool = PerplexitySearchTool()
    result_str = tool._run(query="What is Python?")
    result_data = json.loads(result_str)

    # Verify API call
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == PERPLEXITY_API_URL
    assert "Authorization" in call_args[1]["headers"]
    assert call_args[1]["json"]["model"] == "sonar"
    assert call_args[1]["json"]["messages"][0]["content"] == "What is Python?"

    # Verify result
    assert result_data["success"] is True
    assert result_data["answer"] == "Test answer about Python."
    assert result_data["citations"] == ["https://python.org", "https://docs.python.org"]
    assert result_data["source"] == "perplexity"


def test_run_with_focus_and_recency(mock_env_perplexity_key, mocker):
    """Test search with custom focus and recency parameters."""
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Latest news."}}],
        "citations": [],
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    tool = PerplexitySearchTool()
    result_str = tool._run(query="AI news", focus="news", recency="day")
    result_data = json.loads(result_str)

    # Verify API call parameters
    call_args = mock_post.call_args
    assert call_args[1]["json"]["search_recency_filter"] == "day"

    assert result_data["success"] is True


def test_run_api_error(mock_env_perplexity_key, mocker):
    """Test handling of API errors."""
    mock_post = mocker.patch("requests.post")
    mock_post.side_effect = requests.exceptions.RequestException("Connection failed")

    tool = PerplexitySearchTool()
    result_str = tool._run(query="test query")
    result_data = json.loads(result_str)

    assert result_data["success"] is False
    assert "Connection failed" in result_data["error"]
    assert result_data["fallback_needed"] is True


def test_run_http_error(mock_env_perplexity_key, mocker):
    """Test handling of HTTP errors."""
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_post.return_value = mock_response

    tool = PerplexitySearchTool()
    result_str = tool._run(query="test query")
    result_data = json.loads(result_str)

    assert result_data["success"] is False
    assert result_data["fallback_needed"] is True


def test_run_empty_citations(mock_env_perplexity_key, mocker):
    """Test handling of responses without citations."""
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Answer without citations."}}],
        # No citations field
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    tool = PerplexitySearchTool()
    result_str = tool._run(query="simple question")
    result_data = json.loads(result_str)

    assert result_data["success"] is True
    assert result_data["citations"] == []


# --- Input Schema Tests ---
def test_input_schema_defaults():
    """Test PerplexitySearchInput default values."""
    input_data = PerplexitySearchInput(query="test")
    assert input_data.query == "test"
    assert input_data.focus == "internet"
    assert input_data.recency == "week"


def test_input_schema_custom_values():
    """Test PerplexitySearchInput with custom values."""
    input_data = PerplexitySearchInput(
        query="news about AI",
        focus="news",
        recency="day",
    )
    assert input_data.query == "news about AI"
    assert input_data.focus == "news"
    assert input_data.recency == "day"
