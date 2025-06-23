import json
from unittest.mock import MagicMock, patch

import pytest
from crewai_tools import RagTool  # For type hinting and potentially mocking its instantiation

# Assuming tests are run from the project root or 'src' is in PYTHONPATH
from epic_news.tools.save_to_rag_tool import SaveToRagInput, SaveToRagTool

# Mock DEFAULT_RAG_CONFIG as it's imported by save_to_rag_tool
# We need to patch it where it's looked up by save_to_rag_tool
MOCK_DEFAULT_RAG_CONFIG = {
    "type": "chroma",
    "db_path": "/tmp/mock_rag_db",
    "collection_name": "mock_rag_collection",
}


@pytest.fixture
def mock_rag_tool_instance():
    """Fixture to create a MagicMock instance of RagTool."""
    mock_rag = MagicMock(spec=RagTool)
    mock_rag.add = MagicMock()  # Mock the 'add' method specifically
    return mock_rag


def test_save_to_rag_tool_instantiation_with_rag_tool(mock_rag_tool_instance):
    """Test tool instantiation when a RagTool instance is provided."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    assert tool._rag_tool == mock_rag_tool_instance
    assert tool.name == "SaveToRag"
    assert "Persist text so it can be retrieved later via the RAG tool." in tool.description
    assert tool.args_schema == SaveToRagInput


@patch("epic_news.tools.save_to_rag_tool.DEFAULT_RAG_CONFIG", MOCK_DEFAULT_RAG_CONFIG)
@patch("epic_news.tools.save_to_rag_tool.RagTool")
def test_save_to_rag_tool_instantiation_without_rag_tool(mock_rag_tool_class):
    """Test tool instantiation when no RagTool instance is provided,
    so it creates its own."""
    mock_rag_instance = mock_rag_tool_class.return_value  # The instance RagTool() would return
    mock_rag_instance.add = MagicMock()

    tool = SaveToRagTool()

    mock_rag_tool_class.assert_called_once_with(config=MOCK_DEFAULT_RAG_CONFIG, summarize=True)
    assert tool._rag_tool == mock_rag_instance
    assert tool.name == "SaveToRag"


def test_save_to_rag_tool_run_success(mock_rag_tool_instance):
    """Test the _run method for successful operation."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    test_text = "This is a test document to save."

    result_json = tool._run(text=test_text)
    result = json.loads(result_json)

    # Assert that the rag_tool's add method was called correctly
    mock_rag_tool_instance.add.assert_called_once_with(source=test_text, data_type="text")

    # Assert the expected JSON output
    assert result == {"status": "success", "message": "stored"}


def test_save_to_rag_tool_run_with_empty_text(mock_rag_tool_instance):
    """Test the _run method with empty text."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    test_text = ""

    result_json = tool._run(text=test_text)
    result = json.loads(result_json)

    mock_rag_tool_instance.add.assert_called_once_with(source=test_text, data_type="text")
    assert result == {"status": "success", "message": "stored"}
