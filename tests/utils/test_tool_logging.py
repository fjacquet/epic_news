
from unittest.mock import patch
from epic_news.utils.tool_logging import configure_tool_logging, get_quiet_tools_config, apply_tool_silence

def test_configure_tool_logging(mocker):
    # Test that configure_tool_logging configures the tool loggers correctly
    mock_logger = mocker.patch('logging.getLogger')
    configure_tool_logging(mute_tools=True)
    mock_logger.assert_called()
    mock_logger.return_value.setLevel.assert_called_with(40)

def test_get_quiet_tools_config(mocker):
    # Test that get_quiet_tools_config returns the correct configuration
    mocker.patch('os.getenv', return_value="true")
    config = get_quiet_tools_config()
    assert config["verbose"]
    assert config["mute_requests"]
    assert config["mute_search"]

def test_apply_tool_silence(mocker):
    # Test that apply_tool_silence applies the tool silencing configuration
    mock_configure_tool_logging = mocker.patch('epic_news.utils.tool_logging.configure_tool_logging')
    mocker.patch('os.getenv', return_value="false")
    apply_tool_silence()
    mock_configure_tool_logging.assert_called_once_with(mute_tools=True, log_level='ERROR')
