"""Crew tests need a MODEL for LLMConfig; pytest-env supplies the API keys."""

import os

os.environ.setdefault("MODEL", "openrouter/test/model")
