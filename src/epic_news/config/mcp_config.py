"""MCP Server configurations for epic_news.

This module provides configuration for Model Context Protocol (MCP) servers
that enhance crew capabilities with advanced tools and integrations.

Available MCP Servers:
- Perplexity MCP: Advanced web research and reasoning
- Wikipedia MCP: Maintained Wikipedia integration
- Custom Tools MCP: Dynamic loading of project-specific tools

Environment Variables:
    PERPLEXITY_API_KEY: API key for Perplexity MCP server
"""

import contextlib
import os
from typing import Optional

from dotenv import load_dotenv

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
    def get_perplexity_mcp():
        """Configure Perplexity MCP server for advanced research.

        The Perplexity MCP server provides access to Perplexity AI's advanced
        research capabilities including web search, conversational AI, deep
        research, and reasoning.

        Available Tools:
        - perplexity_search: Direct web search with real-time results
        - perplexity_ask: Conversational AI with integrated search
        - perplexity_research: Deep research using sonar-deep-research model
        - perplexity_reason: Advanced reasoning capabilities

        Environment Variables:
            PERPLEXITY_API_KEY: Required. Your Perplexity API key.

        Returns:
            dict: MCP server configuration for Perplexity, compatible with MCPServerAdapter.

        Raises:
            ValueError: If PERPLEXITY_API_KEY is not set.

        Example:
            >>> from crewai_tools import MCPServerAdapter
            >>> mcp_params = MCPConfig.get_perplexity_mcp()
            >>> with MCPServerAdapter(mcp_params) as tools:
            >>>     # Use tools with agents
            >>>     pass
        """
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError(
                "PERPLEXITY_API_KEY environment variable is required for Perplexity MCP. "
                "Please set it in your .env file."
            )

        return {
            "command": "npx",
            "args": ["@perplexity-ai/mcp-server"],
            "env": {"PERPLEXITY_API_KEY": api_key},
        }

    @staticmethod
    def get_wikipedia_mcp():
        """Configure Wikipedia MCP server for knowledge retrieval.

        The Wikipedia MCP server provides maintained access to Wikipedia's
        knowledge base with language support and efficient content retrieval.

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
        return {
            "command": "uvx",
            "args": ["--from", "wikipedia-mcp-server@latest", "wikipedia-mcp"],
            "env": {},
        }

    @staticmethod
    def get_custom_tools_mcp(project_root: str | None = None):
        """Configure custom tools MCP server for project-specific tools.

        This MCP server exposes the epic_news custom tools (62 tools) via the
        MCP protocol, enabling dynamic tool loading and better observability.

        Args:
            project_root: Optional path to project root. If None, uses current directory.

        Returns:
            dict: MCP server configuration for custom tools.

        Note:
            This server needs to be implemented as part of Phase 3.3.
            See src/epic_news/mcp_servers/tools_server.py (to be created).

        Example:
            >>> mcp_config = MCPConfig.get_custom_tools_mcp()
            >>> # Use with CrewAI MCP integration
        """
        return {
            "command": "python",
            "args": ["-m", "epic_news.mcp_servers.tools_server"],
            "env": {"PROJECT_ROOT": project_root or os.getcwd()},
        }

    @staticmethod
    def get_all_mcp_servers():
        """Get all configured MCP servers.

        Returns:
            dict: Dictionary of all MCP server configurations.

        Example:
            >>> all_servers = MCPConfig.get_all_mcp_servers()
            >>> perplexity = all_servers['perplexity']
            >>> wikipedia = all_servers['wikipedia']
        """
        servers = {
            "wikipedia": MCPConfig.get_wikipedia_mcp(),
        }

        # Only include Perplexity if API key is available
        with contextlib.suppress(ValueError):
            servers["perplexity"] = MCPConfig.get_perplexity_mcp()

        return servers
