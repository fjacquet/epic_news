import pytest
import json
from unittest.mock import patch, MagicMock

# Tool to be tested
from epic_news.tools.email_search import DelegatingEmailSearchTool, DelegatingEmailSearchInput

# Actual tools that will be mocked at the point of import within email_search.py
# We don't need to import them directly here for these tests, but it's good to be aware
# from epic_news.tools.hunter_io_tool import HunterIOTool as ActualHunterTool
# from epic_news.tools.serper_email_search_tool import SerperEmailSearchTool as ActualSerperTool

@pytest.fixture
def router_tool_instance():
    """Provides an instance of the DelegatingEmailSearchTool."""
    return DelegatingEmailSearchTool()

# --- Instantiation Test ---
def test_delegating_tool_instantiation(router_tool_instance):
    assert router_tool_instance.name == "email_search_router"
    assert "Finds professional email addresses using a specified provider." in router_tool_instance.description
    assert router_tool_instance.args_schema == DelegatingEmailSearchInput

# --- _run Method Tests (Delegation Logic) ---

@patch('epic_news.tools.email_search.HunterIOTool') # Patch where HunterIOTool is imported/used
def test_run_delegates_to_hunter_success(MockHunterToolClass, router_tool_instance):
    mock_hunter_instance = MagicMock()
    mock_hunter_instance._run.return_value = json.dumps({"hunter_data": "success"})
    MockHunterToolClass.return_value = mock_hunter_instance

    query = "example.com"
    result_str = router_tool_instance._run(provider="hunter", query=query)
    result_data = json.loads(result_str)

    MockHunterToolClass.assert_called_once_with() # Check instantiation
    mock_hunter_instance._run.assert_called_once_with(domain=query)
    assert result_data == {"hunter_data": "success"}

@patch('epic_news.tools.email_search.SerperEmailSearchTool') # Patch where SerperEmailSearchTool is imported/used
def test_run_delegates_to_serper_success(MockSerperToolClass, router_tool_instance):
    mock_serper_instance = MagicMock()
    mock_serper_instance._run.return_value = json.dumps({"serper_data": "success"})
    MockSerperToolClass.return_value = mock_serper_instance

    query = "Example Inc"
    result_str = router_tool_instance._run(provider="serper", query=query)
    result_data = json.loads(result_str)

    MockSerperToolClass.assert_called_once_with() # Check instantiation
    mock_serper_instance._run.assert_called_once_with(query=query)
    assert result_data == {"serper_data": "success"}

def test_run_invalid_provider(router_tool_instance):
    query = "test_query"
    result_str = router_tool_instance._run(provider="invalid_provider", query=query)
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert "Invalid provider: 'invalid_provider'. Must be 'hunter' or 'serper'." in result_data["error"]

@patch('epic_news.tools.email_search.HunterIOTool')
def test_run_hunter_init_error(MockHunterToolClass, router_tool_instance):
    error_message = "Mocked Hunter API Key Error"
    MockHunterToolClass.side_effect = ValueError(error_message) # Error on instantiation

    result_str = router_tool_instance._run(provider="hunter", query="example.com")
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert f"Configuration error for hunter: {error_message}" in result_data["error"]

@patch('epic_news.tools.email_search.SerperEmailSearchTool')
def test_run_serper_init_error(MockSerperToolClass, router_tool_instance):
    error_message = "Mocked Serper API Key Error"
    MockSerperToolClass.side_effect = ValueError(error_message) # Error on instantiation

    result_str = router_tool_instance._run(provider="serper", query="Example Inc")
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert f"Configuration error for serper: {error_message}" in result_data["error"]

@patch('epic_news.tools.email_search.HunterIOTool')
def test_run_hunter_runtime_error(MockHunterToolClass, router_tool_instance):
    mock_hunter_instance = MagicMock()
    error_message = "Mocked Hunter Runtime Error"
    mock_hunter_instance._run.side_effect = Exception(error_message)
    MockHunterToolClass.return_value = mock_hunter_instance

    result_str = router_tool_instance._run(provider="hunter", query="example.com")
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert f"Failed to execute search with hunter: {error_message}" in result_data["error"]

@patch('epic_news.tools.email_search.SerperEmailSearchTool')
def test_run_serper_runtime_error(MockSerperToolClass, router_tool_instance):
    mock_serper_instance = MagicMock()
    error_message = "Mocked Serper Runtime Error"
    mock_serper_instance._run.side_effect = Exception(error_message)
    MockSerperToolClass.return_value = mock_serper_instance

    result_str = router_tool_instance._run(provider="serper", query="Example Inc")
    result_data = json.loads(result_str)

    assert "error" in result_data
    assert f"Failed to execute search with serper: {error_message}" in result_data["error"]
