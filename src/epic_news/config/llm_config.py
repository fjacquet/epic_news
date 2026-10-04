"""Centralized LLM configuration (OpenRouter and native LiteLLM routes)."""

import asyncio
import json
import os
import random
import time
from typing import Any, Literal

from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

_DEFAULT_MODEL = "gemini/gemini-3.8-flash"
_DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# LiteLLM-level retries for transient provider errors (429 / 5xx), per completion call.
_LITELLM_NUM_RETRIES = 2

# Applied when LLM_REASONING_EFFORT is unset for Gemini 3: without it the API
# defaults to thinking level "high" (slow, token-hungry).
_GEMINI3_DEFAULT_REASONING_EFFORT = "medium"

# Re-issues of an identical call that came back empty (see _wrap_call_for_react_safety).
_DEFAULT_EMPTY_RETRIES = "2"
_EMPTY_RETRY_BASE_DELAY = 0.5
_EMPTY_RETRY_MAX_DELAY = 8.0

# Module-level so tests can replace them and never sleep for real.
_sleep = time.sleep
_async_sleep = asyncio.sleep


def _empty_retry_delay(attempt: int) -> float:
    """Backoff before retry ``attempt`` (1-based): exponential, capped, with jitter.

    Nominal delay is ``0.5s * 2**(attempt-1)`` capped at 8s; the actual delay is drawn
    uniformly from 50-100% of it so parallel agents don't retry in lockstep.
    """
    nominal = min(_EMPTY_RETRY_MAX_DELAY, _EMPTY_RETRY_BASE_DELAY * 2 ** (attempt - 1))
    return random.uniform(nominal / 2, nominal)  # noqa: S311 - jitter, not crypto


def _empty_retries_from_env() -> int:
    return int(os.getenv("LLM_EMPTY_RETRIES", _DEFAULT_EMPTY_RETRIES))


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

    Retries at most ``max_retries`` times, sleeping :func:`_empty_retry_delay` before
    each retry, then returns the last (possibly empty) result so the caller's normal
    empty-handling still applies. Extracted from the ``LLM.call`` patch so the retry
    loop is unit-testable without live calls.
    """
    result = call_fn()
    attempts = 0
    while attempts < max_retries and _is_empty_llm_response(result):
        attempts += 1
        delay = _empty_retry_delay(attempts)
        logger.warning(
            f"Empty response from LLM '{model}' (likely Gemini thought-only turn); "
            f"retrying {attempts}/{max_retries} in {delay:.2f}s"
        )
        _sleep(delay)
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
        delay = _empty_retry_delay(attempts)
        logger.warning(
            f"Empty response from async LLM '{model}' (likely Gemini thought-only turn); "
            f"retrying {attempts}/{max_retries} in {delay:.2f}s"
        )
        await _async_sleep(delay)
        result = await call_fn()
    return result


def _field(source: Any, key: str) -> Any:
    """Read ``key`` off an object attribute or a mapping entry, whichever applies."""
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _tool_call_name_and_arguments(tool_call: Any) -> tuple[str, str] | None:
    """Pull ``(name, arguments)`` out of one tool call, or ``None`` if it isn't one.

    Covers every shape CrewAI treats as a tool call in
    ``agent_utils._is_tool_call_list``, as objects or plain dicts:

    * OpenAI/litellm — ``.function.name`` / ``.function.arguments``
    * Gemini — ``.function_call.name`` / ``.function_call.args``
    * Anthropic, Bedrock — ``.name`` / ``.input``
    """
    for container_key in ("function", "function_call"):
        container = _field(tool_call, container_key)
        if container is None:
            continue
        name = _field(container, "name")
        arguments = _field(container, "arguments")
        if arguments is None:
            arguments = _field(container, "args")
        if name:
            return str(name), _stringify_arguments(arguments)

    name = _field(tool_call, "name")
    if name:
        return str(name), _stringify_arguments(_field(tool_call, "input"))

    return None


def _stringify_arguments(arguments: Any) -> str:
    """Render tool arguments as the JSON object the ReAct parser expects."""
    if arguments is None or arguments == "":
        return "{}"
    if isinstance(arguments, str):
        return arguments
    try:
        return json.dumps(arguments, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(arguments)


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

    Only the first call is converted — ReAct runs one action per step, so a parallel
    batch would be re-requested on the next turn anyway. A list whose first entry is no
    recognisable tool call yields ``None``; the caller stringifies it rather than letting
    a raw list escape (see :func:`_wrap_call_for_react_safety`).
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


def _react_safe_text(llm: object, result: Any) -> Any:
    """Return ``result`` as something a ReAct consumer can handle — never a raw list.

    A ``str`` (the normal case) passes through untouched. A tool-call list becomes ReAct
    text. Anything else that is still a ``list`` is stringified as a last resort: garbled
    output beats ``ValidationError`` on ``TaskOutput.raw``, which aborts the whole crew.
    Both non-``str`` outcomes are logged with the offending class so the next occurrence
    identifies itself.
    """
    model = getattr(llm, "model", "?")
    react_text = _coerce_tool_calls_to_react_text(result)

    if react_text is not None:
        action_line = next(
            (line for line in react_text.splitlines() if line.startswith("Action:")), react_text
        )
        dropped = len(result) - 1 if isinstance(result, list) else 0
        extra = f" Dropped {dropped} further tool call(s) in the same response." if dropped else ""
        logger.warning(
            f"LLM '{model}' ({type(llm).__name__}) returned native tool calls on a ReAct step; "
            f"coercing to Thought/Action text to keep TaskOutput.raw a string. "
            f"Coerced: {action_line}.{extra}"
        )
        return react_text

    if isinstance(result, list):
        logger.error(
            f"LLM '{model}' ({type(llm).__name__}) returned a list that is not a recognisable "
            f"tool call: {result!r}. Stringifying it so TaskOutput.raw stays a string."
        )
        return str(result)

    return result


def _wrap_call_for_react_safety(cls: type) -> None:
    """Wrap ``cls.call``/``cls.acall`` with empty-retry + tool-call coercion, in place.

    Two provider misbehaviours are absorbed here, both observed on
    ``gemini/gemini-3.7-flash`` and both fatal to a whole crew run:

    *Empty responses.* Gemini intermittently returns a *thought-only* response on ReAct
    steps: the generated tokens land in a thinking block carrying a ``thought_signature``
    and ``message.content`` comes back ``None`` (``finish_reason`` is still ``stop``, so
    it is not a length cut-off). CrewAI's ``_validate_and_finalize_llm_response`` rejects
    it with ``ValueError: Invalid response from LLM call - None or empty``. The empties
    are stochastic (~40-60% per call on the worst prompts) and, counter-intuitively, get
    worse with thinking disabled — so re-issuing the identical call usually yields text.
    Retries back off exponentially with jitter (0.5s base, 8s cap). Tune the ceiling with
    ``LLM_EMPTY_RETRIES`` (default 2); 0 disables it.

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
            result = _call_with_empty_retry(
                lambda: original_call(self, *args, **kwargs),
                _empty_retries_from_env(),
                getattr(self, "model", "?"),
            )
            return _react_safe_text(self, result)

        call._epic_news_react_safe = True  # type: ignore[attr-defined]
        cls.call = call  # type: ignore[attr-defined]

    original_acall = cls.__dict__.get("acall")
    if original_acall is not None and not getattr(original_acall, "_epic_news_react_safe", False):

        async def acall(self, *args, **kwargs):
            result = await _acall_with_empty_retry(
                lambda: original_acall(self, *args, **kwargs),
                _empty_retries_from_env(),
                getattr(self, "model", "?"),
            )
            return _react_safe_text(self, result)

        acall._epic_news_react_safe = True  # type: ignore[attr-defined]
        cls.acall = acall  # type: ignore[attr-defined]


