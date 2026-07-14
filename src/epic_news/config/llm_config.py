"""Centralized LLM configuration for OpenRouter."""

import os

from crewai import LLM
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def _is_empty_llm_response(result: object) -> bool:
    """True when an ``LLM.call`` result carries no usable text.

    CrewAI's ReAct path returns the model's answer as a ``str``; an empty/blank
    string or ``None`` means the provider produced no output text for this turn.
    """
    if result is None:
        return True
    return isinstance(result, str) and not result.strip()


def _call_with_empty_retry(call_fn, max_retries: int, model: str = "?"):
    """Invoke ``call_fn`` and re-invoke it while it returns an empty LLM response.

    Retries at most ``max_retries`` times, then returns the last (possibly empty)
    result so the caller's normal empty-handling still applies. Extracted from the
    ``LLM.call`` patch so the retry loop is unit-testable without live calls.
    """
    result = call_fn()
    attempts = 0
    while attempts < max_retries and _is_empty_llm_response(result):
        attempts += 1
        logger.warning(
            f"Empty response from LLM '{model}' (likely Gemini thought-only turn); "
            f"retrying {attempts}/{max_retries}"
        )
        result = call_fn()
    return result


def _patch_anthropic_detection_for_openrouter() -> None:
    """Stop CrewAI applying its *native*-Anthropic message workaround on OpenRouter.

    CrewAI flags any model whose name contains ``anthropic/``/``claude-`` as
    Anthropic (``LLM._is_anthropic_model``) and, for such models, prepends a dummy
    ``{"role": "user", "content": "."}`` before a leading system message
    (``LLM._format_messages_for_provider``). That is only correct for Anthropic's
    *native* API, where LiteLLM hoists system content into the top-level ``system``
    parameter. Over OpenRouter's OpenAI-compatible endpoint LiteLLM passes messages
    verbatim, so the prepend leaves the system message at index 1 and Anthropic
    rejects the request::

        messages.1: role 'system' must precede an 'assistant' message or end the array

    ``is_anthropic`` is re-derived from the model string on every construction *and*
    on ``LLM.__deepcopy__`` (which reconstructs the LLM without carrying the flag),
    and CrewAI deep-copies agent LLMs while assembling crews — so a post-construction
    override does not survive. Patching the classifier is the only lever that sticks;
    native ``anthropic/`` routing (no ``openrouter/`` prefix) keeps its correct
    behaviour.
    """
    if getattr(LLM, "_openrouter_anthropic_patched", False):
        return

    original = LLM._is_anthropic_model

    def _is_anthropic_model(model: str) -> bool:
        if model.lower().startswith("openrouter/"):
            return False
        return original(model)

    LLM._is_anthropic_model = staticmethod(_is_anthropic_model)  # type: ignore[method-assign]
    LLM._openrouter_anthropic_patched = True  # type: ignore[attr-defined]


def _force_react_tool_calling() -> None:
    """Keep CrewAI on ReAct (text) tool-calling instead of native function-calling.

    CrewAI's experimental agent executor calls ``LLM.supports_function_calling()``
    to choose between a provider's native function-calling and ReAct-style
    (Thought / Action / Action Input) tool-calling. Native function-calling trips
    provider-specific bugs in the executor:

    * Gemini returns a ``tool_calls`` list that CrewAI assigns to ``TaskOutput.raw``
      (a ``str`` field) -> ``ValidationError: Input should be a valid string``.
    * Anthropic's forced-final-answer prefill is rejected by the API.

    This project's crews are already tuned for ReAct: the default OpenRouter/Mistral
    model reports ``supports_function_calling() == False``, so ReAct is the proven,
    working path. Force it for every provider so behaviour is uniform and native-fc
    executor bugs cannot resurface when the model is swapped.
    """
    if getattr(LLM, "_react_tool_calling_forced", False):
        return

    def supports_function_calling(self: LLM) -> bool:
        return False

    LLM.supports_function_calling = supports_function_calling  # type: ignore[method-assign]
    LLM._react_tool_calling_forced = True  # type: ignore[attr-defined]


def _patch_llm_retry_on_empty() -> None:
    """Retry ``LLM.call`` when a provider returns empty content.

    ``gemini/gemini-3.5-flash`` intermittently returns a *thought-only* response on
    CrewAI ReAct steps: the generated tokens land in a thinking block carrying a
    ``thought_signature`` and ``message.content`` comes back ``None`` (``finish_reason``
    is still ``stop``, so it is not a length/budget cut-off). CrewAI's
    ``_validate_and_finalize_llm_response`` rejects the empty answer with
    ``ValueError: Invalid response from LLM call - None or empty`` and the task dies
    after its three built-in retries. Measured on a captured failing prompt, the
    empties are *stochastic* (~40-60% per call on the worst prompts) and, counter-
    intuitively, get worse with thinking disabled — so re-issuing the identical call
    a handful of times reliably yields text. CrewAI deep-copies agent LLMs while
    assembling crews, so this must patch the class, not an instance.

    Provider-agnostic and cheap: a non-empty response returns on the first call, so
    only genuine empties pay the retry cost. Tune the ceiling with ``LLM_EMPTY_RETRIES``
    (default 6); set it to 0 to disable.
    """
    if getattr(LLM, "_retry_on_empty_patched", False):
        return

    original_call = LLM.call

    def call(self: LLM, *args, **kwargs):
        max_retries = int(os.getenv("LLM_EMPTY_RETRIES", "6"))
        return _call_with_empty_retry(
            lambda: original_call(self, *args, **kwargs),
            max_retries,
            getattr(self, "model", "?"),
        )

    LLM.call = call  # type: ignore[method-assign]
    LLM._retry_on_empty_patched = True  # type: ignore[attr-defined]


