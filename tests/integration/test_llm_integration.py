"""
Integration tests for LLM client implementations.

Tests integration with LLM APIs using mocked responses.
Verifies that clients correctly handle real-world API response formats.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from stock_analyzer.exceptions import AnalysisError
from stock_analyzer.llm_client import (
    ClaudeLLMClient,
    GeminiLLMClient,
    OpenAILLMClient,
)
from stock_analyzer.models import AnalysisResponse, StockData


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    return StockData(
        symbol="AAPL",
        current_price=185.75,
        price_change_percent=2.3,
        volume=52000000,
        historical_prices=pd.DataFrame({
            'Date': ['2026-01-28', '2026-01-29', '2026-01-30'],
            'Close': [180.0, 181.6, 185.75],
            'Volume': [48000000, 50000000, 52000000],
        }),
        fundamentals={
            'market_cap': 2800000000000,
            'pe_ratio': 28.5,
            'sector': 'Technology',
        },
        metadata={'source': 'yfinance'}
    )


class TestClaudeIntegration:
    """Test Anthropic Claude API integration."""

    @pytest.mark.asyncio
    async def test_claude_successful_analysis(self, sample_stock_data):
        """Test successful analysis with Claude."""
        client = ClaudeLLMClient(
            api_key="test-key",
            model="claude-sonnet-4-5",
            enable_caching=True
        )

        # Mock realistic Claude response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text="""Apple Inc. (AAPL) shows strong bullish momentum with a 2.3% gain.

**Trend Analysis:**
The stock has demonstrated consistent upward movement over the past three trading days,
with increasing volume indicating strong buying interest. Technical indicators suggest
continued positive sentiment.

**Risk Factors:**
- Current valuation at P/E of 28.5x may indicate overvaluation
- Market volatility could impact near-term performance
- Regulatory scrutiny in multiple jurisdictions

**Opportunities:**
- Strong product pipeline for Q2 launch
- Expanding services segment showing 15% YoY growth
- Strategic positioning in AI and wearables market"""
        )]
        mock_response.usage = MagicMock(
            input_tokens=1200,
            output_tokens=350,
            cache_read_input_tokens=800,  # Cached tokens
        )

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await client.analyze(
                prompt="Provide a detailed analysis of AAPL stock based on the provided data.",
                stock_data=sample_stock_data,
                system_prompt="You are an expert financial analyst."
            )

            # Verify response structure
            assert isinstance(response, AnalysisResponse)
            assert len(response.text) > 100
            assert response.tokens_used == 1550  # 1200 + 350
            assert response.model == "claude-sonnet-4-5"
            assert 'input_tokens' in response.metadata
            assert 'output_tokens' in response.metadata

            # Verify analysis content quality
            assert 'AAPL' in response.text or 'Apple' in response.text
            assert any(keyword in response.text.lower() for keyword in [
                'trend', 'analysis', 'risk', 'opportunity', 'momentum'
            ])

    @pytest.mark.asyncio
    async def test_claude_with_prompt_caching(self, sample_stock_data):
        """Test that prompt caching is properly configured."""
        client = ClaudeLLMClient(
            api_key="test-key",
            enable_caching=True
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis text")]
        mock_response.usage = MagicMock(
            input_tokens=100,
            output_tokens=50,
            cache_read_input_tokens=80
        )

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await client.analyze(
                prompt="Analyze",
                stock_data=sample_stock_data,
                system_prompt="System prompt"
            )

            # Verify cache control was added to system message
            call_kwargs = mock_create.call_args.kwargs
            if 'system' in call_kwargs and call_kwargs['system']:
                system_messages = call_kwargs['system']
                # Check if any message has cache_control
                has_cache_control = any(
                    isinstance(msg, dict) and 'cache_control' in msg
                    for msg in system_messages
                )
                assert has_cache_control

    @pytest.mark.asyncio
    async def test_claude_handles_api_errors(self, sample_stock_data):
        """Test Claude error handling."""
        client = ClaudeLLMClient(api_key="test-key")

        with patch.object(client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error: Rate limit exceeded")

            with pytest.raises(AnalysisError) as exc_info:
                await client.analyze("Test", sample_stock_data)

            assert "AAPL" in str(exc_info.value)
            assert "Rate limit" in str(exc_info.value)


class TestOpenAIIntegration:
    """Test OpenAI API integration."""

    @pytest.mark.asyncio
    async def test_openai_successful_analysis(self, sample_stock_data):
        """Test successful analysis with OpenAI."""
        client = OpenAILLMClient(
            api_key="test-key",
            model="gpt-4o",
            temperature=0.7
        )

        # Mock realistic OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="""AAPL Analysis Summary:

