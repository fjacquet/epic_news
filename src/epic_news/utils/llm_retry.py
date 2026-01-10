"""
LLM retry mechanism for CrewAI.

This module provides a custom LLM wrapper with retry logic to handle
temporary API issues, rate limiting, and other transient errors that
might cause "Invalid response from LLM call - None or empty" errors.
"""

import asyncio
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import LLMResult
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from epic_news.utils.logger import get_logger  # Adjusted import path

# Get logger for this module
logger = get_logger(__name__)


class RetryLLMWrapper(BaseLLM):
    """
    A wrapper for LLM models that adds retry capability.

    This wrapper intercepts LLM calls and adds exponential backoff retry
    logic to handle transient errors in API calls.
    """

    llm: BaseLLM
    max_retries: int = 3
    min_seconds: float = 1
    max_seconds: float = 60
    factor: float = 2
    verbose: bool = False

    def __init__(
        self,
        llm: BaseLLM,
        max_retries: int = 5,
        min_seconds: float = 1,
        max_seconds: float = 60,
        factor: float = 2,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the RetryLLMWrapper.

        Args:
            llm: The base LLM to wrap with retry logic
            max_retries: Maximum number of retry attempts
            min_seconds: Minimum backoff time in seconds
            max_seconds: Maximum backoff time in seconds
            factor: Backoff factor for exponential delay
            verbose: Whether to log detailed retry information
        """
        super().__init__(
            llm=llm,
            max_retries=max_retries,
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            factor=factor,
            verbose=verbose,
        )

    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return f"Retry{self.llm._llm_type}"

    def _generate(
        self,
        prompts: list[str],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Generate LLM result with retry capability.

        Args:
            prompts: List of prompts to send to the LLM
            stop: List of stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments to pass to the LLM

        Returns:
            LLMResult: The generated result from the LLM

        Raises:
            RetryError: When all retry attempts fail

        """
        attempt = 0
        last_exception = None

        # Create a retryer with exponential backoff
        retryer = Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.min_seconds, max=self.max_seconds),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )

        for attempt in retryer:  # type: ignore[assignment]
            with attempt:  # type: ignore[attr-defined]
                try:
                    if self.verbose and attempt.retry_state.attempt_number > 1:  # type: ignore[attr-defined]
                        logger.warning(
                            f"Retrying LLM call, attempt {attempt.retry_state.attempt_number}/{self.max_retries}"  # type: ignore[attr-defined]
                        )

                    # Call the underlying LLM
                    result = self.llm._generate(prompts, stop=stop, run_manager=run_manager, **kwargs)

                    # Check if result is empty or None
                    if not result or not result.generations or not result.generations[0]:
                        raise ValueError("Empty response from LLM call")

                    # Additional validation to check for empty content
                    for gen_list in result.generations:
                        if not gen_list or not gen_list[0].text or gen_list[0].text.strip() == "":
                            raise ValueError("Empty content in LLM response")

                    return result

                except Exception as e:
                    last_exception = e
                    logger.warning(f"LLM call failed with error: {str(e)}. Retrying...")
                    raise e

        # This code should not be reached due to reraise=True in Retrying
        logger.error(f"All {self.max_retries} LLM call attempts failed")
        if last_exception:
            raise last_exception
        raise RuntimeError("All LLM call attempts failed")

    async def _agenerate(  # type: ignore[override]
        self,
        prompts: list[str],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Generate LLM result with retry capability (async version).

        Args:
            prompts: List of prompts to send to the LLM
            stop: List of stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments to pass to the LLM

        Returns:
            LLMResult: The generated result from the LLM

        """
        # Implement async retry logic similar to the sync version
        attempt = 0
        while attempt < self.max_retries:
            try:
                if self.verbose and attempt > 0:
                    logger.warning(f"Retrying async LLM call, attempt {attempt + 1}/{self.max_retries}")

                # Call the underlying LLM
                result = await self.llm._agenerate(prompts, stop=stop, run_manager=run_manager, **kwargs)  # type: ignore[arg-type]

                # Check if result is empty or None
                if not result or not result.generations or not result.generations[0]:
                    raise ValueError("Empty response from async LLM call")

                # Additional validation to check for empty content
                for gen_list in result.generations:
                    if not gen_list or not gen_list[0].text or gen_list[0].text.strip() == "":
                        raise ValueError("Empty content in async LLM response")

                return result

            except Exception as e:
                logger.warning(f"Async LLM call failed with error: {str(e)}. Retrying...")
                attempt += 1
                if attempt >= self.max_retries:
                    logger.error(f"All {self.max_retries} async LLM call attempts failed")
                    raise

                # Exponential backoff
                wait_time = min(self.max_seconds, self.min_seconds * (self.factor**attempt))
                await asyncio.sleep(wait_time)

        raise RuntimeError("All async LLM call attempts failed")


def get_llm_with_retries(llm: BaseLLM, max_retries: int = 5, verbose: bool = False) -> BaseLLM:
    """
    Wrap an LLM with retry capabilities.

    Args:
        llm: The base LLM to wrap
        max_retries: Maximum number of retry attempts
        verbose: Whether to log detailed retry information

    Returns:
        BaseLLM: The wrapped LLM with retry capability

    """
    return RetryLLMWrapper(llm=llm, max_retries=max_retries, verbose=verbose)
