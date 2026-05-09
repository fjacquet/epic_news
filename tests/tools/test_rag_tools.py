import copy
from typing import Any

from crewai_tools import RagTool

from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.save_to_rag_tool import SaveToRagTool

# Mirror the production DEFAULT_RAG_CONFIG shape (crewai-tools 1.x).
TEST_DEFAULT_RAG_CONFIG: dict[str, Any] = {
    "vectordb": {
        "provider": "chromadb",
        "config": {
            "persist_directory": "/tmp/test_chroma_db",
            "collection_name": "epic_news_default_collection",
        },
    },
    "embedding_model": {
        "provider": "openai",
        "config": {
            "model_name": "text-embedding-ada-002",
        },
    },
}


def test_get_rag_tools_no_suffix(mocker):
    mocker.patch(
        "epic_news.rag_config.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    tools = get_rag_tools()

    assert len(tools) == 2
    retrieval_tool, save_tool = tools

    # Test RagTool (retrieval)
    assert isinstance(retrieval_tool, RagTool)
    assert "retrieve information from the epic_news knowledge base" in retrieval_tool.description
    assert retrieval_tool.summarize is True
    assert retrieval_tool.collection_name == "epic_news_default_collection"

    # Test SaveToRagTool
    assert isinstance(save_tool, SaveToRagTool)
    assert save_tool._rag_tool == retrieval_tool


def test_get_rag_tools_with_suffix(mocker):
    mocker.patch(
        "epic_news.rag_config.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    suffix = "test_crew"
    tools = get_rag_tools(collection_suffix=suffix)

    assert len(tools) == 2
    retrieval_tool, save_tool = tools

    # Test RagTool (retrieval)
    assert isinstance(retrieval_tool, RagTool)
    assert "retrieve information from the epic_news knowledge base" in retrieval_tool.description
    assert retrieval_tool.collection_name == f"epic_news-{suffix}"

    # Test SaveToRagTool
    assert isinstance(save_tool, SaveToRagTool)
    assert save_tool._rag_tool == retrieval_tool


def test_default_rag_config_immutability(mocker):
    mocker.patch(
        "epic_news.rag_config.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    original_collection_name = TEST_DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"]

    # Call with a suffix, which should not mutate the source config.
    get_rag_tools(collection_suffix="stocks")
    assert TEST_DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"] == original_collection_name

    # Subsequent calls produce fresh tool instances.
    tools_no_suffix = get_rag_tools()
    assert isinstance(tools_no_suffix[0], RagTool)

    tools_crypto_suffix = get_rag_tools(collection_suffix="crypto")
    assert isinstance(tools_crypto_suffix[0], RagTool)
