"""What ``LLMConfig.get_openrouter_llm`` actually sends to ``litellm.completion``.

Asserting attributes on the ``LLM`` object is not enough: a kwarg CrewAI does not
forward (or LiteLLM silently drops) looks fine on the object and never reaches the
provider. These tests patch ``litellm.completion``, run a real ``LLM.call`` and
inspect the captured kwargs. A second tier runs LiteLLM's own
``get_optional_params`` to prove the provider payload survives ``drop_params``.
Zero network calls.
"""

import inspect

import litellm
import pytest
from litellm.utils import get_optional_params

from epic_news.config.llm_config import LLMConfig

_ENV_KEYS = (
    "MODEL",
    "LLM_TEMPERATURE",
    "LLM_REASONING_EFFORT",
    "LLM_TIMEOUT_QUICK",
    "LLM_TIMEOUT_DEFAULT",
    "LLM_TIMEOUT_LONG",
    "OPENROUTER_BASE_URL",
    "LLM_EMPTY_RETRIES",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("LLM_EMPTY_RETRIES", "0")


@pytest.fixture
def sent(monkeypatch):
    """Patch ``litellm.completion`` and return a callable that runs one LLM call."""
    captured: list[dict] = []

    def fake_completion(**kwargs):
        captured.append(kwargs)
        return litellm.ModelResponse(
            choices=[
                litellm.Choices(
                    message=litellm.Message(content="Final Answer: ok", role="assistant"),
                    finish_reason="stop",
                )
            ]
        )

    monkeypatch.setattr(litellm, "completion", fake_completion)

    def run(**llm_kwargs) -> dict:
        llm = LLMConfig.get_openrouter_llm(**llm_kwargs)
        llm.call([{"role": "user", "content": "hi"}])
        return captured[-1]

    return run


# --- timeout ---------------------------------------------------------------


def test_default_timeout_reaches_completion(sent):
    assert sent(model="openrouter/mistralai/mistral-small-2603")["timeout"] == 300


@pytest.mark.parametrize(("task_type", "expected"), [("quick", 120), ("default", 300), ("long", 600)])
def test_task_type_selects_timeout(sent, task_type, expected):
    kwargs = sent(model="gemini/gemini-3.8-flash", task_type=task_type)
    assert kwargs["timeout"] == expected


def test_timeout_env_override(sent, monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT_LONG", "900")
    assert sent(model="gemini/gemini-3.8-flash", task_type="long")["timeout"] == 900


# --- temperature -----------------------------------------------------------


@pytest.mark.parametrize(
    "model",
    [
        "gemini/gemini-3.8-flash",
        "openrouter/google/gemini-3.8-flash",
        "vertex_ai/gemini-3.8-flash",
    ],
)
def test_gemini_default_temperature_not_sent_on_any_route(sent, monkeypatch, model):
    monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
    assert "temperature" not in sent(model=model)


def test_gemini_explicit_temperature_is_sent(sent):
    assert sent(model="openrouter/google/gemini-3.8-flash", temperature=0.2)["temperature"] == 0.2


def test_non_gemini_default_temperature_is_sent(sent, monkeypatch):
    monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
    assert sent(model="openrouter/mistralai/mistral-small-2603")["temperature"] == 0.7


# --- reasoning -------------------------------------------------------------


def test_openrouter_reasoning_goes_in_extra_body(sent, monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "high")
    kwargs = sent(model="openrouter/mistralai/magistral-medium-2509")
    assert kwargs["extra_body"] == {"reasoning": {"effort": "high"}}
    assert "reasoning_effort" not in kwargs


def test_openrouter_reasoning_survives_litellm_drop_params():
    """LiteLLM drops top-level ``reasoning_effort`` for models it doesn't know reason."""
    litellm.drop_params = True
    params = get_optional_params(
        model="mistralai/magistral-medium-2509",
        custom_llm_provider="openrouter",
        extra_body={"reasoning": {"effort": "high"}},
    )
    assert params["extra_body"] == {"reasoning": {"effort": "high"}}


def test_native_gemini3_defaults_to_medium_reasoning(sent):
    kwargs = sent(model="gemini/gemini-3.8-flash")
    assert kwargs["reasoning_effort"] == "medium"
    assert "extra_body" not in kwargs


def test_native_gemini3_medium_maps_to_thinking_level_medium():
    litellm.drop_params = True
    params = get_optional_params(
        model="gemini-3.8-flash", custom_llm_provider="gemini", reasoning_effort="medium"
    )
    assert params["thinkingConfig"]["thinkingLevel"] == "medium"


def test_openrouter_gemini3_defaults_to_medium_reasoning_in_extra_body(sent):
    kwargs = sent(model="openrouter/google/gemini-3.8-flash")
    assert kwargs["extra_body"] == {"reasoning": {"effort": "medium"}}


def test_gemini3_explicit_none_is_sent_not_dropped(sent, monkeypatch):
    """Dropping it would fall back to the API default (high); LiteLLM maps none->low."""
    monkeypatch.setenv("LLM_REASONING_EFFORT", "none")
    assert sent(model="gemini/gemini-3.8-flash")["reasoning_effort"] == "none"


def test_env_effort_overrides_gemini_default(sent, monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", " HIGH ")
    assert sent(model="gemini/gemini-3.8-flash")["reasoning_effort"] == "high"


@pytest.mark.parametrize("effort", ["", "none"])
def test_non_gemini_reasoning_stays_opt_in(sent, monkeypatch, effort):
    monkeypatch.setenv("LLM_REASONING_EFFORT", effort)
    kwargs = sent(model="openrouter/mistralai/mistral-small-2603")
    assert "reasoning_effort" not in kwargs
    assert "extra_body" not in kwargs


def test_older_gemini_gets_no_default_reasoning(sent):
    kwargs = sent(model="gemini/gemini-2.5-flash")
    assert "reasoning_effort" not in kwargs


# --- transport -------------------------------------------------------------


def test_num_retries_reaches_completion(sent):
    assert sent(model="gemini/gemini-3.8-flash")["num_retries"] == 2


def test_openrouter_base_url_default(sent):
    assert sent(model="openrouter/mistralai/mistral-small-2603")["base_url"] == "https://openrouter.ai/api/v1"


def test_openrouter_base_url_from_env(sent, monkeypatch):
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://proxy.example/api/v1")
    assert sent(model="openrouter/mistralai/mistral-small-2603")["base_url"] == "https://proxy.example/api/v1"


def test_native_route_gets_no_base_url(sent, monkeypatch):
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://proxy.example/api/v1")
    assert "base_url" not in sent(model="gemini/gemini-3.8-flash")


def test_middle_out_option_removed(sent):
    assert "enable_middle_out" not in inspect.signature(LLMConfig.get_openrouter_llm).parameters
    assert "transforms" not in sent(model="openrouter/mistralai/mistral-small-2603")
