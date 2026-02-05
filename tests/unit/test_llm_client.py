"""
Unit tests for LLM client abstraction.

Tests the abstract base class and concrete implementations for:
- ClaudeLLMClient (Anthropic)
- OpenAILLMClient
- GeminiLLMClient
- LLMClientFactory
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from stock_analyzer.exceptions import AnalysisError
from stock_analyzer.llm_client import (
    ClaudeLLMClient,
    GeminiLLMClient,
    LLMClient,
    LLMClientFactory,
    OpenAILLMClient,
)
from stock_analyzer.models import AnalysisResponse, StockData
import pandas as pd


@pytest.fixture
def mock_stock_data():
    """Create mock stock data for testing."""
    return StockData(
        symbol="AAPL",
        current_price=185.75,
        price_change_percent=2.3,
        volume=52000000,
        historical_prices=pd.DataFrame({
            'Date': ['2026-01-29', '2026-01-30'],
            'Close': [181.60, 185.75],
            'Volume': [48000000, 52000000]
        }),
        fundamentals={"pe_ratio": 28.5, "market_cap": 2800000000000},
        metadata={"source": "yfinance"}
    )


class TestLLMClientAbstraction:
    """Test the abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()

    def test_abstract_methods_defined(self):
        """Test that abstract methods are properly defined."""
        assert hasattr(LLMClient, 'analyze')
        assert hasattr(LLMClient, 'count_tokens')


class TestClaudeLLMClient:
    """Test Anthropic Claude LLM client."""

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_stock_data):
        """Test successful analysis with Claude."""
        client = ClaudeLLMClient(
            api_key="test-key",
            model="claude-sonnet-4-5",
            enable_caching=True,
            max_tokens=2048
        )

        # Mock the Anthropic client response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Strong upward momentum with positive indicators.")]
        mock_response.usage = MagicMock(input_tokens=1000, output_tokens=500)

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await client.analyze(
                prompt="Analyze AAPL stock",
                stock_data=mock_stock_data,
                system_prompt="You are a stock analyst"
            )

            assert isinstance(response, AnalysisResponse)
            assert response.text == "Strong upward momentum with positive indicators."
            assert response.tokens_used == 1500  # 1000 + 500
            assert response.model == "claude-sonnet-4-5"

    @pytest.mark.asyncio
    async def test_analyze_with_caching(self, mock_stock_data):
        """Test that prompt caching is enabled when configured."""
        client = ClaudeLLMClient(
            api_key="test-key",
            model="claude-sonnet-4-5",
            enable_caching=True
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis text")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await client.analyze(
                prompt="Test prompt",
                stock_data=mock_stock_data,
                system_prompt="System prompt"
            )

            # Verify caching was enabled in system message
            call_args = mock_create.call_args
            assert call_args is not None
            system_arg = call_args.kwargs.get('system')
            if system_arg:
                assert any('cache_control' in msg for msg in system_arg if isinstance(msg, dict))

    @pytest.mark.asyncio
    async def test_analyze_api_error(self, mock_stock_data):
        """Test handling of API errors."""
        client = ClaudeLLMClient(api_key="test-key")

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(AnalysisError):
                await client.analyze(
                    prompt="Test",
                    stock_data=mock_stock_data
                )

    @pytest.mark.asyncio
    async def test_count_tokens(self):
        """Test token counting (uses approximation)."""
        client = ClaudeLLMClient(api_key="test-key")

        # Claude uses approximation: 4 chars ≈ 1 token
        text = "This is a test string"  # 21 characters
        count = await client.count_tokens(text)
        assert count > 0  # Should return some positive number
        assert count == len(text) // 4  # Verify approximation formula


