from pydantic import BaseModel, Field


class AccuWeatherToolInput(BaseModel):
    """Input schema for the AccuWeatherTool."""

    location: str = Field(..., description="The city name to get the current weather for (e.g., 'London').")
