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

from composio import Composio
from composio_crewai import CrewAIProvider
from crewai.tools import BaseTool
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class ComposioConfig:
    """Centralized Composio tool configuration for epic_news.

    This class provides factory methods for creating Composio tool instances
    using the Composio 1.0 API with CrewAI provider integration.

    Usage:
        >>> from epic_news.config.composio_config import ComposioConfig
        >>> config = ComposioConfig()
        >>> search_tools = config.get_search_tools()
    """

    def __init__(self, api_key: str | None = None, user_id: str = "default"):
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

    def get_search_tools(self) -> list[BaseTool]:
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
                search_specific = [t for t in platform_tools if "search" in t.name.lower()]
                tools.extend(search_specific)
            except Exception as e:
                logger.error("❌ Could not load {} search tools from Composio: {}", platform, e)

        return tools

    def get_gmail_email_tools(self, include_send: bool = True) -> list[BaseTool]:
        """Get Gmail email tools including send functionality.

        IMPORTANT: The Gmail toolkit query only returns ~20 tools due to API pagination.
        This method explicitly requests all important Gmail tools including SEND actions.

        Args:
            include_send: If True, includes GMAIL_SEND_EMAIL and GMAIL_SEND_DRAFT tools.

        Returns:
            List of CrewAI-compatible Gmail tools.

        Available Tools (when include_send=True):
            - GMAIL_SEND_EMAIL: Send a new email
            - GMAIL_SEND_DRAFT: Send an existing draft
            - GMAIL_CREATE_EMAIL_DRAFT: Create a draft email
            - GMAIL_REPLY_TO_THREAD: Reply to an email thread
            - GMAIL_FORWARD_MESSAGE: Forward an email
            - GMAIL_FETCH_EMAILS: Fetch emails from inbox
            - GMAIL_GET_PROFILE: Get user profile

        Example:
            >>> config = ComposioConfig()
            >>> gmail_tools = config.get_gmail_email_tools()
        """
        tools = []

        # Core Gmail tools to explicitly request
        gmail_tools_list = [
            "GMAIL_CREATE_EMAIL_DRAFT",
            "GMAIL_FETCH_EMAILS",
            "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            "GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
            "GMAIL_FORWARD_MESSAGE",
            "GMAIL_GET_PROFILE",
            "GMAIL_GET_ATTACHMENT",
            "GMAIL_ADD_LABEL_TO_EMAIL",
            "GMAIL_CREATE_LABEL",
        ]

        # Add send tools if requested
        if include_send:
            gmail_tools_list.extend(
                [
                    "GMAIL_SEND_EMAIL",
                    "GMAIL_SEND_DRAFT",
                    "GMAIL_REPLY_TO_THREAD",
                ]
            )

        try:
            tools = self.client.tools.get(user_id=self.user_id, tools=gmail_tools_list)
        except Exception as e:
            # A 401 here means COMPOSIO_API_KEY is missing/invalid. Callers previously
            # treated the resulting empty list as "no tools configured" and let a
            # tool-less agent report the email as sent.
            hint = (
                " Check COMPOSIO_API_KEY in .env — Composio rejected the credentials."
                if "401" in str(e) or "Invalid API key" in str(e)
                else ""
            )
            logger.error("❌ Could not load Gmail tools from Composio: {}.{}", e, hint)

        return tools