Apple stock demonstrates positive momentum with 2.3% daily gain and strong volume.

Key Observations:
1. Upward price trajectory over 3-day period
2. Volume increase suggests institutional buying
3. Technology sector showing overall strength

Risk Assessment:
- High P/E ratio (28.5x) indicates premium valuation
- Market concentration risk in iPhone segment
- Global supply chain dependencies

Investment Outlook:
- Services revenue growth remains strong catalyst
- Product innovation pipeline supports valuation
- Consider entry points on minor pullbacks"""
            ),
            finish_reason='stop'
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=1100,
            completion_tokens=200,
            total_tokens=1300
        )

        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            response = await client.analyze(
                prompt="Analyze AAPL stock",
                stock_data=sample_stock_data,
                system_prompt="You are a financial analyst"
            )

            # Verify response
            assert isinstance(response, AnalysisResponse)
            assert len(response.text) > 100
            assert response.tokens_used == 1300
            assert response.model == "gpt-4o"
            assert 'finish_reason' in response.metadata

    @pytest.mark.asyncio
    async def test_openai_temperature_control(self, sample_stock_data):
        """Test that temperature parameter is applied."""
        client = OpenAILLMClient(
            api_key="test-key",
            temperature=0.3
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="Analysis"),
            finish_reason='stop'
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )

        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            await client.analyze("Test", sample_stock_data)

            # Verify temperature was used
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs.get('temperature') == 0.3

    @pytest.mark.asyncio
    async def test_openai_handles_content_filter(self, sample_stock_data):
        """Test handling of content filter responses."""
        client = OpenAILLMClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content=None),
            finish_reason='content_filter'
        )]
        mock_response.usage = MagicMock(total_tokens=50)

        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            # Should handle gracefully (though content might be None)
            response = await client.analyze("Test", sample_stock_data)
            assert response.metadata['finish_reason'] == 'content_filter'


class TestGeminiIntegration:
    """Test Google Gemini API integration."""

    @pytest.mark.asyncio
    async def test_gemini_successful_analysis(self, sample_stock_data):
        """Test successful analysis with Gemini."""
        client = GeminiLLMClient(
            api_key="test-key",
            model="gemini-2.5-pro",
            temperature=0.7
        )

        # Mock realistic Gemini response
        mock_response = MagicMock()
        mock_response.text = """## AAPL Stock Analysis

**Current Status:** Apple stock shows bullish momentum with +2.3% gain

**Trend Analysis:**
Three-day upward trend with increasing volume pattern. The stock moved from $180 to $185.75,
demonstrating consistent buyer support. Volume expansion (48M to 52M) confirms genuine demand.

**Risk Considerations:**
1. Valuation premium at 28.5x P/E ratio
2. Technology sector volatility exposure
3. Macro-economic headwinds

**Growth Catalysts:**
1. Strong ecosystem lock-in effect
2. Services segment high-margin growth
3. Emerging market expansion potential

