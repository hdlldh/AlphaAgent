"""
LLM client abstraction for multi-provider support.

Provides a unified interface for:
- Anthropic Claude
- OpenAI GPT
- Google Gemini

All clients implement the LLMClient abstract base class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from stock_analyzer.exceptions import AnalysisError
from stock_analyzer.logging import get_logger
from stock_analyzer.models import AnalysisResponse, StockData
from stock_analyzer.retry import retry_with_backoff

logger = get_logger(__name__)


class LLMClient(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must implement:
    - analyze(): Generate stock analysis
    - count_tokens(): Count tokens in text
    """

    @abstractmethod
    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResponse:
        """
        Generate stock analysis using LLM.

        Args:
            prompt: User prompt for analysis
            stock_data: Stock market data to analyze
            system_prompt: Optional system prompt for context

        Returns:
            AnalysisResponse with generated text, tokens used, and metadata

        Raises:
            AnalysisError: If analysis fails
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass


class ClaudeLLMClient(LLMClient):
    """
    Anthropic Claude LLM client.

    Supports prompt caching for cost optimization.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        enable_caching: bool = True,
        max_tokens: int = 2048,
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-sonnet-4-5-20250929)
            enable_caching: Enable prompt caching (90% cost reduction)
            max_tokens: Maximum output tokens
        """
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.enable_caching = enable_caching
        self.max_tokens = max_tokens

    @retry_with_backoff(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        exceptions=(Exception,),
    )
    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResponse:
        """
        Analyze stock using Claude.

        Uses prompt caching if enabled to reduce costs on repeated system prompts.
        """
        logger.debug(f"Requesting Claude analysis for {stock_data.symbol}")
        try:
            messages = [{"role": "user", "content": prompt}]

            # Build system messages with optional caching
            system = []
            if system_prompt:
                system_msg = {
                    "type": "text",
                    "text": system_prompt,
                }
                # Add cache control for cost optimization
                if self.enable_caching:
                    system_msg["cache_control"] = {"type": "ephemeral"}
                system.append(system_msg)

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system if system else None,
                messages=messages,
            )

            logger.debug(
                f"Claude analysis complete for {stock_data.symbol}: "
                f"{response.usage.input_tokens} input + {response.usage.output_tokens} output tokens"
            )

            return AnalysisResponse(
                text=response.content[0].text,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                model=self.model,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "cached": hasattr(response.usage, "cache_read_input_tokens"),
                },
            )

        except Exception as e:
            logger.error(f"Claude API error for {stock_data.symbol}: {type(e).__name__}: {e}")
            raise AnalysisError(
                stock_data.symbol,
                f"Claude API error: {str(e)}",
                self.model,
            )

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens using Claude's tokenizer.

        Note: Anthropic doesn't provide a direct token counting API,
        so this uses approximation (4 chars ≈ 1 token).
        """
        # Rough approximation: 4 characters ≈ 1 token
        return len(text) // 4


class OpenAILLMClient(LLMClient):
    """
    OpenAI GPT LLM client.

    Supports GPT-4o, GPT-4 Turbo, and other OpenAI models.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum output tokens
        """
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @retry_with_backoff(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        exceptions=(Exception,),
    )
    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResponse:
        """
        Analyze stock using OpenAI GPT.
        """
        logger.debug(f"Requesting OpenAI analysis for {stock_data.symbol}")
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            logger.debug(
                f"OpenAI analysis complete for {stock_data.symbol}: "
                f"{response.usage.total_tokens} tokens"
            )

            return AnalysisResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=self.model,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "finish_reason": response.choices[0].finish_reason,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI API error for {stock_data.symbol}: {type(e).__name__}: {e}")
            raise AnalysisError(
                stock_data.symbol,
                f"OpenAI API error: {str(e)}",
                self.model,
            )

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens using approximation.

        OpenAI doesn't provide async token counting, so using approximation.
        """
        # Rough approximation: 4 characters ≈ 1 token
        return len(text) // 4


class GeminiLLMClient(LLMClient):
    """
    Google Gemini LLM client.

    Supports Gemini 2.5 Pro and Flash models.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro",
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
            model: Model name (default: gemini-2.5-pro)
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum output tokens
        """
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    @retry_with_backoff(
        max_attempts=3,
        base_delay=2.0,
        max_delay=30.0,
        exceptions=(Exception,),
    )
    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResponse:
        """
        Analyze stock using Google Gemini.

        Note: Gemini doesn't have separate system/user messages,
        so system prompt is prepended to user prompt.
        """
        logger.debug(f"Requesting Gemini analysis for {stock_data.symbol}")
        try:
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = await self.model.generate_content_async(
                full_prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                },
            )

            logger.debug(
                f"Gemini analysis complete for {stock_data.symbol}: "
                f"{response.usage_metadata.total_token_count} tokens"
            )

            return AnalysisResponse(
                text=response.text,
                tokens_used=response.usage_metadata.total_token_count,
                model=self.model.model_name,
                metadata={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "candidates_tokens": response.usage_metadata.candidates_token_count,
                },
            )

        except Exception as e:
            logger.error(f"Gemini API error for {stock_data.symbol}: {type(e).__name__}: {e}")
            raise AnalysisError(
                stock_data.symbol,
                f"Gemini API error: {str(e)}",
                self.model.model_name,
            )

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens using approximation.
        """
        # Rough approximation: 4 characters ≈ 1 token
        return len(text) // 4


class LLMClientFactory:
    """
    Factory for creating LLM clients.

    Supports:
    - anthropic: ClaudeLLMClient
    - openai: OpenAILLMClient
    - gemini: GeminiLLMClient
    """

    # Default models for each provider
    DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-5-20250929",
        "openai": "gpt-4o",
        "gemini": "gemini-2.5-pro",
    }

    @staticmethod
    def create(
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMClient:
        """
        Create LLM client for specified provider.

        Args:
            provider: "anthropic", "openai", or "gemini" (case-insensitive)
            api_key: API key for the provider
            model: Model name (uses default if not specified)
            **kwargs: Provider-specific configuration

        Returns:
            LLMClient instance

        Raises:
            ValueError: Unknown provider

        Examples:
            >>> # Create Claude client
            >>> client = LLMClientFactory.create(
            ...     provider="anthropic",
            ...     api_key="sk-ant-...",
            ...     model="claude-sonnet-4-5",
            ...     enable_caching=True
            ... )

            >>> # Create OpenAI client
            >>> client = LLMClientFactory.create(
            ...     provider="openai",
            ...     api_key="sk-...",
            ...     temperature=0.8
            ... )

            >>> # Create Gemini client
            >>> client = LLMClientFactory.create(
            ...     provider="gemini",
            ...     api_key="...",
            ...     model="gemini-2.5-flash"
            ... )
        """
        provider = provider.lower()

        # Get default model if not specified
        if model is None:
            model = LLMClientFactory.DEFAULT_MODELS.get(provider)

        if provider == "anthropic":
            return ClaudeLLMClient(
                api_key=api_key,
                model=model,
                **kwargs,
            )
        elif provider == "openai":
            return OpenAILLMClient(
                api_key=api_key,
                model=model,
                **kwargs,
            )
        elif provider == "gemini":
            return GeminiLLMClient(
                api_key=api_key,
                model=model,
                **kwargs,
            )
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: anthropic, openai, gemini"
            )
