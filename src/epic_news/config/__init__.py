"""Configuration package for epic_news.

ComposioConfig is intentionally not re-exported: Composio is loaded lazily (company_news and
email sending) because importing it costs ~2 s. Import it from epic_news.config.composio_config.
"""

from epic_news.config.llm_config import LLMConfig

__all__ = ["LLMConfig"]