def _apply_react_patches(cls: type) -> None:
    """Apply both ReAct defences to one LLM class."""
    cls.supports_function_calling = _react_only_supports_function_calling  # type: ignore[attr-defined]
    _wrap_call_for_react_safety(cls)


def _apply_react_patches_to_tree(cls: type) -> None:
    """Apply the ReAct defences to ``cls`` and every subclass already imported."""
    _apply_react_patches(cls)
    subclass: type
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
    """Centralized LLM configuration: OpenRouter or a native LiteLLM provider route.

    Single source of truth for LLM configuration across all crews in epic_news.
    ``MODEL`` picks the route: ``openrouter/...`` goes through OpenRouter's
    OpenAI-compatible endpoint; any other LiteLLM prefix (``gemini/``,
    ``vertex_ai/``, ``anthropic/``, ...) uses that provider natively.

    Environment Variables:
        MODEL: Model identifier (default: "gemini/gemini-3.8-flash")
        OPENROUTER_API_KEY: OpenRouter API key (openrouter/ route only)
        OPENROUTER_BASE_URL: OpenRouter endpoint (default: https://openrouter.ai/api/v1)
        LLM_TEMPERATURE: Response randomness (0.0-2.0, default: 0.7; never applied
            to Gemini models, which should keep their default of 1.0)
        LLM_MAX_TOKENS: Maximum response tokens (optional)
        LLM_REASONING_EFFORT: none/minimal/low/medium/high. Opt-in, except for
            Gemini 3 models where it defaults to "medium"
        LLM_TIMEOUT_QUICK: Timeout for quick tasks (default: 120s)
        LLM_TIMEOUT_DEFAULT: Timeout for standard tasks (default: 300s)
        LLM_TIMEOUT_LONG: Timeout for complex tasks (default: 600s)
        LLM_EMPTY_RETRIES: Re-issues of a call that returned empty text (default: 2)
        CREW_MAX_ITER: Maximum iterations per crew (default: 5)
        CREW_MAX_RPM: Maximum requests per minute (default: 20)

    Usage:
        >>> from epic_news.config.llm_config import LLMConfig
        >>> llm = LLMConfig.get_openrouter_llm()
        >>> slow_llm = LLMConfig.get_openrouter_llm(task_type="long")
    """

    @staticmethod
    def get_openrouter_llm(
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        reasoning_effort: str | None = None,
        task_type: Literal["quick", "default", "long"] = "default",
    ) -> LLM:
        """Build the CrewAI LLM every agent should use.

        Despite the historical name this is route-aware: OpenRouter transport is
        applied only to ``openrouter/`` models (see class docstring).

        Args:
            model: Model name (e.g., "gemini/gemini-3.8-flash" or "openrouter/mistralai/mistral-small-2603").
                   If None, uses MODEL from .env.
            temperature: LLM temperature (0.0-2.0). If None, uses LLM_TEMPERATURE
                        from .env (default: 0.7) — except for Gemini models on any
                        route, where the env default is not sent (Gemini 3 should
                        run at its default 1.0). An explicit value is always sent.
            max_tokens: Maximum response tokens. If None, uses LLM_MAX_TOKENS
                       from .env (unlimited if not set).
            reasoning_effort: "none", "minimal", "low", "medium" or "high". If None,
                             reads LLM_REASONING_EFFORT from .env. When unset/empty,
                             Gemini 3 models default to "medium" (LiteLLM maps it
                             to thinking_level); other models send nothing. "none"
                             sends nothing, except on Gemini 3 where it is sent
                             (LiteLLM maps it to the lowest thinking level; leaving
                             it out would mean the API default "high").
                             On ``openrouter/`` models it is sent as
                             ``extra_body={"reasoning": {"effort": ...}}``: LiteLLM
                             drops a top-level ``reasoning_effort`` for OpenRouter
                             models it doesn't know to support reasoning.
            task_type: Per-call request timeout tier, see :meth:`get_timeout`.

        Returns:
            CrewAI LLM instance (always LiteLLM-backed).

        Example:
            >>> llm = LLMConfig.get_openrouter_llm()
            >>> creative_llm = LLMConfig.get_openrouter_llm(temperature=1.2)
            >>> research_llm = LLMConfig.get_openrouter_llm(task_type="long")
        """
        resolved_model = model or os.getenv("MODEL") or _DEFAULT_MODEL
        model_lower = resolved_model.lower()
        is_openrouter = model_lower.startswith("openrouter/")
        is_gemini = "gemini" in model_lower
        is_gemini3 = "gemini-3" in model_lower  # same test LiteLLM uses

        # Gemini 3+ deprecates temperature/top_p/top_k and LiteLLM recommends keeping
        # the default 1.0. Drop the env-derived default on every route
        # (gemini/, vertex_ai/, openrouter/google/); an explicit caller value is kept.
        temp = temperature
        if temp is None and not is_gemini:
            temp = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        tokens = max_tokens
        if tokens is None:
            max_tokens_str = os.getenv("LLM_MAX_TOKENS")
            if max_tokens_str is not None and max_tokens_str.strip():
                tokens = int(max_tokens_str)

        # Normalize the value itself: LiteLLM validates against a lowercase Literal,
        # so "LOW"/" Low " must become "low", and "" must become None.
        effort: str | None = reasoning_effort
        if effort is None:
            effort = os.getenv("LLM_REASONING_EFFORT", "")
        effort = effort.strip().lower()
        if not effort:
            effort = _GEMINI3_DEFAULT_REASONING_EFFORT if is_gemini3 else None
        elif effort == "none" and not is_gemini3:
            effort = None

        # Route-aware transport. Only "openrouter/"-prefixed models go through
        # OpenRouter's OpenAI-compatible endpoint (api_key + base_url below). Every
        # other provider prefix ("gemini/", "anthropic/", ...) is a native LiteLLM
        # provider that resolves its own credentials from the environment (e.g.
        # GEMINI_API_KEY for gemini/), so forcing OpenRouter's base_url/api_key
        # would break it. Leave both unset and let LiteLLM take the native route.
        # Keys CrewAI's LLM does not declare land in ``additional_params`` and are
        # forwarded verbatim to litellm.completion (crewai LLM._prepare_completion_params).
        extra: dict[str, Any] = {"num_retries": _LITELLM_NUM_RETRIES}
        if is_openrouter:
            api_key: str | None = os.getenv("OPENROUTER_API_KEY")
            base_url: str | None = os.getenv("OPENROUTER_BASE_URL") or _DEFAULT_OPENROUTER_BASE_URL
            if effort is not None:
                extra["extra_body"] = {"reasoning": {"effort": effort}}
                effort = None
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
            timeout=LLMConfig.get_timeout(task_type),
            **extra,
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
