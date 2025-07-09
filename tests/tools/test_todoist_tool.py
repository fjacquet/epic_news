import os
import sys
from pathlib import Path

import pytest

# Add the project root to the path so we can import from epic_news
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from epic_news.tools.todoist_tool import TodoistTool


@pytest.fixture
def tool():
    """Fixture to provide a TodoistTool instance."""
    return TodoistTool()


def test_initialization(tool, mocker):
    """Test that the tool initializes correctly."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    assert tool.name == "todoist_tool"
    assert tool.base_url == "https://api.todoist.com/rest/v2"


def test_missing_api_key(tool, mocker):
    """Test that an error is raised if the API key is missing."""
    mocker.patch.dict(os.environ, {}, clear=True)
    result = tool._run(action="get_tasks")
    assert "TODOIST_API_KEY environment variable not set" in result


def test_get_tasks(tool, mocker):
    """Test getting tasks from Todoist."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    mock_get = mocker.patch("epic_news.tools.todoist_tool.requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "1", "content": "Task 1"}, {"id": "2", "content": "Task 2"}]
    mock_get.return_value = mock_response

    result = tool._run(action="get_tasks")

    assert "Found 2 tasks" in result
    expected_headers = {"Authorization": "Bearer fake_api_token", "Content-Type": "application/json"}
    mock_get.assert_called_once_with(
        "https://api.todoist.com/rest/v2/tasks", headers=expected_headers, params={}
    )


def test_get_tasks_with_project(tool, mocker):
    """Test getting tasks from a specific project."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    mock_get = mocker.patch("epic_news.tools.todoist_tool.requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "1", "content": "Project Task"}]
    mock_get.return_value = mock_response

    result = tool._run(action="get_tasks", project_id="123")

    assert "Found 1 tasks" in result
    expected_headers = {"Authorization": "Bearer fake_api_token", "Content-Type": "application/json"}
    mock_get.assert_called_once_with(
        "https://api.todoist.com/rest/v2/tasks", headers=expected_headers, params={"project_id": "123"}
    )


def test_create_task(tool, mocker):
    """Test creating a task in Todoist."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    mock_post = mocker.patch("epic_news.tools.todoist_tool.requests.post")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "new_task", "content": "New Task"}
    mock_post.return_value = mock_response

    result = tool._run(action="create_task", task_content="New Task", due_string="tomorrow", priority=4)

    assert "Task created successfully" in result
    expected_headers = {"Authorization": "Bearer fake_api_token", "Content-Type": "application/json"}
    mock_post.assert_called_once_with(
        "https://api.todoist.com/rest/v2/tasks",
        headers=expected_headers,
        json={"content": "New Task", "due_string": "tomorrow", "priority": 4},
    )


def test_complete_task(tool, mocker):
    """Test completing a task in Todoist."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    mock_post = mocker.patch("epic_news.tools.todoist_tool.requests.post")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 204
    mock_post.return_value = mock_response

    result = tool._run(action="complete_task", task_id="task_123")

    assert "Task task_123 completed successfully" in result
    expected_headers = {"Authorization": "Bearer fake_api_token", "Content-Type": "application/json"}
    mock_post.assert_called_once_with(
        "https://api.todoist.com/rest/v2/tasks/task_123/close", headers=expected_headers
    )


def test_get_projects(tool, mocker):
    """Test getting projects from Todoist."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    mock_get = mocker.patch("epic_news.tools.todoist_tool.requests.get")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": "1", "name": "Project 1"}, {"id": "2", "name": "Project 2"}]
    mock_get.return_value = mock_response

    result = tool._run(action="get_projects")

    assert "Found 2 projects" in result
    expected_headers = {"Authorization": "Bearer fake_api_token", "Content-Type": "application/json"}
    mock_get.assert_called_once_with("https://api.todoist.com/rest/v2/projects", headers=expected_headers)


def test_invalid_action(tool, mocker):
    """Test handling of invalid actions."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    result = tool._run(action="invalid_action")
    assert "Error: Unknown action" in result


def test_missing_required_params(tool, mocker):
    """Test handling of missing required parameters."""
    mocker.patch.dict(os.environ, {"TODOIST_API_KEY": "fake_api_token"})
    result = tool._run(action="create_task")
    assert "Error: task_content is required" in result

    result = tool._run(action="complete_task")
    assert "Error: task_id is required" in result
