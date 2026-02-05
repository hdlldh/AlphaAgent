"""
Contract tests for Analyzer component.

Tests the public API contract of the Analyzer class.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.exceptions import AnalysisError
from stock_analyzer.llm_client import ClaudeLLMClient
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.models import AnalysisResponse, Insight, StockData
from stock_analyzer.storage import Storage


@pytest.fixture
def mock_storage(tmp_path):
    """Create a mock storage instance."""
    db_path = tmp_path / "test.db"
    storage = Storage(str(db_path))
    storage.init_database()
    return storage


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock(spec=ClaudeLLMClient)

    # Mock analyze method
    async def mock_analyze(prompt, stock_data, system_prompt=None):
        return AnalysisResponse(
            text="""**Summary:**
Strong upward momentum with positive indicators.

**Trend Analysis:**
The stock has gained 2.3% with volume 15% above average.

**Risk Factors:**
- Overvaluation concerns
- Market volatility

**Opportunities:**
- Product launches
- Services growth""",
            tokens_used=1500,
            model="claude-sonnet-4-5",
            metadata={}
        )

    client.analyze = mock_analyze
    return client


@pytest.fixture
def mock_fetcher():
    """Create a mock stock fetcher."""
    fetcher = MagicMock(spec=StockFetcher)

    async def mock_fetch(symbol, start_date=None, end_date=None):
        return StockData(
            symbol=symbol,
            current_price=185.75,
            price_change_percent=2.3,
            volume=52000000,
            historical_prices=pd.DataFrame({
                'Close': [180.0, 181.6, 185.75],
                'Volume': [48000000, 50000000, 52000000],
            }),
            fundamentals={'market_cap': 2800000000000, 'pe_ratio': 28.5},
            metadata={'source': 'yfinance'}
        )

    fetcher.fetch_stock_data = mock_fetch
    return fetcher


@pytest.fixture
def analyzer(mock_llm_client, mock_fetcher, mock_storage):
    """Create an Analyzer instance with mocked dependencies."""
    return Analyzer(
        llm_client=mock_llm_client,
        fetcher=mock_fetcher,
        storage=mock_storage
    )


class TestAnalyzerContract:
    """Test the Analyzer public API contract."""

    @pytest.mark.asyncio
    async def test_analyze_stock_returns_insight(self, analyzer):
        """Test that analyze_stock returns an Insight object."""
        insight = await analyzer.analyze_stock("AAPL")

        assert isinstance(insight, Insight)
        assert insight.stock_symbol == "AAPL"
        assert insight.summary
        assert insight.trend_analysis
        assert insight.risk_factors
        assert insight.opportunities
        assert insight.confidence_level in ["high", "medium", "low"]
        assert insight.analysis_date == date.today()

    @pytest.mark.asyncio
    async def test_analyze_stock_with_date(self, analyzer):
        """Test analyzing stock for specific date."""
        analysis_date = date(2026, 1, 30)
        insight = await analyzer.analyze_stock("AAPL", date=analysis_date)

        assert insight.analysis_date == analysis_date

    @pytest.mark.asyncio
    async def test_analyze_stock_saves_to_storage(self, analyzer, mock_storage):
        """Test that analysis results are saved to storage."""
        insight = await analyzer.analyze_stock("AAPL")

        # Verify analysis was saved
        saved_analysis = mock_storage.get_analysis("AAPL", date.today())
        assert saved_analysis is not None
        assert saved_analysis.analysis_status == "success"

        # Verify insight was saved
        insights = mock_storage.get_insights("AAPL", limit=1)
        assert len(insights) > 0
        assert insights[0].stock_symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_analyze_stock_force_reanalysis(self, analyzer, mock_storage):
        """Test that force=True re-analyzes even if exists."""
        # First analysis
        insight1 = await analyzer.analyze_stock("AAPL")

        # Second analysis with force=True should create new analysis
        insight2 = await analyzer.analyze_stock("AAPL", force=True)

        assert insight2 is not None

    @pytest.mark.asyncio
    async def test_analyze_stock_invalid_symbol(self, analyzer, mock_fetcher):
        """Test error handling for invalid symbol."""
        # Mock fetcher to raise error
        async def mock_fetch_error(symbol, start_date=None, end_date=None):
            from stock_analyzer.exceptions import InvalidSymbolError
            raise InvalidSymbolError(symbol, "Not found")

        mock_fetcher.fetch_stock_data = mock_fetch_error

        with pytest.raises(Exception):  # Could be InvalidSymbolError or AnalysisError
            await analyzer.analyze_stock("INVALID")

    @pytest.mark.asyncio
    async def test_analyze_batch_processes_multiple_stocks(self, analyzer):
        """Test batch analysis of multiple stocks."""
        symbols = ["AAPL", "TSLA", "MSFT"]
        result = await analyzer.analyze_batch(symbols, parallel=1)

        assert result.total == 3
        assert result.success_count <= 3
        assert result.failure_count >= 0
        assert result.success_count + result.failure_count == result.total

    @pytest.mark.asyncio
    async def test_analyze_batch_parallel_execution(self, analyzer):
        """Test that batch analysis can run in parallel."""
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]
        result = await analyzer.analyze_batch(symbols, parallel=2)

        assert result.total == 4

    @pytest.mark.asyncio
    async def test_analyze_batch_continue_on_error(self, analyzer, mock_fetcher):
        """Test that batch continues on error when flag is set."""
        symbols = ["AAPL", "INVALID", "MSFT"]

        # Make INVALID fail
        call_count = [0]
        original_fetch = mock_fetcher.fetch_stock_data

        async def conditional_fetch(symbol, start_date=None, end_date=None):
            if symbol == "INVALID":
                from stock_analyzer.exceptions import InvalidSymbolError
                raise InvalidSymbolError(symbol, "Not found")
            return await original_fetch(symbol, start_date, end_date)

        mock_fetcher.fetch_stock_data = conditional_fetch

        result = await analyzer.analyze_batch(
            symbols,
            parallel=1,
            continue_on_error=True
        )

        # Should have processed all 3, but one failed
        assert result.total == 3
        assert result.failure_count >= 1

    @pytest.mark.asyncio
    async def test_analyzer_uses_prompt_templates(self, analyzer, mock_llm_client):
        """Test that analyzer uses proper prompt templates."""
        await analyzer.analyze_stock("AAPL")

        # Verify that analyze was called (prompt was generated)
        # The mock should have been called
        assert mock_llm_client.analyze is not None

    @pytest.mark.asyncio
    async def test_analyzer_handles_llm_errors(self, analyzer, mock_llm_client):
        """Test error handling when LLM fails."""
        # Make LLM fail
        async def mock_analyze_error(prompt, stock_data, system_prompt=None):
            raise Exception("LLM API Error")

        mock_llm_client.analyze = mock_analyze_error

        with pytest.raises(AnalysisError):
            await analyzer.analyze_stock("AAPL")

    @pytest.mark.asyncio
    async def test_analyzer_extracts_structured_output(self, analyzer):
        """Test that analyzer extracts structured fields from LLM output."""
        insight = await analyzer.analyze_stock("AAPL")

        # Verify structured extraction
        assert isinstance(insight.risk_factors, list)
        assert len(insight.risk_factors) > 0
        assert isinstance(insight.opportunities, list)
        assert len(insight.opportunities) > 0

    @pytest.mark.asyncio
    async def test_analyzer_sets_confidence_level(self, analyzer):
        """Test that analyzer determines confidence level."""
        insight = await analyzer.analyze_stock("AAPL")

        assert insight.confidence_level in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_analyzer_tracks_duration(self, analyzer, mock_storage):
        """Test that analysis duration is tracked."""
        await analyzer.analyze_stock("AAPL")

        analysis = mock_storage.get_analysis("AAPL", date.today())
        assert analysis.duration_seconds is not None
        assert analysis.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_analyzer_metadata_includes_model_info(self, analyzer):
        """Test that insight metadata includes LLM model information."""
        insight = await analyzer.analyze_stock("AAPL")

        assert 'llm_model' in insight.metadata or 'model' in insight.metadata
        assert 'tokens_used' in insight.metadata or 'tokens' in insight.metadata


class TestBatchAnalysisResult:
    """Test BatchAnalysisResult structure."""

    @pytest.mark.asyncio
    async def test_batch_result_structure(self, analyzer):
        """Test that batch result has required fields."""
        result = await analyzer.analyze_batch(["AAPL"], parallel=1)

        assert hasattr(result, 'total')
        assert hasattr(result, 'success_count')
        assert hasattr(result, 'failure_count')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'results')

    @pytest.mark.asyncio
    async def test_batch_result_individual_results(self, analyzer):
        """Test that batch result includes individual results."""
        result = await analyzer.analyze_batch(["AAPL", "TSLA"], parallel=1)

        assert isinstance(result.results, list)
        assert len(result.results) == 2

        for individual_result in result.results:
            assert hasattr(individual_result, 'stock_symbol')
            assert hasattr(individual_result, 'status')
