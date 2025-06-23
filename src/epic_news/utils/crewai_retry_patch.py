"""
CrewAI LLM retry integration.

This module patches the CrewAI framework to add retry capabilities for LLM calls,
addressing the "Invalid response from LLM call - None or empty" error without
changing model configurations.
"""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM

from epic_news.utils.llm_retry import get_llm_with_retries  # Adjusted import path
from epic_news.utils.logger import get_logger  # Adjusted import path

# Get logger for this module
logger = get_logger(__name__)

# Keep track of patched modules to avoid duplicate patching
_PATCHED = False


def patch_crewai_llm_initialization(max_retries: int = 5, verbose: bool = True) -> None:
    """
    Patch CrewAI to use LLM wrapper with retry capability.

    This function monkeypatches CrewAI's LLM initialization code to wrap
    all LLM instances with our retry logic. This ensures all LLM calls across
    the application get retry capabilities without changing model configurations.

    Args:
        max_retries: Maximum number of retry attempts for LLM calls
        verbose: Whether to log detailed retry information

    """
    global _PATCHED
    if _PATCHED:
        logger.info("CrewAI LLM initialization already patched with retry logic")
        return

    try:
        # Import CrewAI agent module - we'll patch its LLM handling
        from crewai.agents.agent import Agent as CrewAIAgent
        from crewai.llms.adapters.openai import OpenAIAdapter

        # Store original methods for patching
        original_get_llm = CrewAIAgent._get_llm
        original_get_model = None

        # Try to access OpenAI adapter's get_model method if it exists
        if hasattr(OpenAIAdapter, "get_model"):
            original_get_model = OpenAIAdapter.get_model

        logger.info(f"Patching CrewAI LLM initialization with {max_retries} max retries")

        # Patch the Agent._get_llm method to wrap LLMs with retry capability
        def patched_get_llm(agent_self) -> Any:
            """Patched version of _get_llm that adds retry capabilities."""
            # Get the original LLM
            llm = original_get_llm(agent_self)

            # Check if it's a langchain LLM that we can wrap
            if isinstance(llm, BaseLLM | BaseChatModel):
                logger.info(f"Adding retry wrapper to LLM: {type(llm).__name__}")
                return get_llm_with_retries(llm, max_retries=max_retries, verbose=verbose)
            return llm

        # Patch OpenAI adapter if applicable
        if original_get_model:

            def patched_get_model(adapter_self, *args: Any, **kwargs: Any) -> Any:
                """Patched version of get_model that adds retry capabilities."""
                # Get the original model
                model = original_get_model(adapter_self, *args, **kwargs)

                # Check if it's a langchain LLM that we can wrap
                if isinstance(model, BaseLLM | BaseChatModel):
                    logger.info(f"Adding retry wrapper to OpenAI model: {type(model).__name__}")
                    return get_llm_with_retries(model, max_retries=max_retries, verbose=verbose)
                return model

            # Apply the patch to OpenAI adapter
            OpenAIAdapter.get_model = patched_get_model

        # Apply the patch to CrewAI Agent
        CrewAIAgent._get_llm = patched_get_llm

        # Set patched flag
        _PATCHED = True
        logger.info("Successfully patched CrewAI LLM initialization with retry logic")

    except ImportError as e:
        logger.error(f"Failed to patch CrewAI - module not found: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to patch CrewAI with retry logic: {str(e)}")


def initialize_retry_mechanism(max_retries: int = 5, timeout: int = 180) -> None:
    """
    Initialize the LLM retry mechanism for epic_news.

    This function should be called early in the application startup
    to ensure all LLM calls have retry capabilities.

    Args:
        max_retries: Maximum number of retry attempts for LLM calls
        timeout: Timeout in seconds for LLM API calls (default: 180 seconds)

    """
    # Patch OpenAI client's default timeout settings
    try:
        import openai

        # Set longer default timeout for OpenAI client
        openai.timeout = timeout
        logger.info(f"Set OpenAI client timeout to {timeout} seconds")
    except ImportError:
        logger.warning("OpenAI client not found, skipping timeout setting")
    except Exception as e:
        logger.warning(f"Failed to set OpenAI timeout: {e}")

    # Patch HTTPX client timeout in CrewAI
    try:
        import httpx

        # Try to find and update timeout in any httpx clients used by CrewAI
        from crewai.llm import OpenAIChat

        if hasattr(OpenAIChat, "client") and hasattr(OpenAIChat.client, "timeout"):
            OpenAIChat.client.timeout = httpx.Timeout(timeout)
            logger.info(f"Set CrewAI OpenAIChat client timeout to {timeout} seconds")
    except ImportError:
        logger.warning("HTTPX or CrewAI OpenAIChat not found, skipping timeout setting")
    except Exception as e:
        logger.warning(f"Failed to set HTTPX timeout: {e}")

    logger.info(f"Initializing LLM retry mechanism with {max_retries} max retries")
    patch_crewai_llm_initialization(max_retries=max_retries, verbose=True)
    logger.info("LLM retry mechanism initialized successfully")
