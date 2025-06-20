"""
Tests for location tools factory functions.
"""

import pytest
from epic_news.tools.location_tools import get_location_tools
from epic_news.tools.geoapify_places_tool import GeoapifyPlacesTool

def test_get_location_tools():
    """Test that get_location_tools returns the expected tools."""
    tools = get_location_tools()
    
    # Verify we get a list
    assert isinstance(tools, list)
    
    # Verify GeoapifyPlacesTool is in the list
    assert any(isinstance(tool, GeoapifyPlacesTool) for tool in tools)
    
    # Verify the expected number of tools (update as more are added)
    assert len(tools) == 1  # Currently only GeoapifyPlacesTool
