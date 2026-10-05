"""Runtime patches to CrewAI 1.15.23's LLM classes, applied once by ``epic_news.main``.

What they do:
- Anthropic detection: OpenRouter model ids such as ``openrouter/anthropic/...`` are not
  sent down CrewAI's native Anthropic path (``_patch_anthropic_detection_for_openrouter``).
- ReAct tool calling: every ``BaseLLM`` subclass reports no native function calling, so
  agents use the ReAct text protocol; tool-call responses are coerced to ReAct text
  (``_force_react_tool_calling``, ``_wrap_call_for_react_safety``,
  ``_coerce_tool_calls_to_react_text``).
- Empty responses: an identical call that came back empty is re-issued with backoff
  (``LLM_EMPTY_RETRIES``, ``_call_with_empty_retry``).
- Concurrency: every LLM call holds one of ``LLM_MAX_CONCURRENCY`` process-wide slots,
  waiting at most ``LLM_SLOT_WAIT_SECONDS`` (``_with_llm_slot`` / ``_awith_llm_slot``).

Re-check on every CrewAI upgrade:
- ``crewai.LLM`` still has ``call``/``acall`` and the attribute
  ``_patch_anthropic_detection_for_openrouter`` replaces (see that function).
- ``BaseLLM.supports_function_calling`` still decides between native tools and ReAct.
- ``BaseLLM.__init_subclass__`` still runs for provider classes created at import time.
- The tests in ``tests/config/`` (tool calling, coercion, empty retry, concurrency cap)
  still pass against the new version.
"""

import asyncio
import contextvars
import json
import os
import random
import threading
import time
from collections.abc import Awaitable, Callable
from typing import Any

from crewai import LLM
from crewai.llms.base_llm import BaseLLM
from loguru import logger

# Re-issues of an identical call that came back empty (see _wrap_call_for_react_safety).
_DEFAULT_EMPTY_RETRIES = "2"
_EMPTY_RETRY_BASE_DELAY = 0.5
_EMPTY_RETRY_MAX_DELAY = 8.0

# Module-level so tests can replace them and never sleep for real.
_sleep = time.sleep
_async_sleep = asyncio.sleep

_llm_slots: threading.BoundedSemaphore | None = None
_llm_slots_lock = threading.Lock()
_holds_slot: contextvars.ContextVar[bool] = contextvars.ContextVar("llm_holds_slot", default=False)


def _llm_concurrency() -> int:
    """Max simultaneous LLM calls in this process (LLM_MAX_CONCURRENCY, default 3)."""
    try:
        return max(1, int(os.getenv("LLM_MAX_CONCURRENCY", "3")))
    except ValueError:
        return 3


def _slot_wait_seconds() -> float:
    """Longest wait for an LLM slot before running uncapped (LLM_SLOT_WAIT_SECONDS, default 120)."""
    try:
        return max(0.0, float(os.getenv("LLM_SLOT_WAIT_SECONDS", "120")))
    except ValueError:
        return 120.0


def _slots() -> threading.BoundedSemaphore:
    global _llm_slots
    with _llm_slots_lock:
        if _llm_slots is None:
            _llm_slots = threading.BoundedSemaphore(_llm_concurrency())
        return _llm_slots


def _reset_llm_slots() -> None:
    """Re-read LLM_MAX_CONCURRENCY on next use (tests only)."""
    global _llm_slots
    with _llm_slots_lock:
        _llm_slots = None


