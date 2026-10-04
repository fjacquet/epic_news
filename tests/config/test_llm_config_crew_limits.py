"""Crew limit defaults from LLMConfig."""

from epic_news.config.llm_config import LLMConfig


def test_max_iter_defaults_to_15(monkeypatch):
    monkeypatch.delenv("CREW_MAX_ITER", raising=False)
    assert LLMConfig.get_max_iter() == 15


def test_max_iter_reads_env(monkeypatch):
    monkeypatch.setenv("CREW_MAX_ITER", "7")
    assert LLMConfig.get_max_iter() == 7
