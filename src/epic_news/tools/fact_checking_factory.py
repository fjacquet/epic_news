from typing import Any, cast

from crewai.tools import BaseTool
from crewai_custom_tools import GoogleFactCheckTool


class FactCheckingToolsFactory:
    """Factory to create fact-checking tools."""

    @staticmethod
    def create(provider: str, **kwargs: Any) -> BaseTool:
        """Create a fact-checking tool based on the provider."""
        # crewai_custom_tools ships without a py.typed marker, so mypy sees its
        # exports as `Any`; cast() documents that GoogleFactCheckTool is a
        # BaseTool subclass (mirrors WebSearchFactory.create).
        if provider == "google":
            return cast(BaseTool, GoogleFactCheckTool(**kwargs))
        raise ValueError(f"Unknown fact-checking provider: {provider}")
