import json

import pytest
from crewai_tools import RagTool  # For type hinting and potentially mocking its instantiation

from epic_news.tools.save_to_rag_tool import SaveToRagInput, SaveToRagTool


@pytest.fixture
def mock_rag_tool_instance(mocker):
    """Fixture to create a MagicMock instance of RagTool."""
    mock_rag = mocker.MagicMock(spec=RagTool)
    mock_rag.add = mocker.MagicMock()  # Mock the 'add' method specifically
    return mock_rag


def test_save_to_rag_tool_instantiation_with_rag_tool(mock_rag_tool_instance):
    """Test tool instantiation when a RagTool instance is provided."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    assert tool._rag_tool == mock_rag_tool_instance
    assert tool.name == "SaveToRag"
    assert "Persist text so it can be retrieved later via the RAG tool." in tool.description
    assert tool.args_schema == SaveToRagInput


def test_save_to_rag_tool_instantiation_without_rag_tool(mocker):
    """When no RagTool is provided, SaveToRagTool builds one from build_rag_tool_kwargs."""
    mock_kwargs = {"config": {"vectordb": {"provider": "chromadb", "config": {}}}, "collection_name": "stub"}
    mock_build = mocker.patch(
        "epic_news.tools.save_to_rag_tool.build_rag_tool_kwargs",
        return_value=mock_kwargs,
    )
    mock_rag_tool_class = mocker.patch("epic_news.tools.save_to_rag_tool.RagTool")
    mock_rag_instance = mock_rag_tool_class.return_value
    mock_rag_instance.add = mocker.MagicMock()

    tool = SaveToRagTool()

    mock_build.assert_called_once_with()
    mock_rag_tool_class.assert_called_once_with(**mock_kwargs, summarize=True)
    assert tool._rag_tool == mock_rag_instance
    assert tool.name == "SaveToRag"


def test_save_to_rag_tool_run_success(mock_rag_tool_instance):
    """Test the _run method for successful operation."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    test_text = "This is a test document to save."

    result_json = tool._run(text=test_text)
    result = json.loads(result_json)

    # crewai-tools 1.x: ``add()`` takes the source positionally.
    mock_rag_tool_instance.add.assert_called_once_with(test_text, data_type="text")

    # Assert the expected JSON output
    assert result == {"status": "success", "message": "stored"}


def test_save_to_rag_tool_run_with_empty_text(mock_rag_tool_instance):
    """Test the _run method with empty text."""
    tool = SaveToRagTool(rag_tool=mock_rag_tool_instance)
    test_text = ""

    result_json = tool._run(text=test_text)
    result = json.loads(result_json)

    mock_rag_tool_instance.add.assert_called_once_with(test_text, data_type="text")
    assert result == {"status": "success", "message": "stored"}
