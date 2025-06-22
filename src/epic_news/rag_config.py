import os

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DEFAULT_RAG_CONFIG = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-large",
        },
    },
    "vectordb": {
        "provider": "chroma",
        "config": {
            "collection_name": "finwiz",
            "dir": os.path.join(
                PROJECT_ROOT, "db"
            ),  # Absolute path to storage directory
            "allow_reset": True,
        },
    },
    "chunker": {
        "chunk_size": 400,
        "chunk_overlap": 100,
        "length_function": "len",
        "min_chunk_size": 150,  # Must be greater than chunk_overlap
    },
}
