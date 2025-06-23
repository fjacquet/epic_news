import json
import os
from unittest.mock import ANY, MagicMock, patch

import pytest

from epic_news.tools.github_org_tool import GitHubOrgSearchInput, GitHubOrgSearchTool

TEST_GITHUB_TOKEN = "ghp_test_token_12345"
TEST_SERPER_API_KEY = "serper_test_key_67890"
GITHUB_ORGS_URL_TEMPLATE = "https://api.github.com/orgs/{org_name}"
SERPER_API_URL = "https://google.serper.dev/search"


# --- Fixtures ---
@pytest.fixture
def mock_env_github_only():
    with patch.dict(os.environ, {"GITHUB_TOKEN": TEST_GITHUB_TOKEN, "SERPER_API_KEY": ""}, clear=True):
        yield


@pytest.fixture
def mock_env_serper_only():  # Still need GITHUB_TOKEN for GitHubBaseTool init
    with patch.dict(
        os.environ, {"GITHUB_TOKEN": TEST_GITHUB_TOKEN, "SERPER_API_KEY": TEST_SERPER_API_KEY}, clear=True
    ):
        yield


@pytest.fixture
def mock_env_both_keys():
    with patch.dict(
        os.environ, {"GITHUB_TOKEN": TEST_GITHUB_TOKEN, "SERPER_API_KEY": TEST_SERPER_API_KEY}, clear=True
    ):
        yield


@pytest.fixture
def mock_env_no_github_token():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "", "SERPER_API_KEY": TEST_SERPER_API_KEY}, clear=True):
        yield


@pytest.fixture
def mock_env_no_keys():
    with patch.dict(os.environ, {"GITHUB_TOKEN": "", "SERPER_API_KEY": ""}, clear=True):
        yield


# --- Instantiation Tests ---


def test_instantiation_github_only(mock_env_github_only):
    tool = GitHubOrgSearchTool()
    assert tool.name == "github_org_search"
    assert "Search for a GitHub organization" in tool.description
    assert tool.args_schema == GitHubOrgSearchInput
    assert tool.api_key == TEST_GITHUB_TOKEN  # From GitHubBaseTool
    assert tool.serper_api_key == ""


def test_instantiation_serper_present(mock_env_serper_only):
    tool = GitHubOrgSearchTool()
    assert tool.api_key == TEST_GITHUB_TOKEN
    assert tool.serper_api_key == TEST_SERPER_API_KEY


def test_instantiation_both_keys(mock_env_both_keys):
    tool = GitHubOrgSearchTool()
    assert tool.api_key == TEST_GITHUB_TOKEN
    assert tool.serper_api_key == TEST_SERPER_API_KEY


def test_instantiation_no_github_token(mock_env_no_github_token):
    with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set"):
        # The error is raised in GitHubOrgSearchTool's __init__ when GITHUB_TOKEN is not found for GitHubBaseTool
        # Forcing the check within GitHubOrgSearchTool itself for clarity, though base class would also fail.
        GitHubOrgSearchTool()


# --- _run Method Tests ---


@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_github_api_success_with_repos(mock_make_request, mock_env_github_only):
    mock_org_response = MagicMock()
    mock_org_response.json.return_value = {
        "login": "testorg",
        "name": "Test Organization",
        "html_url": "https://github.com/testorg",
        "description": "A test org",
        "public_repos": 10,
        "followers": 100,
        "repos_url": "https://api.github.com/orgs/testorg/repos",
    }
    mock_repos_response = MagicMock()
    mock_repos_response.json.return_value = [
        {"name": "repo1", "html_url": "https://github.com/testorg/repo1"},
        {"name": "repo2", "html_url": "https://github.com/testorg/repo2"},
    ]
    mock_make_request.side_effect = [mock_org_response, mock_repos_response]

    tool = GitHubOrgSearchTool()
    result_json = tool._run(org_name="testorg")
    result = json.loads(result_json)

    assert result["exists"]
    assert result["login"] == "testorg"
    assert len(result["top_repos"]) == 2
    assert result["top_repos"][0]["name"] == "repo1"
    mock_make_request.assert_any_call("GET", "https://api.github.com/orgs/testorg", headers=ANY)
    mock_make_request.assert_any_call("GET", "https://api.github.com/orgs/testorg/repos", headers=ANY)


@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_github_api_success_no_repos_url(mock_make_request, mock_env_github_only):
    mock_org_response = MagicMock()
    mock_org_response.json.return_value = {
        "login": "testorg",
        "name": "Test Organization",
        "html_url": "https://github.com/testorg",
        "description": "A test org",
        "public_repos": 10,
        "followers": 100,
        "repos_url": None,  # No repos URL
    }
    mock_make_request.return_value = mock_org_response

    tool = GitHubOrgSearchTool()
    result_json = tool._run(org_name="testorg")
    result = json.loads(result_json)

    assert result["exists"]
    assert result["login"] == "testorg"
    assert result["top_repos"] == []
    mock_make_request.assert_called_once_with("GET", "https://api.github.com/orgs/testorg", headers=ANY)


