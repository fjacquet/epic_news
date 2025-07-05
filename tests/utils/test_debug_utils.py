
import json
from loguru import logger
import unittest
from unittest.mock import patch, mock_open

from pydantic import BaseModel

from epic_news.utils.debug_utils import (
    dump_crewai_state,
    log_state_keys,
    analyze_crewai_output,
    parse_crewai_output,
)

# Configure logging
# logging.basicConfig(level=logging.INFO)


class SampleModel(BaseModel):
    name: str
    value: int


class TestDebugUtils(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("epic_news.utils.debug_utils.logger")
    def test_dump_crewai_state(self, mock_logger, mock_file):
        """
        Test the dump_crewai_state function.
        """
        state_data = {"key": "value"}
        dump_crewai_state(state_data, "test_crew")
        mock_file.assert_called_once_with(
            "output/debug/test_crew_state_dump.json", "w", encoding="utf-8"
        )
        mock_logger.info.assert_called_with(
            "✅ CrewAI state for 'test_crew' dumped to output/debug/test_crew_state_dump.json"
        )

    @patch("epic_news.utils.debug_utils.logger")
    def test_log_state_keys(self, mock_logger):
        """
        Test the log_state_keys function.
        """
        state_data = {"key1": "value1", "key2": "value2"}
        log_state_keys(state_data)
        mock_logger.info.assert_any_call("All state keys: ['key1', 'key2']")

    @patch("epic_news.utils.debug_utils.logger")
    def test_analyze_crewai_output(self, mock_logger):
        """
        Test the analyze_crewai_output function.
        """
        state_data = {"raw": "some raw data", "pydantic": SampleModel(name="test", value=1)}
        analyze_crewai_output(state_data, "test_crew")
        mock_logger.info.assert_any_call("Found 'raw' output. Length: 13")
        mock_logger.info.assert_any_call("Found 'pydantic' object. Type: <class '__main__.SampleModel'>")

    def test_parse_crewai_output(self):
        """
        Test the parse_crewai_output function.
        """
        # Test with raw JSON string
        raw_output = '{"name": "test", "value": 1}'
        crew_output = type("CrewOutput", (), {"raw": raw_output})()
        parsed = parse_crewai_output(crew_output, SampleModel, {})
        self.assertEqual(parsed.name, "test")
        self.assertEqual(parsed.value, 1)

        # Test with Pydantic model
        pydantic_output = SampleModel(name="test2", value=2)
        crew_output = type("CrewOutput", (), {"pydantic": pydantic_output})()
        parsed = parse_crewai_output(crew_output, SampleModel, {})
        self.assertEqual(parsed.name, "test2")
        self.assertEqual(parsed.value, 2)


if __name__ == "__main__":
    unittest.main()