def _with_llm_slot[T](call_fn: Callable[[], T]) -> T:
    """Run one LLM call while holding a process-wide concurrency slot.

    CrewAI async tasks, the DOCX section pool, the menu recipe pool and the OSINT
    fan-out all start LLM calls in parallel; this is the single place that bounds them.
    Reentrant per logical call: crewai's LLM.call re-invokes itself (e.g. when the
    provider rejects ``stop``), and the nested call must not take a second slot.

    The cap is a soft limit, so it can never hang a run:

    * A thread running an event loop never waits: crewai's async executor can make a
      sync call on the loop thread (``summarize_messages`` on context overflow) while
      coroutines on that same loop hold every slot. The slot is taken only if one is
      free; otherwise the call runs uncapped, with a warning.
    * Other threads wait at most LLM_SLOT_WAIT_SECONDS (default 120), then run uncapped
      with a warning.

    An uncapped call still marks itself as holding a slot, so its nested calls do not
    wait again; it never releases a slot it did not take.
    """
    if _holds_slot.get():
        return call_fn()
    slots = _slots()
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        wait = _slot_wait_seconds()
        acquired = slots.acquire(timeout=wait)
        if not acquired:
            logger.warning(f"Waited {wait:g}s for an LLM slot; running this call uncapped")
    else:
        acquired = slots.acquire(blocking=False)
        if not acquired:
            logger.warning(
                "LLM slot busy on an event-loop thread; running this call uncapped to avoid a deadlock"
            )
    token = _holds_slot.set(True)
    try:
        return call_fn()
    finally:
        _holds_slot.reset(token)
        if acquired:
            slots.release()


async def _awith_llm_slot[T](call_fn: Callable[[], Awaitable[T]]) -> T:
    """Async twin of _with_llm_slot; waits for a slot without blocking the event loop.

    Polls a non-blocking acquire so a cancelled waiter can never leak a slot. Stops
    polling after LLM_SLOT_WAIT_SECONDS (default 120) and runs the call uncapped with a
    warning: a helper loop polling here may be what the slot holders are waiting on
    (crewai's multi-chunk ``summarize_messages`` blocks the loop thread on it).
    """
    if _holds_slot.get():
        return await call_fn()
    slots = _slots()
    wait = _slot_wait_seconds()
    deadline = time.monotonic() + wait
    acquired = slots.acquire(blocking=False)
    while not acquired and time.monotonic() < deadline:
        await asyncio.sleep(0.02)
        acquired = slots.acquire(blocking=False)
    if not acquired:
        logger.warning(f"Waited {wait:g}s for an LLM slot; running this call uncapped")
    token = _holds_slot.set(True)
    try:
        return await call_fn()
    finally:
        _holds_slot.reset(token)
        if acquired:
            slots.release()


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

    Crews started with ``akickoff`` (``akickoff_flow``: OSINT, RssWeekly) reach the
    provider through ``acall``, which returns empty content and raw tool calls exactly
    like the sync path does. Under the sync ``kickoff``, ``async_execution=True`` tasks
    run in CrewAI threads and use the sync ``call``.
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

    Both entry points are wrapped. Under the sync ``kickoff``, tasks with
    ``async_execution=True`` run in CrewAI threads (``Task.execute_async``) and use the
    sync ``call``. Crews started with ``akickoff`` reach the provider through ``acall``
    (``agent_utils.aget_llm_response``), which carries the identical
    ``if tool_calls and not available_functions: return tool_calls`` return as ``call``.

    Only classes that define their *own* ``call``/``acall`` are wrapped; inheritors reuse
    the wrapped parent, so nothing is ever double-wrapped. CrewAI deep-copies agent LLMs
    while assembling crews, so this must patch classes, never instances.
    """
    original_call = cls.__dict__.get("call")
    if original_call is not None and not getattr(original_call, "_epic_news_react_safe", False):

        def call(self, *args, **kwargs):
            result = _call_with_empty_retry(
                lambda: _with_llm_slot(lambda: original_call(self, *args, **kwargs)),
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
                lambda: _awith_llm_slot(lambda: original_acall(self, *args, **kwargs)),
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


def apply_crewai_patches() -> None:
    """Install every patch on CrewAI's LLM classes. Safe to call more than once."""
    _patch_anthropic_detection_for_openrouter()
    _force_react_tool_calling()
