import os

import pytest
import requests

from epic_news.tools.fact_checking_factory import FactCheckingToolsFactory
from epic_news.tools.google_fact_check_tool import GoogleFactCheckTool


@pytest.fixture
def factory():
    return FactCheckingToolsFactory()


def test_create_google_fact_check_tool(factory, mocker):
    """Test creating a GoogleFactCheckTool from the factory."""
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
    tool = factory.create("google")
    assert isinstance(tool, GoogleFactCheckTool)
    assert tool.api_key == "test_api_key"


def test_google_fact_check_tool_missing_api_key(mocker):
    """Test that GoogleFactCheckTool raises an error if the API key is missing."""
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(ValueError, match="Google API key is not set"):
        GoogleFactCheckTool()


def test_google_fact_check_tool_run_success(mocker):
    """Test a successful run of the GoogleFactCheckTool."""
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"claims": [{"text": "Test claim"}]}
    mock_get.return_value = mock_response

    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
    tool = GoogleFactCheckTool()
    result = tool._run(query="test query")

    # Tool returns JSON string, not dict
    assert "claims" in result
    assert "Test claim" in result
    mock_get.assert_called_once_with(
        "https://factchecktools.googleapis.com/v1alpha1/claims:search",
        params={
            "query": "test query",
            "pageSize": 10,
            "key": "test_api_key",
        },
    )


def test_google_fact_check_tool_run_error(mocker):
    """Test an unsuccessful run of the GoogleFactCheckTool due to a request exception."""
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.RequestException("API error")

    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
    tool = GoogleFactCheckTool()
    result = tool._run(query="test query")

    assert "Error: API error" in result
