"""Centralized LLM configuration for OpenRouter."""

import os
from typing import Any

from crewai import LLM
from crewai.llms.base_llm import BaseLLM
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


async def _acall_with_empty_retry(call_fn, max_retries: int, model: str = "?"):
    """Async twin of :func:`_call_with_empty_retry` for ``BaseLLM.acall``.

    Tasks declared with ``async_execution=True`` reach the provider through ``acall``,
    which returns empty content and raw tool calls exactly like the sync path does.
    """
    result = await call_fn()
    attempts = 0
    while attempts < max_retries and _is_empty_llm_response(result):
        attempts += 1
        logger.warning(
            f"Empty response from async LLM '{model}' (likely Gemini thought-only turn); "
            f"retrying {attempts}/{max_retries}"
        )
        result = await call_fn()
    return result


def _tool_call_name_and_arguments(tool_call: Any) -> tuple[str, str] | None:
    """Pull ``(name, arguments)`` out of one tool call, or ``None`` if it isn't one.

    Accepts both shapes CrewAI can hand back: litellm's
    ``ChatCompletionMessageToolCall`` objects and the plain dicts some providers emit.
    """
    function = getattr(tool_call, "function", None)
    if function is None and isinstance(tool_call, dict):
        function = tool_call.get("function")
    if function is None:
        return None

    if isinstance(function, dict):
        name = function.get("name")
        arguments = function.get("arguments")
    else:
        name = getattr(function, "name", None)
        arguments = getattr(function, "arguments", None)

    if not name:
        return None
    return str(name), str(arguments) if arguments else "{}"


def _coerce_tool_calls_to_react_text(result: Any) -> str | None:
    """Render a provider's ``tool_calls`` list as ReAct text, or ``None`` if not applicable.

    ``crewai.llm.LLM.call`` returns the raw ``tool_calls`` list whenever the provider
    emits function calls and no ``available_functions`` were supplied::

        if tool_calls and not available_functions:
            return tool_calls

    Every ReAct consumer downstream assumes a ``str``. ``agent_utils.format_answer()``
    calls ``parse()``, which raises on a list, and the except-branch stores the list in
    ``AgentFinish.output``. That reaches ``TaskOutput.raw`` — a ``str`` field — and the
    crew dies with ``ValidationError: Input should be a valid string [input_value=
    [ChatCompletionMessageToolCall...]]``. Observed with ``gemini/gemini-3.5-flash``,
    whose tool-call ids carry a base64 ``thoughtSignature`` suffix.

    Translating the call into the Thought/Action/Action Input the ReAct loop expects
    keeps the model's actual intent: it asked for a tool, so let the loop run that tool
    instead of crashing the whole crew.
    """
    if not isinstance(result, list) or not result:
        return None

    parsed = _tool_call_name_and_arguments(result[0])
    if parsed is None:
        return None

    name, arguments = parsed
    return f"Thought: I need to use the {name} tool.\nAction: {name}\nAction Input: {arguments}"


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


def _react_only_supports_function_calling(self: BaseLLM) -> bool:
    """Replacement for every provider's ``supports_function_calling``: always ReAct."""
    return False


def _log_tool_call_coercion(llm: object, model: str, react_text: str) -> None:
    """Report a coerced native tool call loudly enough to identify the culprit class."""
    action_line = next((line for line in react_text.splitlines() if line.startswith("Action:")), react_text)
    logger.warning(
        f"LLM '{model}' ({type(llm).__name__}) returned native tool calls on a ReAct step; "
        f"coercing to Thought/Action text to keep TaskOutput.raw a string. "
        f"Coerced: {action_line}"
    )


