import os

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel

from src.epic_news.models.accuweather_models import AccuWeatherToolInput


class AccuWeatherTool(BaseTool):
    name: str = "get_current_weather"
    description: str = "A tool to get the current weather conditions for a specific location."
    args_schema: type[BaseModel] = AccuWeatherToolInput
    _base_url: str = "http://dataservice.accuweather.com"

    def _run(self, location: str) -> str:
        """Run the AccuWeather tool to get current weather conditions."""
        try:
            api_key = os.getenv('ACCUWEATHER_API_KEY')
            if not api_key:
                raise ValueError("ACCUWEATHER_API_KEY environment variable not set.")

            # Step 1: Get location key from location name
            location_key = self._get_location_key(location, api_key)

            # Step 2: Get current conditions using the location key
            return self._get_current_conditions(location_key, api_key)

        except Exception as e:
            return f"Error getting weather from AccuWeather: {e}"

    def _get_location_key(self, location: str, api_key: str) -> str:
        """Get the location key for a given location name."""
        url = f"{self._base_url}/locations/v1/cities/autocomplete"
        params = {"apikey": api_key, "q": location}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Location '{location}' not found.")
        return data[0]['Key']

    def _get_current_conditions(self, location_key: str, api_key: str) -> str:
        """Get the current weather conditions for a given location key."""
        url = f"{self._base_url}/currentconditions/v1/{location_key}"
        params = {"apikey": api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            return "Could not retrieve weather data."

        weather_info = data[0]
        temp = weather_info['Temperature']['Metric']['Value']
        unit = weather_info['Temperature']['Metric']['Unit']
        weather_text = weather_info['WeatherText']
        return f"Current weather in your location: {temp}°{unit}, {weather_text}."
