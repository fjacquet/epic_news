import copy

from crewai_tools import RagTool

from epic_news.tools.rag_tools import get_rag_tools
from epic_news.tools.save_to_rag_tool import SaveToRagTool

# Make a deep copy of the original DEFAULT_RAG_CONFIG for testing
# to avoid modifying the actual global config during tests.
# We'll patch 'epic_news.tools.rag_tools.DEFAULT_RAG_CONFIG' to use this copy.
# This structure should mirror epic_news.rag_config.DEFAULT_RAG_CONFIG
TEST_DEFAULT_RAG_CONFIG = {
    "llm": {
        "provider": "openai",  # Using a common provider for tests
        "config": {
            "model": "gpt-3.5-turbo",  # Example model
        },
    },
    "embedder": {
        "provider": "openai",  # Using a common provider
        "config": {
            "model": "text-embedding-ada-002",  # Key is 'model', not 'model_name'
        },
    },
    "vectordb": {  # Top-level key for vector database configuration
        "provider": "chroma",
        "config": {
            "collection_name": "epic_news_default_collection",  # Test default collection name
            "dir": "/tmp/test_chroma_db",  # Mocked path for tests
            "allow_reset": True,
        },
    },
    "chunker": {  # Adding chunker as it's in the actual config
        "chunk_size": 500,
        "chunk_overlap": 50,
        "length_function": "len",
        "min_chunk_size": 100,
    },
}


def test_get_rag_tools_no_suffix(mocker):
    mocker.patch(
        "epic_news.tools.rag_tools.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    tools = get_rag_tools()

    assert len(tools) == 2
    retrieval_tool, save_tool = tools

    # Test RagTool (retrieval)
    assert isinstance(retrieval_tool, RagTool)
    assert "retrieve information from the epic_news knowledge base" in retrieval_tool.description
    assert retrieval_tool.summarize is True  # as per current implementation

    # Test SaveToRagTool
    assert isinstance(save_tool, SaveToRagTool)
    assert save_tool._rag_tool == retrieval_tool  # Check if it's the same instance


def test_get_rag_tools_with_suffix(mocker):
    mocker.patch(
        "epic_news.tools.rag_tools.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    suffix = "test_crew"
    tools = get_rag_tools(collection_suffix=suffix)

    assert len(tools) == 2
    retrieval_tool, save_tool = tools

    # Test RagTool (retrieval)
    assert isinstance(retrieval_tool, RagTool)
    assert "retrieve information from the epic_news knowledge base" in retrieval_tool.description

    # Test SaveToRagTool
    assert isinstance(save_tool, SaveToRagTool)
    assert save_tool._rag_tool == retrieval_tool


def test_default_rag_config_immutability(mocker):
    mocker.patch(
        "epic_news.tools.rag_tools.DEFAULT_RAG_CONFIG",
        new_callable=lambda: copy.deepcopy(TEST_DEFAULT_RAG_CONFIG),
    )
    original_collection_name = TEST_DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"]

    # Call with a suffix, which should modify a copy
    get_rag_tools(collection_suffix="stocks")

    # Assert that the mocked DEFAULT_RAG_CONFIG (our deep copy) was not changed by the call above
    assert TEST_DEFAULT_RAG_CONFIG["vectordb"]["config"]["collection_name"] == original_collection_name

    # Call again without suffix - verify tools are created correctly
    tools_no_suffix = get_rag_tools()
    retrieval_tool_no_suffix = tools_no_suffix[0]
    assert isinstance(retrieval_tool_no_suffix, RagTool)

    # Call with another suffix - verify tools are created correctly
    tools_crypto_suffix = get_rag_tools(collection_suffix="crypto")
    retrieval_tool_crypto_suffix = tools_crypto_suffix[0]
    assert isinstance(retrieval_tool_crypto_suffix, RagTool)