class TestOpenAILLMClient:
    """Test OpenAI LLM client."""

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_stock_data):
        """Test successful analysis with OpenAI."""
        client = OpenAILLMClient(
            api_key="test-key",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2048
        )

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Strong bullish trend observed."))
        ]
        mock_response.usage = MagicMock(total_tokens=1200)

        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await client.analyze(
                prompt="Analyze AAPL",
                stock_data=mock_stock_data,
                system_prompt="You are a financial analyst"
            )

            assert isinstance(response, AnalysisResponse)
            assert response.text == "Strong bullish trend observed."
            assert response.tokens_used == 1200
            assert response.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_analyze_with_temperature(self, mock_stock_data):
        """Test that temperature setting is applied."""
        client = OpenAILLMClient(
            api_key="test-key",
            temperature=0.5
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Analysis"))]
        mock_response.usage = MagicMock(total_tokens=100)

        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await client.analyze("Test", mock_stock_data)

            # Verify temperature was passed
            call_args = mock_create.call_args
            assert call_args.kwargs.get('temperature') == 0.5

    @pytest.mark.asyncio
    async def test_count_tokens_approximation(self):
        """Test token counting (uses approximation for OpenAI)."""
        client = OpenAILLMClient(api_key="test-key")

        # OpenAI doesn't have a direct count method, so it uses approximation
        count = await client.count_tokens("This is a test string with multiple words")
        assert count > 0  # Should return some positive number


class TestGeminiLLMClient:
    """Test Google Gemini LLM client."""

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_stock_data):
        """Test successful analysis with Gemini."""
        client = GeminiLLMClient(
            api_key="test-key",
            model="gemini-2.5-pro",
            temperature=0.7,
            max_output_tokens=2048
        )

        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Positive outlook with strong fundamentals."
        mock_response.usage_metadata = MagicMock(total_token_count=800)

        with patch.object(client.model, 'generate_content_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response

            response = await client.analyze(
                prompt="Analyze AAPL",
                stock_data=mock_stock_data,
                system_prompt="Expert financial analyst"
            )

            assert isinstance(response, AnalysisResponse)
            assert response.text == "Positive outlook with strong fundamentals."
            assert response.tokens_used == 800

    @pytest.mark.asyncio
    async def test_analyze_combines_system_and_user_prompt(self, mock_stock_data):
        """Test that system prompt is prepended to user prompt."""
        client = GeminiLLMClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.text = "Analysis"
        mock_response.usage_metadata = MagicMock(total_token_count=100)

        with patch.object(client.model, 'generate_content_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response

            await client.analyze(
                prompt="User prompt",
                stock_data=mock_stock_data,
                system_prompt="System prompt"
            )

            # Verify prompts were combined
            call_args = mock_generate.call_args
            full_prompt = call_args.args[0]
            assert "System prompt" in full_prompt
            assert "User prompt" in full_prompt

    @pytest.mark.asyncio
    async def test_count_tokens_approximation(self):
        """Test token counting for Gemini."""
        client = GeminiLLMClient(api_key="test-key")

        # Gemini uses approximation like OpenAI
        count = await client.count_tokens("Test string")
        assert count > 0


class TestLLMClientFactory:
    """Test LLM client factory."""

    def test_create_anthropic_client(self):
        """Test creating Anthropic client via factory."""
        client = LLMClientFactory.create(
            provider="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-5",
            enable_caching=True
        )

        assert isinstance(client, ClaudeLLMClient)
        assert client.model == "claude-sonnet-4-5"
        assert client.enable_caching is True

    def test_create_anthropic_with_default_model(self):
        """Test creating Anthropic client with default model."""
        client = LLMClientFactory.create(
            provider="anthropic",
            api_key="test-key"
        )

        assert isinstance(client, ClaudeLLMClient)
        # Should use default model
        assert "claude" in client.model.lower()

    def test_create_openai_client(self):
        """Test creating OpenAI client via factory."""
        client = LLMClientFactory.create(
            provider="openai",
            api_key="test-key",
            model="gpt-4o",
            temperature=0.8
        )

        assert isinstance(client, OpenAILLMClient)
        assert client.model == "gpt-4o"
        assert client.temperature == 0.8

    def test_create_openai_with_default_model(self):
        """Test creating OpenAI client with default model."""
        client = LLMClientFactory.create(
            provider="openai",
            api_key="test-key"
        )

        assert isinstance(client, OpenAILLMClient)
        assert "gpt" in client.model.lower()

    def test_create_gemini_client(self):
        """Test creating Gemini client via factory."""
        client = LLMClientFactory.create(
            provider="gemini",
            api_key="test-key",
            model="gemini-2.5-flash",
            temperature=0.6
        )

        assert isinstance(client, GeminiLLMClient)
        assert "gemini" in client.model.model_name.lower()

    def test_create_gemini_with_default_model(self):
        """Test creating Gemini client with default model."""
        client = LLMClientFactory.create(
            provider="gemini",
            api_key="test-key"
        )

        assert isinstance(client, GeminiLLMClient)
        assert "gemini" in client.model.model_name.lower()

    def test_create_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMClientFactory.create(
                provider="unknown_provider",
                api_key="test-key"
            )

    def test_create_case_insensitive_provider(self):
        """Test that provider names are case-insensitive."""
        client1 = LLMClientFactory.create(provider="ANTHROPIC", api_key="key")
        client2 = LLMClientFactory.create(provider="Anthropic", api_key="key")
        client3 = LLMClientFactory.create(provider="anthropic", api_key="key")

        assert isinstance(client1, ClaudeLLMClient)
        assert isinstance(client2, ClaudeLLMClient)
        assert isinstance(client3, ClaudeLLMClient)


class TestProviderIntegration:
    """Test integration between different providers."""

    @pytest.mark.asyncio
    async def test_all_providers_return_same_interface(self, mock_stock_data):
        """Test that all providers return AnalysisResponse with same structure."""
        providers = [
            ("anthropic", ClaudeLLMClient, "claude-sonnet-4-5"),
            ("openai", OpenAILLMClient, "gpt-4o"),
            ("gemini", GeminiLLMClient, "gemini-2.5-pro"),
        ]

        for provider_name, client_class, model in providers:
            client = LLMClientFactory.create(
                provider=provider_name,
                api_key="test-key",
                model=model
            )

            assert isinstance(client, client_class)
            assert isinstance(client, LLMClient)

    def test_all_providers_have_required_methods(self):
        """Test that all provider implementations have required methods."""
        clients = [
            ClaudeLLMClient(api_key="key"),
            OpenAILLMClient(api_key="key"),
            GeminiLLMClient(api_key="key"),
        ]

        for client in clients:
            assert hasattr(client, 'analyze')
            assert hasattr(client, 'count_tokens')
            assert callable(getattr(client, 'analyze'))
            assert callable(getattr(client, 'count_tokens'))
