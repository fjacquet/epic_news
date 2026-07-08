"""
Factory functions for location-based tools.

This module provides factory functions that return collections of tools
for location-based searches and operations.
"""

from crewai.tools import BaseTool
from crewai_custom_tools import GeoapifyPlacesTool


def get_location_tools() -> list[BaseTool]:
    """
    Return a collection of tools for location-based searches and operations.

    Returns:
        List[BaseTool]: A list of location-related tools
    """
    return [
        GeoapifyPlacesTool(),
        # Other location-related tools can be added here as needed
    ]
