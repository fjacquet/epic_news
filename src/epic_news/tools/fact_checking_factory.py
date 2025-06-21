from typing import Any

from .google_fact_check_tool import GoogleFactCheckTool


class FactCheckingToolsFactory:
    """Factory to create fact-checking tools."""

    @staticmethod
    def create(provider: str, **kwargs: Any) -> Any:
        """Create a fact-checking tool based on the provider."""
        if provider == "google":
            return GoogleFactCheckTool(**kwargs)
        else:
            raise ValueError(f"Unknown fact-checking provider: {provider}")
