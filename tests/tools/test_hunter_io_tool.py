import json
import os
from unittest.mock import MagicMock, patch

import pytest

from epic_news.tools.email_base import EmailSearchTool
from epic_news.tools.hunter_io_tool import HunterIOInput, HunterIOTool

TEST_HUNTER_API_KEY = "test_hunter_key_123"
HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"


# --- Fixtures ---
@pytest.fixture
def mock_env_hunter_key():
    with patch.dict(os.environ, {"HUNTER_API_KEY": TEST_HUNTER_API_KEY}, clear=True):
        yield


@pytest.fixture
def mock_env_no_hunter_key():
    with patch.dict(os.environ, {"HUNTER_API_KEY": ""}, clear=True):
        yield


# --- Instantiation Tests ---


def test_instantiation_success(mock_env_hunter_key):
    tool = HunterIOTool()
    assert tool.name == "hunter_io_search"
    assert "Find professional email addresses" in tool.description
    assert tool.args_schema == HunterIOInput
    assert isinstance(tool.searcher, EmailSearchTool)
    assert tool.searcher.api_key == TEST_HUNTER_API_KEY


def test_instantiation_no_api_key(mock_env_no_hunter_key):
    with pytest.raises(ValueError, match="HUNTER_API_KEY environment variable not set"):
        HunterIOTool()


def test_instantiation_with_searcher_instance():
    mock_searcher = MagicMock(spec=EmailSearchTool)
    mock_searcher.api_key = "custom_key"
    tool = HunterIOTool(searcher=mock_searcher)
    assert tool.searcher == mock_searcher
    assert tool.searcher.api_key == "custom_key"


# --- _run Method Tests ---


@patch.object(EmailSearchTool, "_make_request")  # Patching on the class used by the instance
def test_run_success(mock_make_request, mock_env_hunter_key):
    tool = HunterIOTool()
    mock_response_data = {"data": {"domain": "example.com", "emails": [{"value": "test@example.com"}]}}
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = mock_response_data
    mock_make_request.return_value = mock_api_response

    domain_to_search = "example.com"
    result_json = tool._run(domain=domain_to_search)
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET", HUNTER_API_URL, params={"domain": domain_to_search, "api_key": TEST_HUNTER_API_KEY}
    )
    assert result == mock_response_data["data"]


@patch.object(EmailSearchTool, "_make_request")
def test_run_api_call_fails(mock_make_request, mock_env_hunter_key):
    tool = HunterIOTool()
    mock_make_request.return_value = None  # Simulate request failure

    result_json = tool._run(domain="example.com")
    result = json.loads(result_json)

    assert result == {"error": "Failed to fetch data from Hunter.io"}


@patch.object(EmailSearchTool, "_make_request")
def test_run_api_returns_no_data_key(mock_make_request, mock_env_hunter_key):
    tool = HunterIOTool()
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = {"errors": [{"message": "Some API error"}]}  # No 'data' key
    mock_make_request.return_value = mock_api_response

    result_json = tool._run(domain="example.com")
    result = json.loads(result_json)

    assert result == {}  # Default from .get("data", {})


@patch.object(EmailSearchTool, "_make_request")
def test_run_empty_domain(mock_make_request, mock_env_hunter_key):
    tool = HunterIOTool()
    mock_response_data = {"data": {"domain": "", "emails": []}}
    mock_api_response = MagicMock()
    mock_api_response.json.return_value = mock_response_data
    mock_make_request.return_value = mock_api_response

    result_json = tool._run(domain="")
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET", HUNTER_API_URL, params={"domain": "", "api_key": TEST_HUNTER_API_KEY}
    )
    assert result == mock_response_data["data"]
