from typing import Any

from crewai_custom_tools import GoogleFactCheckTool


class FactCheckingToolsFactory:
    """Factory to create fact-checking tools."""

    @staticmethod
    def create(provider: str, **kwargs: Any) -> Any:
        """Create a fact-checking tool based on the provider."""
        if provider == "google":
            return GoogleFactCheckTool(**kwargs)
        raise ValueError(f"Unknown fact-checking provider: {provider}")
