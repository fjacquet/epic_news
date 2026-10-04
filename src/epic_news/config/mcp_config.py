"""MCP Server configurations for epic_news.

This module provides configuration for Model Context Protocol (MCP) servers
that enhance crew capabilities with advanced tools and integrations.

Available MCP Servers:
- Wikipedia MCP: Maintained Wikipedia integration
"""

import sysconfig
from pathlib import Path

from dotenv import load_dotenv
from mcp import StdioServerParameters

load_dotenv()


class MCPConfig:
    """Centralized MCP server configuration.

    This class provides factory methods for creating MCP server configurations
    that can be used with CrewAI's MCPServerAdapter.

    Usage:
        >>> from epic_news.config.mcp_config import MCPConfig
        >>> from crewai_tools import MCPServerAdapter
        >>>
        >>> # Get Wikipedia MCP tools
        >>> wikipedia_params = MCPConfig.get_wikipedia_mcp()
        >>> with MCPServerAdapter(wikipedia_params) as tools:
        >>>     # tools is now available for agents
        >>>     pass
    """

    @staticmethod
    def get_wikipedia_mcp():
        """Configure Wikipedia MCP server for knowledge retrieval.

        The Wikipedia MCP server provides maintained access to Wikipedia's
        knowledge base with language support and efficient content retrieval.
        It runs the ``wikipedia-mcp`` console script of the locked
        ``wikipedia-mcp-server`` dependency installed in this environment,
        rather than downloading an unpinned release at runtime.

        Available Tools:
        - search: Search Wikipedia articles with language support
        - fetch: Fetch full page content by article ID

        Returns:
            dict: MCP server configuration for Wikipedia, compatible with MCPServerAdapter.

        Example:
            >>> from crewai_tools import MCPServerAdapter
            >>> mcp_params = MCPConfig.get_wikipedia_mcp()
            >>> with MCPServerAdapter(mcp_params) as tools:
            >>>     # Use tools with agents
            >>>     pass
        """
        return StdioServerParameters(
            command=str(Path(sysconfig.get_path("scripts")) / "wikipedia-mcp"),
            args=[],
            env={},
        )
