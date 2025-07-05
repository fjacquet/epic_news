
import json
import logging
from unittest.mock import MagicMock
from faker import Faker
from epic_news.utils.debug_utils import dump_crewai_state, make_serializable, log_state_keys, analyze_crewai_output, parse_crewai_output
from pydantic import BaseModel
from loguru import logger

fake = Faker()

class MockModel(BaseModel):
    name: str
    value: int

def test_dump_crewai_state(tmp_path, mocker):
    # Test that dump_crewai_state dumps the state to a JSON file
    mocker.patch('os.environ.get', return_value="true")
    state_data = {"test_key": "test_value"}
    debug_file = dump_crewai_state(state_data, "test_crew", debug_dir=tmp_path)
    assert debug_file.endswith(".json")
    with open(debug_file, "r") as f:
        assert json.load(f) == state_data

def test_make_serializable():
    # Test that make_serializable converts an object to a JSON-serializable format
    obj = MockModel(name="test", value=1)
    serializable_obj = make_serializable(obj)
    assert serializable_obj == {"name": "test", "value": 1}

def test_log_state_keys(caplog):
    # Test that log_state_keys logs the state data keys
    state_data = {"test_key": "test_value"}
    with caplog.at_level(logging.INFO):
        log_state_keys(state_data)
    assert "test_key" in caplog.text

def test_analyze_crewai_output(caplog):
    # Test that analyze_crewai_output analyzes the CrewAI output structure
    state_data = {"task_outputs": {"raw": "test_output"}}
    with caplog.at_level(logging.INFO):
        analyze_crewai_output(state_data, "test_crew")
    assert "CrewAI Analysis" in caplog.text

def test_parse_crewai_output():
    # Test that parse_crewai_output parses the CrewAI output to a Pydantic model
    class MockReport(BaseModel):
        title: str
        content: str
    
    report_content = MagicMock()
    report_content.raw = '{"title": "Test Title", "content": "Test Content"}'
    parsed_output = parse_crewai_output(report_content, MockReport)
    assert parsed_output.title == "Test Title"
    assert parsed_output.content == "Test Content"
