"""Composio tool configuration and management for epic_news.

This module provides centralized configuration for Composio tools integration.
Composio offers 500+ tools across various categories for agentic workflows.

IMPORTANT: This module uses Composio 1.0 API which is different from legacy versions.
The old ComposioToolSet API is deprecated and no longer works.

Environment Variables:
    COMPOSIO_API_KEY: Your Composio API key (required)

Composio Setup:
    1. Sign up at https://app.composio.dev
    2. Get your API key from Settings -> API Keys
    3. Add to .env: COMPOSIO_API_KEY=your_key_here
    4. Connect integrations for tools you want to use (see COMPOSIO_SETUP_GUIDE.md)

Note: company_news_crew.py uses the old deprecated API. Update it to use this module instead.
"""
import os
from typing import List, Optional

from composio import Composio
from composio_crewai import CrewAIProvider
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()


class ComposioConfig:
    """Centralized Composio tool configuration for epic_news.

    This class provides factory methods for creating Composio tool instances
    using the Composio 1.0 API with CrewAI provider integration.

    Usage:
        >>> from epic_news.config.composio_config import ComposioConfig
        >>> config = ComposioConfig()
        >>> search_tools = config.get_search_tools()
        >>> social_tools = config.get_social_media_tools()
    """

    def __init__(self, api_key: Optional[str] = None, user_id: str = "default"):
        """Initialize Composio configuration.

        Args:
            api_key: Optional Composio API key. If None, reads from COMPOSIO_API_KEY env var.
            user_id: User ID for Composio API (default: "default")

        Raises:
            ValueError: If COMPOSIO_API_KEY is not set.
        """
        self.api_key = api_key or os.getenv("COMPOSIO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "COMPOSIO_API_KEY environment variable is required for Composio integration. "
                "Please set it in your .env file or get an API key from https://app.composio.dev"
            )

        self.user_id = user_id

        # Initialize Composio client with CrewAI provider
        self.client = Composio(api_key=self.api_key, provider=CrewAIProvider())

    def get_search_tools(self) -> List[BaseTool]:
        """Get search-related Composio tools from social media platforms.

        NOTE: Composio 1.0 has NO dedicated "SEARCH" toolkit. Search functionality
        comes from Reddit, Twitter, and HackerNews toolkits.

        Returns:
            List of CrewAI-compatible search tools from social platforms.

        Available Tools:
            - REDDIT_SEARCH_ACROSS_SUBREDDITS: Search Reddit for topics
            - REDDIT_GET_SUBREDDITS_SEARCH: Find relevant subreddits
            - TWITTER_FULL_ARCHIVE_SEARCH: Search Twitter posts
            - HACKERNEWS_SEARCH_POSTS: Search Hacker News stories

        Example:
            >>> config = ComposioConfig()
            >>> search_tools = config.get_search_tools()
        """
        # Get search tools from social media platforms
        tools = []
        for platform in ["REDDIT", "TWITTER", "HACKERNEWS"]:
            try:
                platform_tools = self.client.tools.get(user_id=self.user_id, toolkits=[platform])
                # Filter to only search-related tools
                search_specific = [t for t in platform_tools if 'search' in t.name.lower()]
                tools.extend(search_specific)
            except Exception as e:
                print(f"Warning: Could not load {platform} search tools: {e}")

        return tools

    def get_social_media_tools(self, platforms: Optional[List[str]] = None) -> List[BaseTool]:
        """Get social media tools for content discovery and analysis.

        Args:
            platforms: List of platforms to get tools for. Options: ['REDDIT', 'TWITTER', 'HACKERNEWS']
                      If None, returns tools for all platforms.

        Returns:
            List of CrewAI-compatible social media tools.

        Setup Required:
            - REDDIT: Connect Reddit account in Composio dashboard
            - TWITTER: Connect Twitter account (requires OAuth)
            - HACKERNEWS: No authentication required

        Example:
            >>> config = ComposioConfig()
            >>> reddit_tools = config.get_social_media_tools(platforms=['REDDIT'])
        """
        if platforms is None:
            platforms = ["REDDIT", "TWITTER", "HACKERNEWS"]

        tools = []
        for platform in platforms:
            try:
                platform_tools = self.client.tools.get(user_id=self.user_id, toolkits=[platform])
                tools.extend(platform_tools)
            except Exception as e:
                # Platform not connected or not available
                print(f"Warning: Could not load {platform} tools: {e}")

        return tools

    def get_financial_tools(self) -> List[BaseTool]:
        """Get financial data and market analysis tools.

        Returns:
            List of CrewAI-compatible financial tools.

        Setup Required:
            - ALPHAVANTAGE: Requires Alpha Vantage API key
            - COINMARKETCAP: Requires CoinMarketCap API key

        Example:
            >>> config = ComposioConfig()
            >>> financial_tools = config.get_financial_tools()
        """
        tools = []
        financial_toolkits = ["ALPHAVANTAGE", "COINMARKETCAP"]

        for toolkit in financial_toolkits:
            try:
                toolkit_tools = self.client.tools.get(user_id=self.user_id, toolkits=[toolkit])
                tools.extend(toolkit_tools)
            except Exception as e:
                print(f"Warning: Could not load {toolkit} tools: {e}")

        return tools

    def get_communication_tools(self) -> List[BaseTool]:
        """Get communication and collaboration tools.

        Returns:
            List of CrewAI-compatible communication tools.

        Setup Required:
            - SLACK: Connect Slack workspace in Composio
            - DISCORD: Connect Discord server
            - NOTION: Connect Notion workspace
            - GMAIL: Already configured in project

        Example:
            >>> config = ComposioConfig()
            >>> comm_tools = config.get_communication_tools()
        """
        tools = []
        comm_toolkits = ["SLACK", "DISCORD", "NOTION", "GMAIL"]

        for toolkit in comm_toolkits:
            try:
                toolkit_tools = self.client.tools.get(user_id=self.user_id, toolkits=[toolkit])
                tools.extend(toolkit_tools)
            except Exception as e:
                print(f"Warning: Could not load {toolkit} tools: {e}")

        return tools

    def get_content_creation_tools(self) -> List[BaseTool]:
        """Get content creation and storage tools.

        Returns:
            List of CrewAI-compatible content creation tools.

        Setup Required:
            - CANVA: Connect Canva account
            - AIRTABLE: Connect Airtable workspace

        Example:
            >>> config = ComposioConfig()
            >>> content_tools = config.get_content_creation_tools()
        """
        tools = []
        content_toolkits = ["CANVA", "AIRTABLE"]

        for toolkit in content_toolkits:
            try:
                toolkit_tools = self.client.tools.get(user_id=self.user_id, toolkits=[toolkit])
                tools.extend(toolkit_tools)
            except Exception as e:
                print(f"Warning: Could not load {toolkit} tools: {e}")

        return tools

    def get_all_tools(self) -> List[BaseTool]:
        """Get all configured Composio tools.

        Returns:
            List of all available CrewAI-compatible Composio tools.

        Example:
            >>> config = ComposioConfig()
            >>> all_tools = config.get_all_tools()
        """
        all_tools = []
        all_tools.extend(self.get_search_tools())
        all_tools.extend(self.get_social_media_tools())
        all_tools.extend(self.get_financial_tools())
        all_tools.extend(self.get_communication_tools())
        all_tools.extend(self.get_content_creation_tools())

        return all_tools

    def get_custom_tools(self, toolkits: List[str]) -> List[BaseTool]:
        """Get tools for custom list of toolkits.

        Args:
            toolkits: List of toolkit names (e.g., ['GITHUB', 'JIRA', 'FIGMA'])

        Returns:
            List of CrewAI-compatible tools for the specified toolkits.

        Example:
            >>> config = ComposioConfig()
            >>> github_jira = config.get_custom_tools(['GITHUB', 'JIRA'])
        """
        tools = []
        for toolkit in toolkits:
            try:
                toolkit_tools = self.client.tools.get(user_id=self.user_id, toolkits=[toolkit])
                tools.extend(toolkit_tools)
            except Exception as e:
                print(f"Warning: Could not load {toolkit} tools: {e}")

        return tools
