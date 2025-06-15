import json
import os
import unittest.mock
from unittest.mock import MagicMock, patch

import pytest
import requests

from epic_news.tools.scrape_ninja_tool import ScrapeNinjaInput, ScrapeNinjaTool

TEST_RAPIDAPI_KEY = "test_rapidapi_key_for_ninja"
SCRAPENINJA_API_URL = "https://scrapeninja.p.rapidapi.com/scrape"

# --- Fixtures ---
@pytest.fixture
def mock_env_rapidapi_key():
    with patch.dict(os.environ, {"RAPIDAPI_KEY": TEST_RAPIDAPI_KEY}, clear=True):
        yield

@pytest.fixture
def mock_env_no_rapidapi_key():
    with patch.dict(os.environ, {"RAPIDAPI_KEY": ""}, clear=True):
        yield

# --- Instantiation Tests ---
def test_instantiation_success(mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    assert tool.name == "ScrapeNinja"
    assert "Scrapes website content using the ScrapeNinja API" in tool.description
    assert tool.args_schema == ScrapeNinjaInput
    assert tool.api_key == TEST_RAPIDAPI_KEY

def test_instantiation_no_api_key(mock_env_no_rapidapi_key):
    with pytest.raises(ValueError, match="RAPIDAPI_KEY environment variable not set"):
        ScrapeNinjaTool()

# --- _run Method Tests ---
@patch('requests.post')
def test_run_basic_success_plain_text_response(mock_requests_post, mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    url_to_scrape = "http://example.com"
    plain_text_content = "<html><body>Hello World</body></html>"

    mock_api_response = MagicMock()
    mock_api_response.text = plain_text_content
    mock_api_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_api_response

    result_str = tool._run(url=url_to_scrape)
    expected_payload = {
        "url": url_to_scrape,
        "retryNum": 1,
        "followRedirects": 1,
        "timeout": 8
    }
    expected_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-RapidAPI-Key": TEST_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "scrapeninja.p.rapidapi.com"
    }

    mock_requests_post.assert_called_once_with(
        SCRAPENINJA_API_URL,
        headers=expected_headers,
        data=json.dumps(expected_payload)
    )
    assert json.loads(result_str) == {"content": plain_text_content}

@patch('requests.post')
def test_run_basic_success_json_response(mock_requests_post, mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    url_to_scrape = "http://example.com/api/data"
    json_content_str = '{"title": "Example API", "data": [1, 2, 3]}'

    mock_api_response = MagicMock()
    mock_api_response.text = json_content_str
    mock_api_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_api_response

    result_str = tool._run(url=url_to_scrape)
    assert result_str == json_content_str # Should return the JSON string as is

@patch('requests.post')
def test_run_with_all_optional_params(mock_requests_post, mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    url_to_scrape = "http://advanced.example.com"
    params = {
        "url": url_to_scrape,
        "headers": ["X-Custom-Header: Value"],
        "retry_num": 3,
        "geo": "de",
        "proxy": "http://user:pass@proxy.example.com:8080",
        "follow_redirects": 0,
        "timeout": 15,
        "text_not_expected": ["Access Denied"],
        "status_not_expected": [403, 500],
        "extractor": "() => document.title"
    }
    expected_payload = {
        "url": url_to_scrape,
        "retryNum": params["retry_num"],
        "followRedirects": params["follow_redirects"],
        "timeout": params["timeout"],
        # Optional params added in order of checks in _run
        "headers": params["headers"],
        "geo": params["geo"],
        "proxy": params["proxy"],
        "textNotExpected": params["text_not_expected"],
        "statusNotExpected": params["status_not_expected"],
        "extractor": params["extractor"]
    }

    mock_api_response = MagicMock()
    mock_api_response.text = '{"title": "Advanced Scrape"}'
    mock_api_response.raise_for_status.return_value = None
    mock_requests_post.return_value = mock_api_response

    result_str = tool._run(**params)
    mock_requests_post.assert_called_once_with(
        SCRAPENINJA_API_URL,
        headers=unittest.mock.ANY, # Headers are checked in basic test
        data=json.dumps(expected_payload)
    )
    assert result_str == '{"title": "Advanced Scrape"}'

@patch('requests.post')
def test_run_requests_exception(mock_requests_post, mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    url_to_scrape = "http://example.com"
    error_message = "Network connection failed"
    mock_requests_post.side_effect = requests.exceptions.RequestException(error_message)

    result_str = tool._run(url=url_to_scrape)
    expected_error = {"error": f"Error scraping {url_to_scrape}: {error_message}"}
    assert json.loads(result_str) == expected_error

@patch('requests.post')
def test_run_http_error(mock_requests_post, mock_env_rapidapi_key):
    tool = ScrapeNinjaTool()
    url_to_scrape = "http://example.com"
    error_message = "401 Client Error: Unauthorized for url"
    
    mock_api_response = MagicMock()
    mock_api_response.raise_for_status.side_effect = requests.exceptions.HTTPError(error_message)
    mock_requests_post.return_value = mock_api_response

    result_str = tool._run(url=url_to_scrape)
    expected_error = {"error": f"Error scraping {url_to_scrape}: {error_message}"}
    assert json.loads(result_str) == expected_error


