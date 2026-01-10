"""Centralized LLM configuration for OpenRouter."""
import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


class LLMConfig:
    """Centralized LLM configuration using OpenRouter.

    This class provides a single source of truth for LLM configuration across
    all crews in the epic_news project. It uses OpenRouter as the primary LLM
    provider, allowing flexible model selection while maintaining cost efficiency.

    Environment Variables:
        MODEL: Model identifier (default: "openrouter/xiaomi/mimo-v2-flash:free")
        OPENROUTER_API_KEY: OpenRouter API key
        LLM_TEMPERATURE: Response randomness (0.0-2.0, default: 0.7)
        LLM_MAX_TOKENS: Maximum response tokens (optional)
        LLM_TIMEOUT_QUICK: Timeout for quick tasks (default: 120s)
        LLM_TIMEOUT_DEFAULT: Timeout for standard tasks (default: 300s)
        LLM_TIMEOUT_LONG: Timeout for complex tasks (default: 600s)
        CREW_MAX_ITER: Maximum iterations per crew (default: 5)
        CREW_MAX_RPM: Maximum requests per minute (default: 20)

    Usage:
        >>> from epic_news.config.llm_config import LLMConfig
        >>> llm = LLMConfig.get_openrouter_llm()
        >>> timeout = LLMConfig.get_timeout("long")
    """

    @staticmethod
    def get_openrouter_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatOpenAI:
        """Get ChatOpenAI instance configured for OpenRouter.

        This method creates a LangChain ChatOpenAI instance configured to use
        OpenRouter's API. It reads configuration from environment variables,
        with sensible defaults for missing values.

        Args:
            model: Model name (e.g., "openrouter/xiaomi/mimo-v2-flash:free").
                   If None, uses MODEL from .env.
            temperature: LLM temperature (0.0-2.0). Controls response randomness.
                        Lower values (0.0-0.3) are more deterministic.
                        Higher values (0.7-2.0) are more creative.
                        If None, uses LLM_TEMPERATURE from .env (default: 0.7).
            max_tokens: Maximum response tokens. Limits response length.
                       If None, uses LLM_MAX_TOKENS from .env (unlimited if not set).

        Returns:
            ChatOpenAI instance configured for OpenRouter API.

        Example:
            >>> # Use default configuration
            >>> llm = LLMConfig.get_openrouter_llm()
            >>>
            >>> # Override temperature for creative tasks
            >>> creative_llm = LLMConfig.get_openrouter_llm(temperature=1.2)
            >>>
            >>> # Use different model
            >>> opus_llm = LLMConfig.get_openrouter_llm(
            ...     model="openrouter/anthropic/claude-3.5-sonnet"
            ... )
        """
        # Get model from parameter or environment
        model_name = model or os.getenv("MODEL", "openrouter/xiaomi/mimo-v2-flash:free")

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

        return ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=temp,
            max_tokens=tokens,
        )

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
