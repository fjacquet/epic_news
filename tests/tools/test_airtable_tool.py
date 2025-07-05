import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.epic_news.tools.airtable_tool import AirtableReaderTool, AirtableTool


@pytest.fixture
def tool():
    """Fixture to provide an AirtableTool instance."""
    return AirtableTool()


def test_airtable_create_record_success(tool, mocker):
    """Test a successful record creation with the AirtableTool."""
    mocker.patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
    mock_table = mocker.patch("src.epic_news.tools.airtable_tool.Table")
    mock_instance = mocker.MagicMock()
    mock_instance.create.return_value = {"id": "rec12345"}
    mock_table.return_value = mock_instance

    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})

    assert result == "Successfully created record in Airtable: rec12345"
    mock_table.assert_called_once_with("fake_api_token", "app123", "Test Table")
    mock_instance.create.assert_called_once_with({"Name": "Test Record"})


def test_airtable_create_record_missing_api_key(tool, mocker):
    """Test that the tool handles a missing API key gracefully."""
    mocker.patch.dict(os.environ, {}, clear=True)
    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})
    assert "AIRTABLE_API_KEY environment variable not set" in str(result)


def test_airtable_create_record_api_error(tool, mocker):
    """Test that the tool handles an API error gracefully."""
    mocker.patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
    mock_table = mocker.patch("src.epic_news.tools.airtable_tool.Table")
    mock_instance = mocker.MagicMock()
    mock_instance.create.side_effect = Exception("API Error")
    mock_table.return_value = mock_instance

    result = tool._run(base_id="app123", table_name="Test Table", data={"Name": "Test Record"})

    assert "Error creating record in Airtable: API Error" in str(result)


@pytest.fixture
def reader_tool():
    """Fixture to provide an AirtableReaderTool instance."""
    return AirtableReaderTool()


def test_airtable_read_records_success(reader_tool, mocker):
    """Test a successful record read with the AirtableReaderTool."""
    mocker.patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
    mock_table = mocker.patch("src.epic_news.tools.airtable_tool.Table")
    mock_instance = mocker.MagicMock()
    mock_instance.all.return_value = [{"id": "rec123", "fields": {"Name": "Test"}}]
    mock_table.return_value = mock_instance

    result = reader_tool._run(base_id="app123", table_name="Test Table")

    assert result == json.dumps([{"id": "rec123", "fields": {"Name": "Test"}}])
    mock_table.assert_called_once_with("fake_api_token", "app123", "Test Table")
    mock_instance.all.assert_called_once()


def test_airtable_read_records_missing_api_key(reader_tool, mocker):
    """Test that the reader tool handles a missing API key gracefully."""
    mocker.patch.dict(os.environ, {}, clear=True)
    result = reader_tool._run(base_id="app123", table_name="Test Table")
    assert "AIRTABLE_API_KEY environment variable not set" in str(result)


def test_airtable_read_records_api_error(reader_tool, mocker):
    """Test that the tool handles an API error gracefully."""
    mocker.patch.dict(os.environ, {"AIRTABLE_API_KEY": "fake_api_token"})
    mock_table = mocker.patch("src.epic_news.tools.airtable_tool.Table")
    mock_instance = mocker.MagicMock()
    mock_instance.all.side_effect = Exception("API Error")
    mock_table.return_value = mock_instance

    result = reader_tool._run(base_id="app123", table_name="Test Table")

    assert "Error reading records from Airtable: API Error" in str(result)
