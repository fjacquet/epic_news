"""
Tests for the GeoapifyPlacesTool.

These tests use mocking to avoid making real API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from epic_news.tools.geoapify_places_tool import GeoapifyPlacesInput, GeoapifyPlacesTool

# Sample API response for testing
SAMPLE_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Test Restaurant",
                "categories": ["catering.restaurant"],
                "distance": 123.45,
            },
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
        }
    ],
}


class TestGeoapifyPlacesInput:
    """Test the input validation for GeoapifyPlacesInput."""

    def test_valid_circle_filter(self):
        """Test valid circle filter input."""
        input_data = {
            "filter_type": "circle",
            "filter_value": "-0.1,51.5,1000",  # lon,lat,radiusM
            "limit": 5,
        }
        result = GeoapifyPlacesInput(**input_data)
        assert result.filter_type == "circle"
        assert result.filter_value == "-0.1,51.5,1000"

    def test_valid_rect_filter(self):
        """Test valid rectangle filter input."""
        input_data = {
            "filter_type": "rect",
            "filter_value": "-0.2,51.4,-0.1,51.5",  # lon1,lat1,lon2,lat2
            "limit": 5,
        }
        result = GeoapifyPlacesInput(**input_data)
        assert result.filter_type == "rect"
        assert result.filter_value == "-0.2,51.4,-0.1,51.5"

    def test_valid_bias(self):
        """Test valid bias input."""
        input_data = {"bias": "-0.1,51.5", "limit": 5}
        result = GeoapifyPlacesInput(**input_data)
        assert result.bias == "-0.1,51.5"

    def test_invalid_bias_format(self):
        """Test invalid bias format."""
        with pytest.raises(ValueError, match="Bias must be in format 'lon,lat'"):
            GeoapifyPlacesInput(bias="invalid", limit=5)

    def test_invalid_circle_filter(self):
        """Test invalid circle filter format."""
        with pytest.raises(ValueError, match="Circle filter requires lon,lat,radiusM"):
            GeoapifyPlacesInput(
                filter_type="circle",
                filter_value="-0.1,51.5",  # Missing radius
                limit=5,
            )


class TestGeoapifyPlacesTool:
    """Test the GeoapifyPlacesTool functionality with mocked API calls."""

    @pytest.fixture
    def mock_env_geoapify_key(self, monkeypatch):
        """Set up the GEOAPIFY_API_KEY environment variable for testing."""
        monkeypatch.setenv("GEOAPIFY_API_KEY", "test_api_key_123")

    @pytest.fixture
    def mock_successful_response(self):
        """Create a mock successful API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = SAMPLE_RESPONSE
        return mock_response

    @pytest.fixture
    def mock_error_response(self):
        """Create a mock error API response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid parameters"}
        mock_response.raise_for_status.side_effect = Exception("API Error")
        return mock_response

    def test_search_with_circle_filter(self, mock_env_geoapify_key, mock_successful_response):
        """Test search with circle filter."""
        with patch("requests.get", return_value=mock_successful_response) as mock_get:
            tool = GeoapifyPlacesTool()
            result = tool._run(
                categories=["catering.restaurant"],
                filter_type="circle",
                filter_value="-0.1,51.5,1000",  # lon,lat,radiusM
                limit=5,
            )

            # Verify the result
            assert "Test Restaurant" in result

            # Verify the API call was made with correct parameters
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://api.geoapify.com/v2/places"
            assert kwargs["params"]["apiKey"] == "test_api_key_123"
            assert kwargs["params"]["categories"] == "catering.restaurant"
            assert kwargs["params"]["filter"] == "circle:-0.1,51.5,1000"
            assert kwargs["params"]["limit"] == 5
            assert kwargs["params"]["lang"] == "en"

    def test_search_with_bias(self, mock_env_geoapify_key, mock_successful_response):
        """Test search with proximity bias."""
        with patch("requests.get", return_value=mock_successful_response) as mock_get:
            tool = GeoapifyPlacesTool()
            tool._run(categories=["commercial.supermarket"], bias="-0.1,51.5", limit=3)

            # Verify the API call was made with bias parameter
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://api.geoapify.com/v2/places"
            assert kwargs["params"]["apiKey"] == "test_api_key_123"
            assert kwargs["params"]["categories"] == "commercial.supermarket"
            assert kwargs["params"]["bias"] == "proximity:-0.1,51.5"
            assert kwargs["params"]["limit"] == 3
            assert kwargs["params"]["lang"] == "en"

    def test_search_with_conditions(self, mock_env_geoapify_key, mock_successful_response):
        """Test search with conditions."""
        with patch("requests.get", return_value=mock_successful_response) as mock_get:
            tool = GeoapifyPlacesTool()
            tool._run(categories=["catering.restaurant"], conditions=["vegetarian", "wheelchair"], limit=5)

            # Verify the API call was made with conditions
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://api.geoapify.com/v2/places"
            assert kwargs["params"]["apiKey"] == "test_api_key_123"
            assert kwargs["params"]["categories"] == "catering.restaurant"
            assert kwargs["params"]["conditions"] == "vegetarian,wheelchair"
            assert kwargs["params"]["limit"] == 5
            assert kwargs["params"]["lang"] == "en"

    def test_missing_api_key(self, monkeypatch):
        """Test behavior when API key is missing."""
        # Remove the API key from environment
        monkeypatch.delenv("GEOAPIFY_API_KEY", raising=False)

        tool = GeoapifyPlacesTool()
        result = tool._run(categories=["catering.restaurant"], limit=1)

        assert "GEOAPIFY_API_KEY environment variable not set" in result

    def test_api_error_handling(self, mock_env_geoapify_key, mock_error_response):
        """Test error handling for API errors."""
        with patch("requests.get", return_value=mock_error_response) as mock_get:
            tool = GeoapifyPlacesTool()
            with pytest.raises(Exception) as exc_info:
                tool._run(categories=["catering.restaurant"], limit=1)

            # Verify the exception was raised
            assert "API Error" in str(exc_info.value)

            # Verify the API was called with correct parameters
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://api.geoapify.com/v2/places"
            assert kwargs["params"]["apiKey"] == "test_api_key_123"
            assert kwargs["params"]["categories"] == "catering.restaurant"
            assert kwargs["params"]["limit"] == 1
            assert kwargs["params"]["lang"] == "en"

    def test_invalid_parameters(self, mock_env_geoapify_key):
        """Test validation of input parameters."""
        tool = GeoapifyPlacesTool()

        # Test with invalid language code (too long)
        result = tool._run(lang="eng")  # Lang must be exactly 2 chars
        result_json = json.loads(result)
        assert "error" in result_json
        assert "validation error" in result_json["error"]
        assert "lang" in result_json["error"]

        # Test with invalid bias format
        result = tool._run(bias="invalid")
        result_json = json.loads(result)
        assert "error" in result_json
        assert "validation error" in result_json["error"]
        assert "Bias must be in format" in result_json["error"]

        # Test with invalid filter type
        result = tool._run(filter_type="invalid_type")
        result_json = json.loads(result)
        assert "error" in result_json
        assert "validation error" in result_json["error"]
        assert "filter_type" in result_json["error"]

    def test_missing_filter_value(self, mock_env_geoapify_key):
        """Test validation when filter_type is provided but filter_value is missing."""
        # We need to directly test the validation in the GeoapifyPlacesInput class
        # since the tool's _run method might be trying to make an API call
        # before validation errors are caught

        # Create a tool instance
        tool = GeoapifyPlacesTool()

        # Test the validation directly
        try:
            # This should fail validation in the field_validator
            GeoapifyPlacesInput(filter_type="circle")
            pytest.fail("Expected validation to fail but it passed")
        except ValidationError as e:
            # Validation should fail with a message about filter_value
            error_msg = str(e)
            assert "filter_value" in error_msg

        # Now test through the tool's _run method
        result = tool._run(filter_type="circle")
        result_json = json.loads(result)

        # Check that we got an error
        assert "error" in result_json
        # The error might be about validation or API, but it should be an error
