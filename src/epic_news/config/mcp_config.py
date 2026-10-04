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
    owns the adapter and stops it after a successful kickoff (see :func:`close_mcp`
    for the failure path). MCP tools are supplementary, so a server that fails to
    start must not take the whole crew down with it. A failed start is remembered on
    the crew instance so the remaining agents don't each retry (and time out).
    """
    if getattr(crew, "_mcp_start_failed", False):
        return []
    try:
        return list(crew.get_mcp_tools())
    except Exception as exc:
        crew._mcp_start_failed = True
        logger.warning(
            f"⚠️ MCP server unavailable for {type(crew).__name__}; continuing without its tools: {exc}"
        )
        return []


def close_mcp(crew: Any) -> None:
    """Stop the crew's CrewBase-managed MCP adapter, if one was started.

    CrewBase stops the adapter only in an after-kickoff hook, i.e. after a
    *successful* kickoff; call this in a ``finally`` so a failed run does not leak
    the server subprocess. Safe after that hook and safe to call twice: the
    reference is cleared before stopping, and stop errors are logged, not raised.
    """
    adapter = getattr(crew, "_mcp_server_adapter", None)
    if adapter is None:
        return
    crew._mcp_server_adapter = None
    try:
        adapter.stop()
    except Exception as exc:
        logger.warning(f"⚠️ Error stopping MCP server for {type(crew).__name__}: {exc}")


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
