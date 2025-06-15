import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Assuming tests are run from the project root or 'src' is in PYTHONPATH
from epic_news.tools.tech_stack_tool import TechStackInput, TechStackTool

# Sample SERPER API Key for tests
TEST_SERPER_API_KEY = "test_serper_api_key_123"

@patch.dict(os.environ, {"SERPER_API_KEY": TEST_SERPER_API_KEY})
def test_tech_stack_tool_instantiation_success():
    """Test successful instantiation when SERPER_API_KEY is set."""
    # Mock BaseSearchTool's _search_serper to avoid issues if it's called during init
    with patch('epic_news.tools.search_base.BaseSearchTool._search_serper', MagicMock(return_value={})):
        tool = TechStackTool()
    assert tool.api_key == TEST_SERPER_API_KEY
    assert tool.name == "tech_stack_analysis"
    # Adjust description assertion based on BaseTool behavior
    assert "Analyze the technology stack used by a website" in tool.description 
    assert tool.args_schema == TechStackInput

@patch.dict(os.environ, {}, clear=True) # Ensure SERPER_API_KEY is not set
def test_tech_stack_tool_instantiation_no_api_key():
    """Test instantiation failure when SERPER_API_KEY is not set."""
    with pytest.raises(ValueError) as excinfo:
        # Mock BaseSearchTool's _search_serper to avoid issues if it's called during init
        with patch('epic_news.tools.search_base.BaseSearchTool._search_serper', MagicMock(return_value={})):
            TechStackTool()
    assert "SERPER_API_KEY environment variable not set" in str(excinfo.value)


@pytest.fixture
def tech_stack_tool_instance_with_mock(): # Renamed fixture
    """Fixture to create a TechStackTool instance with SERPER_API_KEY set and _search_serper mocked."""
    # Patch _search_serper on BaseSearchTool where it's defined
    with patch('epic_news.tools.search_base.BaseSearchTool._search_serper') as mock_search_serper_method:
        with patch.dict(os.environ, {"SERPER_API_KEY": TEST_SERPER_API_KEY}):
            tool = TechStackTool()
        yield tool, mock_search_serper_method # Yield tool and the mock

def test_run_simple_success(tech_stack_tool_instance_with_mock): # Updated to use new fixture
    """Test _run method with detailed=False and successful tech identification."""
    domain_to_test = "example.com"
    mock_search_results = [
        {"title": "Example Tech", "snippet": "Uses React and Google Analytics"},
        {"title": "Another Example", "snippet": "Powered by WordPress"}
    ]
    tool, mock_search_serper = tech_stack_tool_instance_with_mock
    mock_search_serper.return_value = {"organic": mock_search_results}

    expected_tech = sorted(['react', 'google analytics', 'wordpress']) # From TECH_PATTERNS

    result_json = tool._run(domain=domain_to_test, detailed=False)
    result = json.loads(result_json)

    assert result["domain"] == domain_to_test
    assert sorted(result["technologies"]) == expected_tech
    assert result["detailed_analysis"] is None
    assert "error" not in result
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )


def test_run_detailed_success(tech_stack_tool_instance_with_mock):
    """Test _run method with detailed=True and successful tech identification."""
    tool, mock_search_serper = tech_stack_tool_instance_with_mock
    domain_to_test = "detailed-example.com"
    mock_search_results = [
        {"title": "Detailed Tech Co", "snippet": "We use React, Next.js, and Google Analytics for our analytics."},
        {"title": "Platform Info", "snippet": "Hosted on Vercel, CMS is WordPress."}
    ]
    mock_search_serper.return_value = {"organic": mock_search_results}

    expected_raw_tech = sorted(['react', 'next.js', 'google analytics', 'vercel', 'wordpress'])
    expected_detailed_analysis = {
        'frameworks': sorted(['react', 'next.js']),
        'analytics': ['google analytics'],
        'hosting': ['vercel'],
        'cms': ['wordpress']
    }

    result_json = tool._run(domain=domain_to_test, detailed=True)
    result = json.loads(result_json)

    assert result["domain"] == domain_to_test
    assert sorted(result["technologies"]) == expected_raw_tech
    assert result["detailed_analysis"] is not None
    
    # Sort lists within the detailed_analysis for consistent comparison
    for category in result["detailed_analysis"]:
        result["detailed_analysis"][category] = sorted(result["detailed_analysis"][category])
        
    assert result["detailed_analysis"] == expected_detailed_analysis
    assert "error" not in result
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )


def test_run_no_search_results(tech_stack_tool_instance_with_mock):
    """Test _run method when _search_serper returns no organic results."""
    tool, mock_search_serper = tech_stack_tool_instance_with_mock
    domain_to_test = "no-results-example.com"
    
    # Scenario 1: detailed=False
    mock_search_serper.return_value = {"organic": []} 

    result_json = tool._run(domain=domain_to_test, detailed=False)
    result = json.loads(result_json)

    assert result["domain"] == domain_to_test
    assert result["technologies"] == []
    assert result["detailed_analysis"] is None
    assert "error" not in result 
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )

    # Reset mock for Scenario 2: detailed=True
    mock_search_serper.reset_mock()
    mock_search_serper.return_value = {"organic": []}

    result_json_detailed = tool._run(domain=domain_to_test, detailed=True)
    result_detailed = json.loads(result_json_detailed)

    assert result_detailed["domain"] == domain_to_test
    assert result_detailed["technologies"] == []
    # When detailed is true and no tech found, detailed_analysis should be an empty dict
    assert result_detailed["detailed_analysis"] == {} 
    assert "error" not in result_detailed
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )


def test_run_search_api_error(tech_stack_tool_instance_with_mock):
    """Test _run method when _search_serper (via _search_tech_sites) encounters an API error."""
    tool, mock_search_serper = tech_stack_tool_instance_with_mock
    domain_to_test = "error-example.com"
    simulated_exception_text = "Simulated API failure during search"
    expected_error_in_output = f"An error occurred during analysis: {simulated_exception_text}"
    
    # Configure the mock to raise an exception when called
    mock_search_serper.side_effect = Exception(simulated_exception_text)

    # Call _run with detailed=False
    result_json = tool._run(domain=domain_to_test, detailed=False)
    result = json.loads(result_json)

    assert result["domain"] == domain_to_test
    assert "technologies" not in result
    assert "detailed_analysis" not in result
    assert result.get("error") == expected_error_in_output
    
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )

    # Reset mock for detailed=True test
    mock_search_serper.reset_mock()
    mock_search_serper.side_effect = Exception(simulated_exception_text)

    result_json_detailed = tool._run(domain=domain_to_test, detailed=True)
    result_detailed = json.loads(result_json_detailed)

    assert result_detailed["domain"] == domain_to_test
    assert "technologies" not in result_detailed
    assert "detailed_analysis" not in result_detailed
    assert result_detailed.get("error") == expected_error_in_output
    mock_search_serper.assert_called_once_with(
        f"site:builtwith.com OR site:wappalyzer.com OR site:stackshare.io {domain_to_test}"
    )

# More tests will follow for _run (detailed, errors, etc.) and direct tests for helper methods will follow.
