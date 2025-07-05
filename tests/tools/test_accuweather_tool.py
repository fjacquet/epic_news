import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.epic_news.tools.accuweather_tool import AccuWeatherTool


@pytest.fixture
def tool():
    """Fixture to provide an AccuWeatherTool instance."""
    return AccuWeatherTool()


@pytest.mark.parametrize("api_key_present", [True, False])
def test_get_current_weather_success(api_key_present, tool, mocker):
    """Test a successful weather retrieval with the AccuWeatherTool."""
    if api_key_present:
        mocker.patch.dict(os.environ, {"ACCUWEATHER_API_KEY": "fake_api_token"})
    else:
        mocker.patch.dict(os.environ, {}, clear=True)

    mock_get = mocker.patch("src.epic_news.tools.accuweather_tool.requests.get")

    if not api_key_present:
        result = tool._run(location="Test City")
        assert "ACCUWEATHER_API_KEY environment variable not set" in str(result)
        return

    # Mock response for location key
    mock_location_response = mocker.MagicMock()
    mock_location_response.json.return_value = [{"Key": "12345"}]
    mock_location_response.raise_for_status.return_value = None

    # Mock response for current conditions
    mock_weather_response = mocker.MagicMock()
    mock_weather_response.json.return_value = [
        {"Temperature": {"Metric": {"Value": 20, "Unit": "C"}}, "WeatherText": "Sunny"}
    ]
    mock_weather_response.raise_for_status.return_value = None

    mock_get.side_effect = [mock_location_response, mock_weather_response]

    result = tool._run(location="Test City")

    assert result == "Current weather in your location: 20°C, Sunny."
    assert mock_get.call_count == 2


def test_get_current_weather_missing_api_key(tool, mocker):
    """Test that the tool handles a missing API key gracefully."""
    mocker.patch.dict(os.environ, {}, clear=True)
    result = tool._run(location="Test City")
    assert "ACCUWEATHER_API_KEY environment variable not set" in str(result)


def test_get_current_weather_location_not_found(tool, mocker):
    """Test that the tool handles a location not found error."""
    mocker.patch.dict(os.environ, {"ACCUWEATHER_API_KEY": "fake_api_token"})
    mock_get = mocker.patch("src.epic_news.tools.accuweather_tool.requests.get")
    mock_location_response = mocker.MagicMock()
    mock_location_response.json.return_value = []
    mock_location_response.raise_for_status.return_value = None
    mock_get.return_value = mock_location_response

    result = tool._run(location="Invalid City")

    assert "Location 'Invalid City' not found" in str(result)