@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_github_api_org_not_found(mock_make_request, mock_env_github_only):
    mock_make_request.return_value = None  # Simulate API error or 404
    tool = GitHubOrgSearchTool()
    result_json = tool._run(org_name="nonexistentorg")
    result = json.loads(result_json)
    assert "error" in result
    assert "Failed to fetch data from GitHub API" in result["error"]


def test_run_empty_org_name(mock_env_github_only):
    tool = GitHubOrgSearchTool()
    result_json = tool._run(org_name="")
    result = json.loads(result_json)
    assert result["error"] == "Organization name cannot be empty"


@patch("epic_news.tools.github_org_tool.os.getenv")
@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_serper_fallback_success(mock_make_request, mock_os_getenv_in_tool_module, mock_env_serper_only):
    # mock_env_serper_only provides GITHUB_TOKEN for tool init, and SERPER_API_KEY
    tool = GitHubOrgSearchTool()  # Instantiation uses GITHUB_TOKEN from mock_env_serper_only

    # When tool._run() calls os.getenv("GITHUB_TOKEN"), make it return ""
    # This forces the Serper path. Other os.getenv calls use the environment from mock_env_serper_only.
    mock_os_getenv_in_tool_module.side_effect = (
        lambda k, d=None: "" if k == "GITHUB_TOKEN" else os.environ.get(k, d)
    )

    mock_serper_response = MagicMock()
    mock_serper_response.json.return_value = {
        "organic": [{"link": "https://github.com/testorg", "title": "Test Org on GitHub"}]
    }
    mock_make_request.return_value = mock_serper_response

    result_json = tool._run(org_name="testorg")
    result = json.loads(result_json)

    assert result["exists"]
    assert result["name"] == "testorg"
    assert result["url"] == "https://github.com/testorg"
    assert result["source"] == "serper"
    expected_payload = {"q": 'site:github.com/orgs "testorg"'}
    mock_make_request.assert_called_once_with("POST", SERPER_API_URL, headers=ANY, json=expected_payload)


@patch("epic_news.tools.github_org_tool.os.getenv")
@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_serper_fallback_not_found(
    mock_make_request, mock_os_getenv_in_tool_module, mock_env_serper_only
):
    tool = GitHubOrgSearchTool()
    mock_os_getenv_in_tool_module.side_effect = (
        lambda k, d=None: "" if k == "GITHUB_TOKEN" else os.environ.get(k, d)
    )

    mock_serper_response = MagicMock()
    mock_serper_response.json.return_value = {"organic": []}  # No results
    mock_make_request.return_value = mock_serper_response

    result_json = tool._run(org_name="nonexistentorg_serper")
    result = json.loads(result_json)

    assert not result["exists"]
    assert result["name"] == "nonexistentorg_serper"
    assert result["source"] == "serper"


@patch("epic_news.tools.github_org_tool.os.getenv")
@patch("epic_news.tools.github_base.GitHubBaseTool._make_request")
def test_run_serper_fallback_api_error(
    mock_make_request, mock_os_getenv_in_tool_module, mock_env_serper_only
):
    tool = GitHubOrgSearchTool()
    mock_os_getenv_in_tool_module.side_effect = (
        lambda k, d=None: "" if k == "GITHUB_TOKEN" else os.environ.get(k, d)
    )

    mock_make_request.return_value = None  # Simulate Serper API error

    result_json = tool._run(org_name="testorg_serper_fail")
    result = json.loads(result_json)

    assert "error" in result
    assert "Failed to fetch data from Serper API" in result["error"]


def test_run_no_keys_available(mock_env_no_keys):
    # GitHubOrgSearchTool's __init__ will raise ValueError if GITHUB_TOKEN is not set
    # because GitHubBaseTool requires it. So, this specific path in _run might be hard to reach
    # if GITHUB_TOKEN is strictly enforced at init.
    # However, if GITHUB_TOKEN was cleared *after* init, this path could be hit.
    # Forcing the condition by directly calling _run after init with no keys.
    with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set"):
        GitHubOrgSearchTool()  # This will fail first if GITHUB_TOKEN is not set

    # To test the specific _run logic if init somehow passed with no GITHUB_TOKEN (e.g. if base was different)
    # we'd need to mock the os.getenv calls within _run itself or manipulate the instance's state.
    # Given the current structure, the primary check is the init failure.

    # Simulating the scenario where init passed but keys were removed before _run
    with patch.dict(
        os.environ, {"GITHUB_TOKEN": TEST_GITHUB_TOKEN, "SERPER_API_KEY": ""}, clear=True
    ):  # Init with GitHub token
        tool = GitHubOrgSearchTool()

    with patch.dict(  # noqa: SIM117
        os.environ, {"GITHUB_TOKEN": "", "SERPER_API_KEY": ""}, clear=True
    ):  # Clear keys before _run  # noqa: SIM117
        # Patch os.getenv specifically for the _run method's checks
        with patch("os.getenv") as mock_os_getenv:
            # First getenv is for GITHUB_TOKEN, second for SERPER_API_KEY inside _run
            mock_os_getenv.side_effect = ["", ""]
            result_json = tool._run(org_name="anyorg")
            result = json.loads(result_json)
            assert result["error"] == "Configuration error: Neither GITHUB_TOKEN nor SERPER_API_KEY is set."
