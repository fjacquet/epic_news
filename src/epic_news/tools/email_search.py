"""Delegating email search tool that routes to specific providers."""

import json

from crewai.tools import BaseTool
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel

from epic_news.models.email_search_models import DelegatingEmailSearchInput

from .hunter_io_tool import HunterIOTool  # Import the actual tool
from .serper_email_search_tool import SerperEmailSearchTool  # Import the actual tool

# Load environment variables from .env file
load_dotenv()


class DelegatingEmailSearchTool(BaseTool):
    """Routes email search queries to Hunter.io or Serper based on the specified provider."""

    name: str = "email_search_router"
    description: str = (
        "Finds professional email addresses using a specified provider. "
        "Use 'hunter' for domain-specific searches (e.g., 'example.com'). "
        "Use 'serper' for company name or broader web searches (e.g., 'Example Inc')."
    )
    args_schema: type[BaseModel] = DelegatingEmailSearchInput

    def _run(self, provider: str, query: str) -> str:
        """Delegates the email search to the appropriate tool based on the provider."""
        provider = provider.lower().strip()
        try:
            if provider == "hunter":
                hunter_tool = HunterIOTool()
                # The HunterIOTool from hunter_io_tool.py expects 'domain' in its _run method
                return hunter_tool._run(domain=query)
            if provider == "serper":
                serper_tool = SerperEmailSearchTool()
                # The SerperEmailSearchTool from serper_email_search_tool.py expects 'query'
                return serper_tool._run(query=query)
            logger.error(f"Invalid email search provider: {provider}")
            return json.dumps({"error": f"Invalid provider: '{provider}'. Must be 'hunter' or 'serper'."})
        except ValueError as ve:
            # Catches API key errors from underlying tools
            logger.error(f"Initialization error for provider '{provider}': {ve}")
            return json.dumps({"error": f"Configuration error for {provider}: {str(ve)}"})
        except Exception as e:
            logger.error(f"Error running email search with provider '{provider}' for query '{query}': {e}")
            return json.dumps({"error": f"Failed to execute search with {provider}: {str(e)}"})


def get_email_search_tools() -> list[BaseTool]:
    """Returns a list of email search tools."""
    return [DelegatingEmailSearchTool()]
