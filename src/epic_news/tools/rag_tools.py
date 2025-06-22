"""
RAG tools for knowledge retrieval and storage across epic_news crews.

This module provides tools for Retrieval Augmented Generation (RAG)
to enable crews to store and retrieve knowledge across sessions.
"""

import copy  # Add import for deepcopy
from typing import List, Optional

from crewai.tools import BaseTool as Tool
from crewai_tools import RagTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from epic_news.rag_config import DEFAULT_RAG_CONFIG
from epic_news.tools.save_to_rag_tool import SaveToRagTool


def get_rag_tools(collection_suffix: Optional[str] = None) -> List[Tool]:
    """
    Get RAG tools for knowledge retrieval and storage.

    Args:
        collection_suffix: Optional suffix to create crew-specific collections.
            For example, "stock" would create a "epic_news-stock" collection.

    Returns:
        List of RAG tools for knowledge retrieval and storage.
    """
    # Create a deep copy of the default config to prevent mutation
    config = copy.deepcopy(DEFAULT_RAG_CONFIG)

    # If a collection suffix is provided, create a crew-specific collection
    if collection_suffix:
        # No need to copy config["vectordb"]["config"] again as config is already a deepcopy
        config["vectordb"]["config"]["collection_name"] = f"epic_news-{collection_suffix}"

    # Instantiate the LLM and Embedder
    llm = ChatOpenAI(**config['llm']['config'])
    embedder = OpenAIEmbeddings(**config['embedder']['config'])

    # Determine the collection name
    collection_name = config['vectordb']['config']['collection_name']

    # Create the RAG tool for retrieval with app_config to ensure collection_name is properly set
    rag_tool = RagTool(
        llm=llm,
        embedder=embedder,
        chunker_config=config['chunker'],
        vectordb_config=config['vectordb'],
        app_config={
            'collection_name': collection_name,  # This ensures the collection name is properly set
            'db': {
                'dir': config['vectordb']['config'].get('dir', '/tmp/chroma_db')
            }
        },
        summarize=True,
        description=(
            "Use this tool to retrieve information from the epic_news knowledge base. "
            "Ask questions about financial data, market trends, or previously "
            "researched information."
        ),
    )

    # Create the SaveToRag tool for storage
    save_to_rag_tool = SaveToRagTool(rag_tool=rag_tool)

    return [rag_tool, save_to_rag_tool]
