import pytest
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import Generation, LLMResult

from epic_news.utils.llm_retry import RetryLLMWrapper, get_llm_with_retries


class MockLLM(BaseLLM):
    def _call(self, prompt: str, stop: list[str] | None = None, run_manager=None, **kwargs) -> str:
        return "test"

    def _generate(
        self, prompts: list[str], stop: list[str] | None = None, run_manager=None, **kwargs
    ) -> LLMResult:
        return LLMResult(generations=[[Generation(text="test")]])

    @property
    def _llm_type(self) -> str:
        return "mock"


class TestRetryLLMWrapper:
    def test_successful_call(self, mocker):
        mock_llm = MockLLM()
        mocker.patch.object(
            mock_llm,
            "_generate",
            return_value=LLMResult(generations=[[Generation(text="successful response")]]),
        )
        retry_wrapper = RetryLLMWrapper(llm=mock_llm)

        result = retry_wrapper._generate(["prompt"])

        assert result.generations[0][0].text == "successful response"
        mock_llm._generate.assert_called_once()

    def test_retry_on_exception(self, mocker):
        mock_llm = MockLLM()
        mocker.patch.object(
            mock_llm,
            "_generate",
            side_effect=[
                Exception("API error"),
                LLMResult(generations=[[Generation(text="successful response")]]),
            ],
        )
        retry_wrapper = RetryLLMWrapper(llm=mock_llm, max_retries=2)

        result = retry_wrapper._generate(["prompt"])

        assert result.generations[0][0].text == "successful response"
        assert mock_llm._generate.call_count == 2

    def test_exhaust_retries(self, mocker):
        mock_llm = MockLLM()
        mocker.patch.object(mock_llm, "_generate", side_effect=Exception("API error"))
        retry_wrapper = RetryLLMWrapper(llm=mock_llm, max_retries=3)

        with pytest.raises(Exception, match="API error"):
            retry_wrapper._generate(["prompt"])

        assert mock_llm._generate.call_count == 3


def test_get_llm_with_retries():
    mock_llm = MockLLM()
    wrapped_llm = get_llm_with_retries(mock_llm)

    assert isinstance(wrapped_llm, RetryLLMWrapper)
    assert wrapped_llm.llm == mock_llm
