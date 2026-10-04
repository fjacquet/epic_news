from epic_news.config.llm_config import LLMConfig


def test_default_model_is_gemini_3_8_flash(monkeypatch):
    """ADR-016: with MODEL unset, LLMConfig falls back to Gemini 3.8 Flash (native route)."""
    monkeypatch.delenv("MODEL", raising=False)

    llm = LLMConfig.get_openrouter_llm()

    assert llm.model == "gemini/gemini-3.8-flash"
