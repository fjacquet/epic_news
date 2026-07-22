"""Native tool-call responses must never reach CrewAI's ReAct pipeline as objects.

CrewAI's LLM.call returns the provider's raw ``tool_calls`` list when no
``available_functions`` were supplied (crewai/llm.py: ``if tool_calls and not
available_functions: return tool_calls``). Every ReAct consumer downstream assumes a
``str``: ``agent_utils.format_answer()`` calls ``parse()``, the parse raises on a
non-str, and the fallback stuffs the list into ``AgentFinish.output`` -> ``TaskOutput.raw``
(a ``str`` field) -> ``ValidationError: Input should be a valid string``, killing the crew.

Two defences, both exercised here without any live LLM call:
1. ``supports_function_calling()`` is forced False on *every* BaseLLM subclass, not just
   ``crewai.llm.LLM`` — native provider classes (GeminiCompletion, ...) override it.
2. If a provider returns tool calls anyway, they are coerced into ReAct text so the
   agent loop can execute the tool instead of crashing.
"""

import asyncio
from types import SimpleNamespace

from crewai import LLM
from crewai.llms.base_llm import BaseLLM

from epic_news.config.llm_config import _coerce_tool_calls_to_react_text


def _tool_call(name: str, arguments: str, call_id: str = "call_1"):
    """Shape of litellm's ChatCompletionMessageToolCall (only the fields we read)."""
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class TestCoercion:
    def test_object_tool_call_becomes_react_text(self):
        result = _coerce_tool_calls_to_react_text(
            [_tool_call("perplexity_search", '{"query": "hotels Edinburgh"}')]
        )
        assert result is not None
        assert "Action: perplexity_search" in result
        assert 'Action Input: {"query": "hotels Edinburgh"}' in result
        assert result.startswith("Thought:")

    def test_dict_tool_call_becomes_react_text(self):
        result = _coerce_tool_calls_to_react_text(
            [{"function": {"name": "scrape_website", "arguments": '{"url": "x"}'}}]
        )
        assert result is not None
        assert "Action: scrape_website" in result

    def test_missing_arguments_defaults_to_empty_object(self):
        result = _coerce_tool_calls_to_react_text([_tool_call("exchange_rate", "")])
        assert "Action Input: {}" in result

    def test_gemini_function_call_shape(self):
        # Gemini-style parts carry function_call.name / .args (a dict, not a JSON string).
        result = _coerce_tool_calls_to_react_text(
            [SimpleNamespace(function_call=SimpleNamespace(name="wikipedia", args={"q": "Édimbourg"}))]
        )
        assert "Action: wikipedia" in result
        assert '"q": "Édimbourg"' in result

    def test_anthropic_name_input_shape(self):
        # Anthropic/Bedrock tool use blocks expose name/input directly.
        result = _coerce_tool_calls_to_react_text([{"name": "scrape_website", "input": {"url": "x"}}])
        assert "Action: scrape_website" in result
        assert 'Action Input: {"url": "x"}' in result

    def test_first_call_wins_for_parallel_calls(self):
        result = _coerce_tool_calls_to_react_text(
            [_tool_call("first_tool", "{}"), _tool_call("second_tool", "{}")]
        )
        assert "Action: first_tool" in result
        assert "second_tool" not in result

    def test_plain_string_is_not_coerced(self):
        assert _coerce_tool_calls_to_react_text("Final Answer: done") is None

    def test_empty_list_is_not_coerced(self):
        assert _coerce_tool_calls_to_react_text([]) is None

    def test_unrecognised_list_is_not_coerced(self):
        assert _coerce_tool_calls_to_react_text(["just a string"]) is None


class TestReactForcing:
    def test_litellm_class_forced(self):
        assert LLM.supports_function_calling(None) is False

    def test_native_provider_class_forced(self):
        # Gemini is the provider this project runs natively (crewai[google-genai]); the
        # other provider classes need extras that are not installed. Its completion class
        # overrides supports_function_calling with a True-returning implementation, so
        # patching only crewai.llm.LLM leaves the hole open.
        from crewai.llms.providers.gemini.completion import GeminiCompletion

        assert GeminiCompletion.supports_function_calling(None) is False

    def test_subclass_defined_after_patch_is_forced(self):
        class _LateProvider(BaseLLM):
            def call(self, messages, **kwargs):  # pragma: no cover - never invoked
                return "unused"

            def supports_function_calling(self) -> bool:
                return True

        assert _LateProvider(model="late/model").supports_function_calling() is False


class TestCallWrapper:
    def test_call_returning_tool_calls_is_coerced_to_text(self):
        class _ToolCallingProvider(BaseLLM):
            def call(self, messages, **kwargs):
                return [_tool_call("perplexity_search", '{"query": "q"}')]

        answer = _ToolCallingProvider(model="fake/model").call([{"role": "user", "content": "hi"}])

        assert isinstance(answer, str)
        assert "Action: perplexity_search" in answer

    def test_call_returning_text_is_untouched(self):
        class _TextProvider(BaseLLM):
            def call(self, messages, **kwargs):
                return "Final Answer: 42"

        assert _TextProvider(model="fake/model").call([]) == "Final Answer: 42"

    def test_unrecognised_list_is_stringified_never_returned_raw(self):
        # A list of any shape reaching TaskOutput.raw is fatal; garbled text is not.
        class _WeirdListProvider(BaseLLM):
            def call(self, messages, **kwargs):
                return [object()]

        answer = _WeirdListProvider(model="fake/model").call([])

        assert isinstance(answer, str)


class TestAsyncCallWrapper:
    """Tasks with async_execution=True go through ``acall``, which has the same
    ``if tool_calls and not available_functions: return tool_calls`` return."""

    def test_acall_returning_tool_calls_is_coerced_to_text(self):
        class _AsyncToolCallingProvider(BaseLLM):
            def call(self, messages, **kwargs):  # pragma: no cover - abstract stand-in
                return "unused"

            async def acall(self, messages, **kwargs):
                return [_tool_call("hybrid_search", '{"query": "q"}')]

        provider = _AsyncToolCallingProvider(model="fake/model")
        answer = asyncio.run(provider.acall([{"role": "user", "content": "hi"}]))

        assert isinstance(answer, str)
        assert "Action: hybrid_search" in answer

    def test_acall_retries_empty_responses(self, monkeypatch):
        monkeypatch.setenv("LLM_EMPTY_RETRIES", "3")
        seen = {"n": 0}

        class _FlakyAsyncProvider(BaseLLM):
            def call(self, messages, **kwargs):  # pragma: no cover - abstract stand-in
                return "unused"

            async def acall(self, messages, **kwargs):
                seen["n"] += 1
                return "" if seen["n"] < 3 else "Final Answer: ok"

        answer = asyncio.run(_FlakyAsyncProvider(model="fake/model").acall([]))

        assert answer == "Final Answer: ok"
        assert seen["n"] == 3

    def test_acall_returning_text_is_untouched(self):
        class _AsyncTextProvider(BaseLLM):
            def call(self, messages, **kwargs):  # pragma: no cover - abstract stand-in
                return "unused"

            async def acall(self, messages, **kwargs):
                return "Final Answer: 42"

        assert asyncio.run(_AsyncTextProvider(model="fake/model").acall([])) == "Final Answer: 42"
