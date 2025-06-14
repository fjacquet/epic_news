import pytest
import json
import os
from unittest.mock import patch, MagicMock, ANY

from epic_news.tools.github_search_tool import GitHubSearchTool, GitHubSearchInput

TEST_GITHUB_TOKEN = "ghp_test_token_for_search_tool"
GITHUB_SEARCH_URL_BASE = "https://api.github.com/search/"

# --- Fixtures ---
@pytest.fixture
def mock_env_github_token():
    with patch.dict(os.environ, {"GITHUB_TOKEN": TEST_GITHUB_TOKEN}, clear=True):
        yield

@pytest.fixture
def mock_env_no_github_token():
    with patch.dict(os.environ, {"GITHUB_TOKEN": ""}, clear=True):
        yield

# --- Instantiation Tests ---

def test_instantiation_success(mock_env_github_token):
    tool = GitHubSearchTool()
    assert tool.name == "github_search"
    assert "Search GitHub for repositories" in tool.description
    assert tool.args_schema == GitHubSearchInput
    assert tool.api_key == TEST_GITHUB_TOKEN
    assert tool.headers["Authorization"] == f"token {TEST_GITHUB_TOKEN}"

def test_instantiation_no_token(mock_env_no_github_token):
    with pytest.raises(ValueError, match="GITHUB_TOKEN environment variable not set"):
        GitHubSearchTool()

# --- _run Method Tests ---

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_invalid_search_type(mock_make_request, mock_env_github_token):
    tool = GitHubSearchTool()
    result_json = tool._run(query="test", search_type="invalid_type")
    result = json.loads(result_json)
    assert "error" in result
    assert "Invalid search type" in result["error"]
    mock_make_request.assert_not_called()

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_api_request_fails(mock_make_request, mock_env_github_token):
    mock_make_request.return_value = None
    tool = GitHubSearchTool()
    result_json = tool._run(query="test", search_type="repositories")
    result = json.loads(result_json)
    assert "error" in result
    assert "Failed to search GitHub repositories" in result["error"]

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_search_repositories_success(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total_count": 1,
        "items": [
            {"full_name": "test/repo1", "html_url": "url1", "description": "desc1", "stargazers_count": 10, "forks_count": 5}
        ]
    }
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    result_json = tool._run(query="test_query", search_type="repositories", max_results=3)
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET",
        f"{GITHUB_SEARCH_URL_BASE}repositories",
        headers=tool.headers,
        params={"q": "test_query", "per_page": 3}
    )
    assert result["query"] == "test_query"
    assert result["search_type"] == "repositories"
    assert result["total_count"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["name"] == "test/repo1"

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_search_code_success(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total_count": 1,
        "items": [
            {"name": "file.py", "path": "src/file.py", "repository": {"full_name": "test/repo"}, "html_url": "code_url"}
        ]
    }
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    result_json = tool._run(query="test_func", search_type="code", max_results=1)
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET",
        f"{GITHUB_SEARCH_URL_BASE}code",
        headers=tool.headers,
        params={"q": "test_func", "per_page": 1}
    )
    assert result["results"][0]["name"] == "file.py"
    assert result["results"][0]["repository"] == "test/repo"

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_search_issues_success(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total_count": 1,
        "items": [
            {"title": "Bug fix", "html_url": "issue_url", "state": "open", "comments": 2, "created_at": "2023-01-01T00:00:00Z"}
        ]
    }
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    result_json = tool._run(query="fix critical bug", search_type="issues")
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET",
        f"{GITHUB_SEARCH_URL_BASE}issues",
        headers=tool.headers,
        params={"q": "fix critical bug", "per_page": 5} # Default max_results
    )
    assert result["results"][0]["title"] == "Bug fix"
    assert result["results"][0]["state"] == "open"

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_search_users_success(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total_count": 1,
        "items": [
            {"login": "testuser", "html_url": "user_url", "type": "User", "score": 1.0}
        ]
    }
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    result_json = tool._run(query="John Doe", search_type="users")
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        "GET",
        f"{GITHUB_SEARCH_URL_BASE}users",
        headers=tool.headers,
        params={"q": "John Doe", "per_page": 5}
    )
    assert result["results"][0]["login"] == "testuser"
    assert result["results"][0]["type"] == "User"

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_max_results_respected(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    # Simulate API returning more items than requested to check truncation logic (though API should handle per_page)
    mock_response.json.return_value = {
        "total_count": 10,
        "items": [{"full_name": f"test/repo{i}", "html_url": f"url{i}"} for i in range(10)]
    }
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    tool._run(query="many_results", search_type="repositories", max_results=2)

    mock_make_request.assert_called_once_with(
        ANY, ANY, headers=ANY, params={"q": "many_results", "per_page": 2}
    )
    # The tool itself doesn't truncate, it relies on GitHub API's per_page.
    # The formatting loop will process whatever 'items' contains.

@patch('epic_news.tools.github_base.GitHubBaseTool._make_request')
def test_run_empty_query(mock_make_request, mock_env_github_token):
    mock_response = MagicMock()
    mock_response.json.return_value = {"total_count": 0, "items": []}
    mock_make_request.return_value = mock_response
    tool = GitHubSearchTool()
    result_json = tool._run(query="", search_type="repositories")
    result = json.loads(result_json)

    mock_make_request.assert_called_once_with(
        ANY, ANY, headers=ANY, params={"q": "", "per_page": 5}
    )
    assert result["query"] == ""
    assert len(result["results"]) == 0
