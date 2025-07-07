
from unittest.mock import mock_open, patch

from loguru import logger
from pydantic import BaseModel

from epic_news.utils.debug_utils import (
    analyze_crewai_output,
    dump_crewai_state,
    log_state_keys,
    parse_crewai_output,
)


class SampleModel(BaseModel):
    name: str
    value: int

def test_dump_crewai_state(caplog):
    """Test the dump_crewai_state function."""
    logger.add(caplog.handler, format="{message}")
    state_data = {"key": "value"}
    with patch("builtins.open", mock_open()) as mock_file, \
         patch("os.environ.get", return_value="true"), \
         patch("epic_news.utils.directory_utils.ensure_output_directory"):
        dump_crewai_state(state_data, "test_crew")
        # The exact filename is timestamped, so we check for a call rather than the exact filename
        mock_file.assert_called()
        assert "CrewAI state dumped to" in caplog.text


def test_log_state_keys(caplog):
    """Test the log_state_keys function."""
    logger.add(caplog.handler, format="{message}")
    state_data = {"key1": "value1", "key2": "value2"}
    log_state_keys(state_data)
    assert "State data keys: ['key1', 'key2']" in caplog.text

def test_analyze_crewai_output(caplog):
    """Test the analyze_crewai_output function."""
    logger.add(caplog.handler, format="{message}")
    state_data = {"raw": "some raw data", "pydantic": SampleModel(name="test", value=1)}
    analyze_crewai_output(state_data, "test_crew")
    assert "CrewAI Analysis for test_crew" in caplog.text

def test_parse_crewai_output():
    """Test the parse_crewai_output function."""
    # Test with raw JSON string
    raw_output = '{"name": "test", "value": 1}'
    crew_output = type("CrewOutput", (), {"raw": raw_output})()
    parsed = parse_crewai_output(crew_output, SampleModel, {})
    assert parsed.name == "test"
    assert parsed.value == 1

    # Test with Pydantic model
    pydantic_output = SampleModel(name="test2", value=2)
    crew_output = type("CrewOutput", (), {"output": pydantic_output})()
    parsed = parse_crewai_output(crew_output, SampleModel, {})
    assert parsed.name == "test2"
    assert parsed.value == 2
