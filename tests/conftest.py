import os

# crewai-custom-tools >=0.4.0: PerplexitySearchTool fails fast at construction
# without a key. CI has no .env; give the suite a dummy so construction-time
# wiring works. Tests that verify missing-key behavior monkeypatch.delenv.
os.environ.setdefault("PERPLEXITY_API_KEY", "test-key")
