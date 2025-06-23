"""
Geoapify Places API tool for searching points of interest.

This tool provides access to the Geoapify Places API, allowing searches for
points of interest by categories, conditions, and location filters.
"""

import json
import os
from enum import Enum

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GeoapifyPlacesInput(BaseModel):
    """Input schema for Geoapify Places search."""

    model_config = ConfigDict(extra="forbid")

    class FilterType(str, Enum):
        CIRCLE = "circle"  # lon,lat,radiusM
        RECT = "rect"  # lon1,lat1,lon2,lat2
        PLACE = "place"  # place ID
        GEOMETRY = "geometry"  # geometry ID

    categories: list[str] | None = Field(
        None,
        description=(
            "List of category IDs to search for "
            "(e.g., ['catering.restaurant', 'commercial.supermarket']). "
            "See https://apidocs.geoapify.com/docs/places/ for full list."
        ),
    )
    conditions: list[str] | None = Field(
        None,
        description=(
            "List of conditions to filter results "
            "(e.g., ['vegetarian', 'wheelchair']). "
            "See API docs for available conditions per category."
        ),
    )
    filter_type: FilterType | None = Field(
        None,
        description=(
            "Type of filter to apply. Options: 'circle' (lon,lat,radiusM), "
            "'rect' (lon1,lat1,lon2,lat2), 'place' (place ID), 'geometry' (geometry ID)"
        ),
    )
    filter_value: str | None = Field(
        None,
        description=(
            "Filter values as comma-separated string based on filter_type. "
            "Example for circle: '-0.0707,51.5085,1000' (lon,lat,radiusM)"
        ),
    )
    bias: str | None = Field(
        None,
        description=(
            "Bias results by proximity to a point as 'lon,lat'. "
            "Results will be sorted by distance from this point."
        ),
    )
    limit: int = Field(20, description="Maximum number of results to return (1-100)", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    lang: str = Field("en", description="Language code (ISO 639-1) for results", min_length=2, max_length=2)

    @field_validator("bias")
    def validate_bias(cls, v):  # noqa: N805
        if v is not None:
            try:
                lon, lat = map(float, v.split(","))
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    raise ValueError("Longitude must be between -180 and 180, latitude between -90 and 90")
            except (ValueError, AttributeError) as e:
                raise ValueError("Bias must be in format 'lon,lat' with valid coordinates") from e
        return v

    @field_validator("filter_value")
    def validate_filter_value(cls, v, info):  # noqa: N805
        values = info.data
        if "filter_type" not in values or values.get("filter_type") is None:
            if v is not None:
                raise ValueError("filter_value requires filter_type to be specified")
            return v

        if v is None:
            raise ValueError(f"filter_value is required when filter_type is {values['filter_type']}")

        try:
            if values["filter_type"] == "circle":
                parts = v.split(",")
                if len(parts) != 3:
                    raise ValueError("Circle filter requires lon,lat,radiusM")
                lon, lat, radius = map(float, parts)
                if not (-180 <= lon <= 180 and -90 <= lat <= 90 and radius > 0):
                    raise ValueError("Invalid circle parameters")

            elif values["filter_type"] == "rect":
                parts = v.split(",")
                if len(parts) != 4:
                    raise ValueError("Rect filter requires lon1,lat1,lon2,lat2")
                lon1, lat1, lon2, lat2 = map(float, parts)
                if not (
                    -180 <= lon1 <= 180 and -90 <= lat1 <= 90 and -180 <= lon2 <= 180 and -90 <= lat2 <= 90
                ):
                    raise ValueError("Invalid rectangle coordinates")

        except ValueError as e:
            raise ValueError(f"Invalid filter_value for {values['filter_type']}: {str(e)}") from e

        return v

    @model_validator(mode="after")
    def validate_filter_dependencies(self):
        """Ensure filter_value is provided when filter_type is set."""
        if self.filter_type is not None and self.filter_value is None:
            raise ValueError(f"filter_value is required when filter_type is {self.filter_type}")
        return self


class GeoapifyPlacesTool(BaseTool):
    """
    Tool for searching points of interest using the Geoapify Places API.

    This tool allows searching for places by categories, conditions, and location.
    It requires a Geoapify API key set in the environment as GEOAPIFY_API_KEY.
    """

    name: str = "geoapify_places_search"
    description: str = (
        "Search for points of interest using the Geoapify Places API. "
        "Supports searching by categories, conditions, and location filters. "
        "Useful for finding restaurants, attractions, and other POIs."
    )
    args_schema: type[BaseModel] = GeoapifyPlacesInput

    def _run(self, **kwargs) -> str:
        """
        Execute the Geoapify Places search with the provided parameters.

        Args:
            **kwargs: Arguments matching GeoapifyPlacesInput schema

        Returns:
            str: JSON string containing the search results or error message

        Raises:
            ValueError: If required parameters are missing or invalid
            requests.exceptions.RequestException: For API request failures
        """
        # Validate input using Pydantic model
        try:
            params = GeoapifyPlacesInput(**kwargs)
        except Exception as e:
            return json.dumps({"error": f"Invalid parameters: {str(e)}"})

        # Get API key from environment
        api_key = os.getenv("GEOAPIFY_API_KEY")
        if not api_key:
            return json.dumps({"error": "GEOAPIFY_API_KEY environment variable not set"})

        # Build query parameters
        query_params = {"apiKey": api_key, "limit": params.limit, "lang": params.lang}

        # Add categories if provided
        if params.categories:
            query_params["categories"] = ",".join(params.categories)

        # Add conditions if provided
        if params.conditions:
            query_params["conditions"] = ",".join(params.conditions)

        # Add filter if provided
        if params.filter_type and params.filter_value:
            query_params["filter"] = f"{params.filter_type.value}:{params.filter_value}"

        # Add bias if provided
        if params.bias:
            query_params["bias"] = f"proximity:{params.bias}"

        # Add offset for pagination
        if params.offset > 0:
            query_params["offset"] = params.offset

        # Make the API request
        try:
            response = requests.get(
                "https://api.geoapify.com/v2/places",
                params=query_params,
                timeout=30,  # 30 seconds timeout
            )
            response.raise_for_status()  # Raise HTTPError for bad responses

            # Parse and validate response
            result = response.json()

            # Check for API errors
            if "error" in result:
                return json.dumps(
                    {
                        "error": f"Geoapify API error: {result.get('message', 'Unknown error')}",
                        "status_code": response.status_code,
                    }
                )

            # Return the GeoJSON FeatureCollection
            return json.dumps(result, ensure_ascii=False)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request to Geoapify API failed: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = f"{error_msg} - {error_data.get('message', 'No error details')}"
                except ValueError:
                    error_msg = f"{error_msg} - Status: {e.response.status_code}"
            return json.dumps({"error": error_msg})
