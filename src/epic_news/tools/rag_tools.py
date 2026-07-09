"""
RAG tools for knowledge retrieval and storage across epic_news crews.

This module provides tools for Retrieval Augmented Generation (RAG)
to enable crews to store and retrieve knowledge across sessions.
"""

from crewai.tools import BaseTool as Tool
from crewai_custom_tools import SaveToRagTool
from crewai_tools import RagTool

from epic_news.rag_config import build_rag_tool_kwargs


def get_rag_tools(collection_suffix: str | None = None) -> list[Tool]:
    """
    Get RAG tools for knowledge retrieval and storage.

    Args:
        collection_suffix: Optional suffix to create crew-specific collections.
            For example, "stock" would create a "epic_news-stock" collection.

    Returns:
        List of RAG tools for knowledge retrieval and storage.
    """
    rag_tool = RagTool(
        **build_rag_tool_kwargs(collection_suffix=collection_suffix),
        summarize=True,
        description=(
            "Use this tool to retrieve information from the epic_news knowledge base. "
            "Ask questions about financial data, market trends, or previously "
            "researched information."
        ),
    )

    save_to_rag_tool = SaveToRagTool(rag_tool=rag_tool)

    return [rag_tool, save_to_rag_tool]
