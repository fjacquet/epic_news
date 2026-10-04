"""Configuration package for epic_news.

ComposioConfig is intentionally not re-exported: importing Composio costs ~2 s and
only company_news uses it (import it from epic_news.config.composio_config).
"""

from epic_news.config.llm_config import LLMConfig
from epic_news.config.mcp_config import MCPConfig

__all__ = ["LLMConfig", "MCPConfig"]