_patch_anthropic_detection_for_openrouter()
_force_react_tool_calling()
_patch_llm_retry_on_empty()


class LLMConfig:
    """Centralized LLM configuration using OpenRouter.

    This class provides a single source of truth for LLM configuration across
    all crews in the epic_news project. It uses OpenRouter as the primary LLM
    provider, allowing flexible model selection while maintaining cost efficiency.

    Environment Variables:
        MODEL: Model identifier (default: "openrouter/mistralai/mistral-small-2603")
        OPENROUTER_API_KEY: OpenRouter API key
        LLM_TEMPERATURE: Response randomness (0.0-2.0, default: 0.7)
        LLM_MAX_TOKENS: Maximum response tokens (optional)
        LLM_TIMEOUT_QUICK: Timeout for quick tasks (default: 120s)
        LLM_TIMEOUT_DEFAULT: Timeout for standard tasks (default: 300s)
        LLM_TIMEOUT_LONG: Timeout for complex tasks (default: 600s)
        CREW_MAX_ITER: Maximum iterations per crew (default: 5)
        CREW_MAX_RPM: Maximum requests per minute (default: 20)
        OPENROUTER_MIDDLE_OUT: Enable middle-out compression (default: true)

    OpenRouter Transforms:
        The "middle-out" transform automatically compresses prompts that exceed
        the model's context window by removing content from the middle while
        preserving the beginning (system prompts) and end (recent context).
        This is enabled by default to prevent context overflow errors.

    Usage:
        >>> from epic_news.config.llm_config import LLMConfig
        >>> llm = LLMConfig.get_openrouter_llm()
        >>> timeout = LLMConfig.get_timeout("long")
    """

    @staticmethod
    def get_openrouter_llm(
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        enable_middle_out: bool | None = None,
        reasoning_effort: str | None = None,
    ) -> LLM:
        """Get CrewAI LLM instance configured for OpenRouter.

        This method creates a CrewAI LLM instance configured to use
        OpenRouter's API. It reads configuration from environment variables,
        with sensible defaults for missing values.

        Args:
            model: Model name (e.g., "openrouter/mistralai/mistral-small-2603").
                   If None, uses MODEL from .env.
            temperature: LLM temperature (0.0-2.0). Controls response randomness.
                        Lower values (0.0-0.3) are more deterministic.
                        Higher values (0.7-2.0) are more creative.
                        If None, uses LLM_TEMPERATURE from .env (default: 0.7).
            max_tokens: Maximum response tokens. Limits response length.
                       If None, uses LLM_MAX_TOKENS from .env (unlimited if not set).
            enable_middle_out: Enable OpenRouter's middle-out compression to handle
                              context overflow. When enabled, prompts exceeding the
                              model's context window are automatically compressed.
                              If None, uses OPENROUTER_MIDDLE_OUT from .env (default: true).
            reasoning_effort: Reasoning effort level for models that support it
                             (e.g., Mistral Magistral: "low", "medium", "high").
                             If None, reads LLM_REASONING_EFFORT from .env.
                             Only applied when set to a non-empty value other than "none".

        Returns:
            CrewAI LLM instance configured for OpenRouter API.

        Example:
            >>> # Use default configuration (with middle-out enabled)
            >>> llm = LLMConfig.get_openrouter_llm()
            >>>
            >>> # Override temperature for creative tasks
            >>> creative_llm = LLMConfig.get_openrouter_llm(temperature=1.2)
            >>>
            >>> # Use different model
            >>> opus_llm = LLMConfig.get_openrouter_llm(
            ...     model="openrouter/anthropic/claude-3.5-sonnet"
            ... )
            >>>
            >>> # Disable middle-out for precise context control
            >>> precise_llm = LLMConfig.get_openrouter_llm(enable_middle_out=False)
        """
        # Get model from parameter or environment
        model_name = model or os.getenv("MODEL", "openrouter/mistralai/mistral-small-2603")

        # Get temperature from parameter or environment
        temp = temperature
        if temp is None:
            temp_str = os.getenv("LLM_TEMPERATURE", "0.7")
            temp = float(temp_str)

        # Get max_tokens from parameter or environment
        tokens = max_tokens
        if tokens is None:
            max_tokens_str = os.getenv("LLM_MAX_TOKENS")
            if max_tokens_str is not None and max_tokens_str.strip():
                tokens = int(max_tokens_str)

        # Get middle-out setting from parameter or environment (default: enabled)
        middle_out = enable_middle_out
        if middle_out is None:
            middle_out_str = os.getenv("OPENROUTER_MIDDLE_OUT", "true").lower()
            middle_out = middle_out_str in ("true", "1", "yes", "on")

        # Resolve reasoning_effort from parameter or environment (opt-in only).
        # Normalize empty/"none" to None: the LiteLLM LLM class validates this
        # against Literal['none','low','medium','high'] and rejects "" (the old
        # native provider silently tolerated the empty string).
        effort = reasoning_effort
        if effort is None:
            effort = os.getenv("LLM_REASONING_EFFORT", "")
        # Normalize the value itself (not just the sentinel check): LiteLLM
        # validates against a lowercase Literal, so "LOW"/" Low " must become "low".
        effort = effort.strip().lower() if effort else ""
        if effort in ("none", ""):
            effort = None

        # Note: OpenRouter middle-out transforms are not supported by CrewAI's
        # native LLM class (which uses its own OpenAI client). OpenRouter handles
        # context overflow gracefully server-side regardless.

        resolved_model = model_name or "openrouter/mistralai/mistral-small-2603"

        # Route-aware transport. Only "openrouter/"-prefixed models go through
        # OpenRouter's OpenAI-compatible endpoint (api_key + base_url below). Every
        # other provider prefix ("gemini/", "anthropic/", ...) is a native LiteLLM
        # provider that resolves its own credentials from the environment (e.g.
        # GEMINI_API_KEY for gemini/), so forcing OpenRouter's base_url/api_key
        # would break it. Leave both unset and let LiteLLM take the native route.
        if resolved_model.startswith("openrouter/"):
            api_key: str | None = os.getenv("OPENROUTER_API_KEY")
            base_url: str | None = "https://openrouter.ai/api/v1"
        else:
            api_key = None
            base_url = None

        # is_litellm=True forces routing through LiteLLM instead of CrewAI 1.15's
        # native OpenAICompatibleCompletion provider. The native provider sends
        # tool/response schemas with OpenAI strict-mode (`strict: true`) generated
        # from our Pydantic models, which are not strict-compliant (title/default/
        # anyOf, no additionalProperties:false). OpenRouter's upstream providers
        # then reject them: Mistral -> 400 "Invalid structured output syntax"
        # (code 3051); OpenAI -> "Invalid schema for function ...". LiteLLM sends
        # the same schemas without strict-mode, which every provider accepts.
        llm = LLM(
            model=resolved_model,
            is_litellm=True,
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
            max_tokens=tokens,
            reasoning_effort=effort,  # type: ignore[arg-type]
        )
        # Contract marker asserted by tests/crews/test_agent_llm_contract.py —
        # distinguishes LLMConfig-configured agents from CrewAI env-fallback LLMs.
        llm.configured_via_llmconfig = True
        return llm

    @staticmethod
    def get_timeout(task_type: str = "default") -> int:
        """Get timeout by task type (seconds).

        Returns appropriate timeout values for different task complexities:
        - quick: 120s - For simple tasks (cooking recipes, classification)
        - default: 300s - For standard tasks (research, analysis)
        - long: 600s - For complex tasks (deep research, comprehensive reports)

        Args:
            task_type: Type of task ("quick", "default", or "long").

        Returns:
            Timeout in seconds.

        Example:
            >>> quick_timeout = LLMConfig.get_timeout("quick")  # 120
            >>> default_timeout = LLMConfig.get_timeout()  # 300
            >>> long_timeout = LLMConfig.get_timeout("long")  # 600
        """
        timeouts = {
            "quick": int(os.getenv("LLM_TIMEOUT_QUICK", "120")),
            "default": int(os.getenv("LLM_TIMEOUT_DEFAULT", "300")),
            "long": int(os.getenv("LLM_TIMEOUT_LONG", "600")),
        }
        return timeouts.get(task_type, timeouts["default"])

    @staticmethod
    def get_max_iter() -> int:
        """Get max iterations for crew execution.

        Returns the maximum number of iterations a crew can perform before
        stopping. This prevents infinite loops while allowing complex tasks
        to iterate as needed.

        Returns:
            Maximum iterations (default: 5).

        Example:
            >>> max_iter = LLMConfig.get_max_iter()  # 5
        """
        return int(os.getenv("CREW_MAX_ITER", "5"))

    @staticmethod
    def get_max_rpm() -> int:
        """Get max requests per minute.

        Returns the maximum number of API requests allowed per minute.
        This helps manage rate limits and control costs.

        Returns:
            Maximum requests per minute (default: 20).

        Example:
            >>> max_rpm = LLMConfig.get_max_rpm()  # 20
        """
        return int(os.getenv("CREW_MAX_RPM", "20"))
