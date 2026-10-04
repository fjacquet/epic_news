"""MCP Server configurations for epic_news.

This module provides configuration for Model Context Protocol (MCP) servers
that enhance crew capabilities with advanced tools and integrations.

Available MCP Servers:
- Wikipedia MCP: Maintained Wikipedia integration
"""

import sysconfig
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from dotenv import load_dotenv
from loguru import logger
from mcp import StdioServerParameters

load_dotenv()


def get_mcp_tools_or_empty(crew: Any) -> list[BaseTool]:
    """Return ``crew.get_mcp_tools()``, or ``[]`` when the MCP server cannot start.

    ``crew`` is a ``@CrewBase`` instance declaring ``mcp_server_params``; CrewBase
    owns the adapter and stops it after kickoff. MCP tools are supplementary, so a
    server that fails to start must not take the whole crew down with it.
    """
    try:
        return list(crew.get_mcp_tools())
    except Exception as exc:
        logger.warning(
            f"⚠️ MCP server unavailable for {type(crew).__name__}; continuing without its tools: {exc}"
        )
        return []


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
