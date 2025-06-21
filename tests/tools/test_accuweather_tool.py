import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.epic_news.tools.accuweather_tool import AccuWeatherTool


@pytest.fixture
def tool():
    """Fixture to provide an AccuWeatherTool instance."""
    return AccuWeatherTool()

@patch.dict(os.environ, {"ACCUWEATHER_API_KEY": "fake_api_token"})
@patch('src.epic_news.tools.accuweather_tool.requests.get')
def test_get_current_weather_success(mock_get, tool):
    """Test a successful weather retrieval with the AccuWeatherTool."""
    # Mock response for location key
    mock_location_response = MagicMock()
    mock_location_response.json.return_value = [{'Key': '12345'}]
    mock_location_response.raise_for_status.return_value = None

    # Mock response for current conditions
    mock_weather_response = MagicMock()
    mock_weather_response.json.return_value = [{
        'Temperature': {'Metric': {'Value': 20, 'Unit': 'C'}},
        'WeatherText': 'Sunny'
    }]
    mock_weather_response.raise_for_status.return_value = None

    mock_get.side_effect = [mock_location_response, mock_weather_response]

    result = tool._run(location="Test City")

    assert result == "Current weather in your location: 20°C, Sunny."
    assert mock_get.call_count == 2

@patch.dict(os.environ, {}, clear=True)
def test_get_current_weather_missing_api_key(tool):
    """Test that the tool handles a missing API key gracefully."""
    result = tool._run(location="Test City")
    assert "ACCUWEATHER_API_KEY environment variable not set" in str(result)

@patch.dict(os.environ, {"ACCUWEATHER_API_KEY": "fake_api_token"})
@patch('src.epic_news.tools.accuweather_tool.requests.get')
def test_get_current_weather_location_not_found(mock_get, tool):
    """Test that the tool handles a location not found error."""
    mock_location_response = MagicMock()
    mock_location_response.json.return_value = []
    mock_location_response.raise_for_status.return_value = None
    mock_get.return_value = mock_location_response

    result = tool._run(location="Invalid City")

    assert "Location 'Invalid City' not found" in str(result)