**Recommendation:** Maintain position with profit-taking levels at $190"""

        mock_response.usage_metadata = MagicMock(
            prompt_token_count=900,
            candidates_token_count=180,
            total_token_count=1080
        )

        with patch.object(client.model, 'generate_content_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response

            response = await client.analyze(
                prompt="Analyze AAPL",
                stock_data=sample_stock_data,
                system_prompt="Expert analyst"
            )

            # Verify response
            assert isinstance(response, AnalysisResponse)
            assert len(response.text) > 100
            assert response.tokens_used == 1080
            assert 'prompt_tokens' in response.metadata

    @pytest.mark.asyncio
    async def test_gemini_combines_prompts(self, sample_stock_data):
        """Test that Gemini combines system and user prompts."""
        client = GeminiLLMClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.text = "Analysis"
        mock_response.usage_metadata = MagicMock(total_token_count=100)

        with patch.object(client.model, 'generate_content_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = mock_response

            await client.analyze(
                prompt="User instruction",
                stock_data=sample_stock_data,
                system_prompt="System context"
            )

            # Verify prompts were combined
            call_args = mock_generate.call_args.args
            combined_prompt = call_args[0]
            assert "System context" in combined_prompt
            assert "User instruction" in combined_prompt


class TestCrossProviderConsistency:
    """Test consistency across different LLM providers."""

    @pytest.mark.asyncio
    async def test_all_providers_return_valid_response(self, sample_stock_data):
        """Test that all providers return valid AnalysisResponse."""
        # Claude
        claude_client = ClaudeLLMClient(api_key="test-key")
        claude_mock = MagicMock()
        claude_mock.content = [MagicMock(text="Claude analysis")]
        claude_mock.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch.object(claude_client.client.messages, 'create', new_callable=AsyncMock, return_value=claude_mock):
            claude_response = await claude_client.analyze("Test", sample_stock_data)
            assert isinstance(claude_response, AnalysisResponse)
            assert claude_response.text
            assert claude_response.tokens_used > 0

        # OpenAI
        openai_client = OpenAILLMClient(api_key="test-key")
        openai_mock = MagicMock()
        openai_mock.choices = [MagicMock(message=MagicMock(content="OpenAI analysis"), finish_reason='stop')]
        openai_mock.usage = MagicMock(total_tokens=150)

        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock, return_value=openai_mock):
            openai_response = await openai_client.analyze("Test", sample_stock_data)
            assert isinstance(openai_response, AnalysisResponse)
            assert openai_response.text
            assert openai_response.tokens_used > 0

        # Gemini
        gemini_client = GeminiLLMClient(api_key="test-key")
        gemini_mock = MagicMock()
        gemini_mock.text = "Gemini analysis"
        gemini_mock.usage_metadata = MagicMock(total_token_count=120)

        with patch.object(gemini_client.model, 'generate_content_async', new_callable=AsyncMock, return_value=gemini_mock):
            gemini_response = await gemini_client.analyze("Test", sample_stock_data)
            assert isinstance(gemini_response, AnalysisResponse)
            assert gemini_response.text
            assert gemini_response.tokens_used > 0


class TestErrorRecovery:
    """Test error handling and recovery across providers."""

    @pytest.mark.asyncio
    async def test_all_providers_raise_analysis_error(self, sample_stock_data):
        """Test that all providers properly raise AnalysisError on failure."""
        providers = [
            ClaudeLLMClient(api_key="test-key"),
            OpenAILLMClient(api_key="test-key"),
            GeminiLLMClient(api_key="test-key"),
        ]

        for client in providers:
            # Mock to raise exception
            if isinstance(client, ClaudeLLMClient):
                with patch.object(client.client.messages, 'create', new_callable=AsyncMock, side_effect=Exception("API Error")):
                    with pytest.raises(AnalysisError):
                        await client.analyze("Test", sample_stock_data)

            elif isinstance(client, OpenAILLMClient):
                with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock, side_effect=Exception("API Error")):
                    with pytest.raises(AnalysisError):
                        await client.analyze("Test", sample_stock_data)

            elif isinstance(client, GeminiLLMClient):
                with patch.object(client.model, 'generate_content_async', new_callable=AsyncMock, side_effect=Exception("API Error")):
                    with pytest.raises(AnalysisError):
                        await client.analyze("Test", sample_stock_data)
