import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import json

from src.epic_news.tools.airtable_tool import AirtableReaderTool, AirtableTool


@pytest.fixture
def tool():
    """Fixture to provide an AirtableTool instance."""
    return AirtableTool()


@patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
@patch("src.epic_news.tools.airtable_tool.Table")
def test_airtable_create_record_success(mock_table, tool):
    """Test a successful record creation with the AirtableTool."""
    mock_instance = MagicMock()
    mock_instance.create.return_value = {"id": "rec12345"}
    mock_table.return_value = mock_instance

    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})

    assert result == "Successfully created record in Airtable: rec12345"
    mock_table.assert_called_once_with("fake_api_token", "app123", "Test Table")
    mock_instance.create.assert_called_once_with({"Name": "Test Record"})


@patch.dict(os.environ, {}, clear=True)
def test_airtable_create_record_missing_api_key(tool):
    """Test that the tool handles a missing API key gracefully."""
    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})
    assert "AIRTABLE_API_KEY environment variable not set" in str(result)


@patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
@patch("src.epic_news.tools.airtable_tool.Table")
def test_airtable_create_record_api_error(mock_table, tool):
    """Test that the tool handles an API error gracefully."""
    mock_instance = MagicMock()
    mock_instance.create.side_effect = Exception("API Error")
    mock_table.return_value = mock_instance

    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})

    assert "Error creating record in Airtable: API Error" in str(result)


@pytest.fixture
def reader_tool():
    """Fixture to provide an AirtableReaderTool instance."""
    return AirtableReaderTool()


@patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
@patch("src.epic_news.tools.airtable_tool.Table")
def test_airtable_read_records_success(mock_table, reader_tool):
    """Test a successful record read with the AirtableReaderTool."""
    mock_instance = MagicMock()
    mock_instance.all.return_value = [{"id": "rec123", "fields": {"Name": "Test"}}]
    mock_table.return_value = mock_instance

    result = reader_tool._run(base_id="app123", table_name="Test Table")

    assert result == json.dumps([{"id": "rec123", "fields": {"Name": "Test"}}])
    mock_table.assert_called_once_with("fake_api_token", "app123", "Test Table")
    mock_instance.all.assert_called_once()


@patch.dict(os.environ, {}, clear=True)
def test_airtable_read_records_missing_api_key(reader_tool):
    """Test that the reader tool handles a missing API key gracefully."""
    result = reader_tool._run(base_id="app123", table_name="Test Table")
    assert "AIRTABLE_API_KEY environment variable not set" in str(result)


@patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
@patch("src.epic_news.tools.airtable_tool.Table")
def test_airtable_read_records_api_error(mock_table, reader_tool):
    """Test that the tool handles an API error gracefully."""
    mock_instance = MagicMock()
    mock_instance.all.side_effect = Exception("API Error")
    mock_table.return_value = mock_instance

    result = reader_tool._run(base_id="app123", table_name="Test Table")

    assert "Error reading records from Airtable: API Error" in str(result)
