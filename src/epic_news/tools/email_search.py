"""Email search tool factory.

The delegating tool implementation now lives in crewai_custom_tools; epic_news
keeps only the factory so crew call sites (`get_email_search_tools`) are unchanged.
"""

from crewai.tools import BaseTool
from crewai_custom_tools import DelegatingEmailSearchTool


def get_email_search_tools() -> list[BaseTool]:
    """Returns a list of email search tools."""
    return [DelegatingEmailSearchTool()]
