import os

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

DEFAULT_RAG_CONFIG = {
    "llm": {
        "provider": "openrouter",  # Changed from openai to openrouter
        "config": {
            "model": os.getenv("MODEL", "openrouter/xiaomi/mimo-v2-flash:free"),
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": "https://openrouter.ai/api/v1",
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": 1000,
        },
    },
    "embedder": {
        "provider": "openai",  # Keep OpenAI for embeddings
        "config": {
            "model": "text-embedding-3-large",
        },
    },
    "vectordb": {
        "provider": "chroma",
        "config": {
            "collection_name": "finwiz",
            "dir": os.path.join(PROJECT_ROOT, "db"),  # Absolute path to storage directory
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