def _wrap_call_for_react_safety(cls: type) -> None:
    """Wrap ``cls.call``/``cls.acall`` with empty-retry + tool-call coercion, in place.

    Two provider misbehaviours are absorbed here, both observed on
    ``gemini/gemini-3.5-flash`` and both fatal to a whole crew run:

    *Empty responses.* Gemini intermittently returns a *thought-only* response on ReAct
    steps: the generated tokens land in a thinking block carrying a ``thought_signature``
    and ``message.content`` comes back ``None`` (``finish_reason`` is still ``stop``, so
    it is not a length cut-off). CrewAI's ``_validate_and_finalize_llm_response`` rejects
    it with ``ValueError: Invalid response from LLM call - None or empty``. The empties
    are stochastic (~40-60% per call on the worst prompts) and, counter-intuitively, get
    worse with thinking disabled — so re-issuing the identical call a handful of times
    reliably yields text. Tune the ceiling with ``LLM_EMPTY_RETRIES`` (default 6); 0
    disables it.

    *Native tool calls on a ReAct step.* See ``_coerce_tool_calls_to_react_text``.

    Both entry points are wrapped: tasks with ``async_execution=True`` reach the provider
    through ``acall`` (``agent_utils.aget_llm_response``), which carries the identical
    ``if tool_calls and not available_functions: return tool_calls`` return as ``call``.

    Only classes that define their *own* ``call``/``acall`` are wrapped; inheritors reuse
    the wrapped parent, so nothing is ever double-wrapped. CrewAI deep-copies agent LLMs
    while assembling crews, so this must patch classes, never instances.
    """
    original_call = cls.__dict__.get("call")
    if original_call is not None and not getattr(original_call, "_epic_news_react_safe", False):

        def call(self, *args, **kwargs):
            model = getattr(self, "model", "?")
            max_retries = int(os.getenv("LLM_EMPTY_RETRIES", "6"))
            result = _call_with_empty_retry(
                lambda: original_call(self, *args, **kwargs),
                max_retries,
                model,
            )
            react_text = _coerce_tool_calls_to_react_text(result)
            if react_text is None:
                return result
            _log_tool_call_coercion(self, model, react_text)
            return react_text

        call._epic_news_react_safe = True  # type: ignore[attr-defined]
        cls.call = call  # type: ignore[attr-defined]

    original_acall = cls.__dict__.get("acall")
    if original_acall is not None and not getattr(original_acall, "_epic_news_react_safe", False):

        async def acall(self, *args, **kwargs):
            model = getattr(self, "model", "?")
            max_retries = int(os.getenv("LLM_EMPTY_RETRIES", "6"))
            result = await _acall_with_empty_retry(
                lambda: original_acall(self, *args, **kwargs),
                max_retries,
                model,
            )
            react_text = _coerce_tool_calls_to_react_text(result)
            if react_text is None:
                return result
            _log_tool_call_coercion(self, model, react_text)
            return react_text

        acall._epic_news_react_safe = True  # type: ignore[attr-defined]
        cls.acall = acall  # type: ignore[attr-defined]


def _apply_react_patches(cls: type) -> None:
    """Apply both ReAct defences to one LLM class."""
    cls.supports_function_calling = _react_only_supports_function_calling  # type: ignore[attr-defined]
    _wrap_call_for_react_safety(cls)


def _apply_react_patches_to_tree(cls: type) -> None:
    """Apply the ReAct defences to ``cls`` and every subclass already imported."""
    _apply_react_patches(cls)
    for subclass in cls.__subclasses__():
        _apply_react_patches_to_tree(subclass)


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

    Patching ``crewai.llm.LLM`` alone is not enough. ``LLM(model=...)`` without
    ``is_litellm=True`` — and ``crewai.utilities.llm_utils.create_llm``, which CrewAI
    uses for env-configured agents and internal helpers — returns a *native provider*
    class instead (``GeminiCompletion``, ``AnthropicCompletion``, ...), and each of
    those overrides ``supports_function_calling`` with a True-returning version. So the
    whole ``BaseLLM`` tree is patched, plus an ``__init_subclass__`` hook for provider
    classes imported lazily after this module loads.
    """
    if getattr(BaseLLM, "_react_tool_calling_forced", False):
        return

    _apply_react_patches_to_tree(BaseLLM)

    original_init_subclass = BaseLLM.__dict__.get("__init_subclass__")

    def patch_new_subclass(cls, **kwargs):
        """Re-apply the ReAct defences to provider classes imported after this module."""
        if original_init_subclass is not None:
            original_init_subclass.__func__(cls, **kwargs)
        else:
            super(BaseLLM, cls).__init_subclass__(**kwargs)
        _apply_react_patches(cls)

    BaseLLM.__init_subclass__ = classmethod(patch_new_subclass)  # type: ignore[assignment]
    BaseLLM._react_tool_calling_forced = True  # type: ignore[attr-defined]
    LLM._react_tool_calling_forced = True  # type: ignore[attr-defined]
    # The call wrapper is installed by the same sweep; keep the historical flag truthful.
    BaseLLM._retry_on_empty_patched = True  # type: ignore[attr-defined]
    LLM._retry_on_empty_patched = True  # type: ignore[attr-defined]


_patch_anthropic_detection_for_openrouter()
_force_react_tool_calling()


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
