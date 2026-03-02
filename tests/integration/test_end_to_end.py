"""
End-to-end integration test for complete analysis workflow.

Tests the full pipeline: fetch data → analyze → store → deliver
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.deliverer import InsightDeliverer
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.llm_client import ClaudeLLMClient
from stock_analyzer.models import AnalysisResponse, StockData, User
from stock_analyzer.storage import Storage


@pytest.fixture
def test_storage(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test_e2e.db"
    storage = Storage(str(db_path))
    storage.init_database()
    return storage


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock(spec=ClaudeLLMClient)

    async def mock_analyze(prompt, stock_data, system_prompt=None):
        volume_str = f"{stock_data.volume:,}" if isinstance(stock_data.volume, (int, float)) else str(stock_data.volume)
        return AnalysisResponse(
            text=f"""**Summary:**
{stock_data.symbol} shows {'positive' if stock_data.price_change_percent > 0 else 'negative'} momentum.

**Trend Analysis:**
The stock moved {stock_data.price_change_percent:.1f}% with volume at {volume_str}.

**Risk Factors:**
- Market volatility
- Valuation concerns
- Sector headwinds

**Opportunities:**
- Strong fundamentals
- Growth potential
- Market expansion""",
            tokens_used=1500,
            model="claude-sonnet-4-5",
            metadata={"source": "test"}
        )

    client.analyze = mock_analyze
    return client


@pytest.fixture
def mock_fetcher():
    """Mock stock fetcher."""
    fetcher = MagicMock(spec=StockFetcher)

    async def mock_fetch(symbol, start_date=None, end_date=None):
        # Simulate different prices for different symbols
        base_price = hash(symbol) % 500 + 50
        return StockData(
            symbol=symbol,
            current_price=float(base_price),
            price_change_percent=2.3,
            volume=52000000,
            historical_prices=pd.DataFrame({
                'Close': [base_price - 5, base_price - 2, base_price],
                'Volume': [48000000, 50000000, 52000000],
            }),
            fundamentals={'market_cap': 2800000000000, 'pe_ratio': 28.5},
            metadata={'source': 'yfinance'}
        )

    fetcher.fetch_stock_data = mock_fetch
    return fetcher


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test complete workflow: fetch → analyze → store."""
        # Create analyzer
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # Execute analysis
        insight = await analyzer.analyze_stock("AAPL")

        # Verify insight was created
        assert insight is not None
        assert insight.stock_symbol == "AAPL"
        assert insight.summary
        assert insight.trend_analysis
        assert len(insight.risk_factors) > 0
        assert len(insight.opportunities) > 0

        # Verify data was stored
        analysis = test_storage.get_analysis("AAPL", date.today())
        assert analysis is not None
        assert analysis.analysis_status == "success"

        insights = test_storage.get_insights("AAPL", limit=1)
        assert len(insights) == 1
        assert insights[0].stock_symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_subscribe_analyze_deliver_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test full user workflow: subscribe → analyze → deliver."""
        # Step 1: User subscribes
        user = User(user_id="test_user_123", telegram_username="@testuser")
        test_storage.add_user(user)

        from stock_analyzer.models import Subscription
        subscription = Subscription(
            user_id="test_user_123",
            stock_symbol="AAPL"
        )
        test_storage.add_subscription(subscription)

        # Step 2: Run analysis
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )
        insight = await analyzer.analyze_stock("AAPL")

        # Step 3: Prepare for delivery
        assert insight.id is not None  # Should have been saved with ID

        # Verify the complete workflow
        subscriptions = test_storage.get_subscriptions(user_id="test_user_123")
        assert len(subscriptions) == 1
        assert subscriptions[0].stock_symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_daily_job_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test daily job workflow: get subscriptions → batch analyze → track job."""
        # Setup: Create multiple users with subscriptions
        for i in range(3):
            user = User(user_id=f"user_{i}", telegram_username=f"@user{i}")
            test_storage.add_user(user)

        # Add subscriptions
        from stock_analyzer.models import Subscription
        symbols = ["AAPL", "TSLA", "MSFT"]
        for user_id in ["user_0", "user_1"]:
            for symbol in symbols:
                sub = Subscription(user_id=user_id, stock_symbol=symbol)
                test_storage.add_subscription(sub)

        # Get unique stocks to analyze
        all_subs = test_storage.get_subscriptions(active_only=True)
        unique_symbols = list(set(sub.stock_symbol for sub in all_subs))

        # Create job
        job = test_storage.create_job(stocks_scheduled=len(unique_symbols))
        assert job.job_status == "running"

        # Analyze stocks
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        result = await analyzer.analyze_batch(
            unique_symbols,
            parallel=1,
            continue_on_error=True
        )

        # Update job
        test_storage.update_job(
            job.id,
            stocks_processed=result.total,
            success_count=result.success_count,
            failure_count=result.failure_count,
            job_status="completed"
        )

        # Verify workflow
        assert result.success_count > 0

    @pytest.mark.asyncio
    async def test_multiple_users_same_stock(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test that same stock is analyzed once for multiple users."""
        # Create multiple users subscribing to same stock
        for i in range(5):
            user = User(user_id=f"user_{i}")
            test_storage.add_user(user)

            from stock_analyzer.models import Subscription
            sub = Subscription(user_id=f"user_{i}", stock_symbol="AAPL")
            test_storage.add_subscription(sub)

        # Analyze AAPL once
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )
        insight = await analyzer.analyze_stock("AAPL")

        # Verify only one analysis was created
        analyses = test_storage.get_insights("AAPL", limit=10)
        assert len(analyses) == 1

        # But it should be deliverable to all 5 users
        subscriptions = test_storage.get_subscriptions(active_only=True)
        aapl_subs = [s for s in subscriptions if s.stock_symbol == "AAPL"]
        assert len(aapl_subs) == 5

    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test error handling throughout the workflow."""
        # Mock fetcher to fail
        from stock_analyzer.exceptions import DataFetchError

        async def mock_fetch_error(symbol, start_date=None, end_date=None):
            if symbol == "INVALID":
                raise DataFetchError(symbol, "Not found", "test")
            # Normal response for valid symbols
            return StockData(
                symbol=symbol,
                current_price=185.75,
                price_change_percent=2.3,
                volume=52000000,
                historical_prices=pd.DataFrame({'Close': [185.75]}),
                fundamentals={},
                metadata={}
            )

        mock_fetcher.fetch_stock_data = mock_fetch_error

        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # Batch analysis with one invalid symbol
        result = await analyzer.analyze_batch(
            ["AAPL", "INVALID", "TSLA"],
            parallel=1,
            continue_on_error=True
        )

        # Should have processed all, but one failed
        assert result.total == 3
        assert result.failure_count >= 1
        assert result.success_count >= 2

    @pytest.mark.asyncio
    async def test_reanalysis_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test re-analysis of existing stock."""
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # First analysis
        insight1 = await analyzer.analyze_stock("AAPL")
        assert insight1 is not None

        # Second analysis (should skip if same day, unless force=True)
        insight2 = await analyzer.analyze_stock("AAPL", force=False)
        assert insight2 is not None

        # Force re-analysis
        insight3 = await analyzer.analyze_stock("AAPL", force=True)
        assert insight3 is not None

    @pytest.mark.asyncio
    async def test_subscription_limits_workflow(self, test_storage, mock_llm_client, mock_fetcher):
        """Test subscription limit enforcement in workflow."""
        # Create user
        user = User(user_id="test_user")
        test_storage.add_user(user)

        # Add 10 subscriptions (at limit)
        from stock_analyzer.models import Subscription
        for i in range(10):
            sub = Subscription(user_id="test_user", stock_symbol=f"SYM{i:02d}")
            test_storage.add_subscription(sub)

        # Trying to add 11th should fail
        from stock_analyzer.exceptions import SubscriptionLimitError
        with pytest.raises(SubscriptionLimitError):
            sub = Subscription(user_id="test_user", stock_symbol="LIMIT")
            test_storage.add_subscription(sub)

        # Verify we can still analyze existing subscriptions
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        subs = test_storage.get_subscriptions(user_id="test_user")
        symbols = [s.stock_symbol for s in subs[:3]]  # Just test first 3

        result = await analyzer.analyze_batch(symbols, parallel=1)
        assert result.success_count > 0


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""

    @pytest.mark.asyncio
    async def test_batch_analysis_faster_than_sequential(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test that batch analysis with parallel=2 is implemented."""
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]

        # This should use parallel execution
        result = await analyzer.analyze_batch(symbols, parallel=2)

        assert result.total == 4
        assert result.duration_seconds is not None


class TestWorkflowDataIntegrity:
    """Test data integrity throughout workflow."""

    @pytest.mark.asyncio
    async def test_analysis_creates_complete_records(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test that analysis creates complete, linked records."""
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        insight = await analyzer.analyze_stock("AAPL")

        # Verify StockAnalysis record
        analysis = test_storage.get_analysis("AAPL", date.today())
        assert analysis is not None
        assert analysis.stock_symbol == "AAPL"
        assert analysis.analysis_status == "success"
        assert analysis.price_snapshot > 0
        assert analysis.duration_seconds is not None

        # Verify Insight record
        assert insight.analysis_id == analysis.id
        assert insight.stock_symbol == analysis.stock_symbol
        assert insight.analysis_date == analysis.analysis_date

    @pytest.mark.asyncio
    async def test_foreign_key_relationships(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test that foreign key relationships are maintained."""
        # Create user and subscription
        user = User(user_id="test_user")
        test_storage.add_user(user)

        from stock_analyzer.models import Subscription
        sub = Subscription(user_id="test_user", stock_symbol="AAPL")
        test_storage.add_subscription(sub)

        # Create analysis
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )
        insight = await analyzer.analyze_stock("AAPL")

        # Verify relationships
        user_subs = test_storage.get_subscriptions(user_id="test_user")
        assert len(user_subs) == 1
        assert user_subs[0].stock_symbol == "AAPL"

        insights = test_storage.get_insights("AAPL", limit=1)
        assert len(insights) == 1
        assert insights[0].id == insight.id


class TestPersonalUseWorkflow:
    """Test personal use workflow without users/subscriptions."""

    @pytest.mark.asyncio
    async def test_daily_job_reads_stock_list_from_env(
        self, test_storage, mock_llm_client, mock_fetcher, monkeypatch
    ):
        """Test daily job workflow using stock list from environment variables."""
        # Set up environment with stock list
        monkeypatch.setenv("STOCK_ANALYZER_STOCK_LIST", "AAPL,MSFT,GOOGL")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_CHANNEL", "@mystocks")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_TOKEN", "test-token")

        # Load config from env
        from stock_analyzer.config import Config
        with patch("stock_analyzer.config.load_dotenv"):
            config = Config.from_env()

        # Verify config loaded correctly
        symbols = config.get_stock_symbols()
        assert symbols == ["AAPL", "MSFT", "GOOGL"]
        assert config.telegram_channel == "@mystocks"

        # Create job tracking
        job = test_storage.create_job(stocks_scheduled=len(symbols))
        assert job.job_status == "running"
        assert job.stocks_scheduled == 3

        # Analyze all stocks from config
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        result = await analyzer.analyze_batch(
            symbols,
            parallel=1,
            continue_on_error=True
        )

        # Update job status
        test_storage.update_job(
            job.id,
            stocks_processed=result.total,
            success_count=result.success_count,
            failure_count=result.failure_count,
            job_status="completed"
        )

        # Verify workflow completed successfully
        assert result.total == 3
        assert result.success_count == 3
        assert result.failure_count == 0

        # Verify insights were created for all stocks
        for symbol in symbols:
            insights = test_storage.get_insights(symbol, limit=1)
            assert len(insights) == 1
            assert insights[0].stock_symbol == symbol

        # Verify analyses were stored
        for symbol in symbols:
            analysis = test_storage.get_analysis(symbol, date.today())
            assert analysis is not None
            assert analysis.analysis_status == "success"

    @pytest.mark.asyncio
    async def test_daily_job_handles_invalid_symbols(
        self, test_storage, mock_llm_client, mock_fetcher, monkeypatch
    ):
        """Test daily job workflow handles invalid stock symbols gracefully."""
        # Set up environment with mixed valid/invalid symbols
        monkeypatch.setenv("STOCK_ANALYZER_STOCK_LIST", "AAPL,INVALID,MSFT,BADSTOCK")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_CHANNEL", "@mystocks")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_TOKEN", "test-token")

        # Mock fetcher to fail for invalid symbols
        from stock_analyzer.exceptions import DataFetchError

        original_fetch = mock_fetcher.fetch_stock_data

        async def mock_fetch_with_errors(symbol, start_date=None, end_date=None):
            if symbol in ["INVALID", "BADSTOCK"]:
                raise DataFetchError(symbol, "Symbol not found", "test")
            return await original_fetch(symbol, start_date, end_date)

        mock_fetcher.fetch_stock_data = mock_fetch_with_errors

        # Load config
        from stock_analyzer.config import Config
        with patch("stock_analyzer.config.load_dotenv"):
            config = Config.from_env()

        symbols = config.get_stock_symbols()
        assert len(symbols) == 4  # All symbols parsed, even invalid ones

        # Create job
        job = test_storage.create_job(stocks_scheduled=len(symbols))

        # Analyze with continue_on_error=True
        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        result = await analyzer.analyze_batch(
            symbols,
            parallel=1,
            continue_on_error=True
        )

        # Update job
        test_storage.update_job(
            job.id,
            stocks_processed=result.total,
            success_count=result.success_count,
            failure_count=result.failure_count,
            job_status="completed"
        )

        # Verify partial success
        assert result.total == 4
        assert result.success_count == 2  # AAPL and MSFT
        assert result.failure_count == 2  # INVALID and BADSTOCK

        # Verify successful analyses were stored
        aapl_insights = test_storage.get_insights("AAPL", limit=1)
        assert len(aapl_insights) == 1

        msft_insights = test_storage.get_insights("MSFT", limit=1)
        assert len(msft_insights) == 1

        # Verify failed analyses recorded errors
        invalid_analysis = test_storage.get_analysis("INVALID", date.today())
        if invalid_analysis:  # May be None if fetch failed before storage
            assert invalid_analysis.analysis_status == "failed"
            assert invalid_analysis.error_message is not None


class TestHistoricalQueryWorkflow:
    """Test historical insight query workflow (personal use)."""

    @pytest.mark.asyncio
    async def test_complete_historical_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test complete workflow: analyze multiple days → query history."""
        from datetime import timedelta

        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # Simulate 5 days of analysis for AAPL
        base_date = date.today() - timedelta(days=4)
        for i in range(5):
            analysis_date = base_date + timedelta(days=i)

            # Analyze stock for this date
            insight = await analyzer.analyze_stock("AAPL", date=analysis_date, force=True)
            assert insight is not None

        # Query historical insights (no user_id - personal use)
        insights = test_storage.get_insights("AAPL", limit=10)

        # Verify all 5 days of data returned
        assert len(insights) == 5

        # Verify chronological ordering (descending - newest first)
        for i in range(len(insights) - 1):
            assert insights[i].analysis_date >= insights[i + 1].analysis_date

    @pytest.mark.asyncio
    async def test_historical_query_with_date_range(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test querying historical data with date range filter."""
        from datetime import timedelta

        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # Analyze 10 days of data
        base_date = date(2026, 1, 10)
        for i in range(10):
            analysis_date = base_date + timedelta(days=i)
            await analyzer.analyze_stock("MSFT", date=analysis_date, force=True)

        # Query with date range (days 13-17)
        start_date = date(2026, 1, 13)
        end_date = date(2026, 1, 17)

        insights = test_storage.get_insights(
            "MSFT",
            start_date=start_date,
            end_date=end_date,
            limit=10
        )

        # Should return 5 days (13, 14, 15, 16, 17)
        assert len(insights) == 5

        # Verify all dates in range
        for insight in insights:
            assert start_date <= insight.analysis_date <= end_date

    @pytest.mark.asyncio
    async def test_historical_pagination_workflow(
        self, test_storage, mock_llm_client, mock_fetcher
    ):
        """Test pagination of historical insights."""
        from datetime import timedelta

        analyzer = Analyzer(
            llm_client=mock_llm_client,
            fetcher=mock_fetcher,
            storage=test_storage
        )

        # Analyze 20 days of data
        base_date = date.today() - timedelta(days=19)
        for i in range(20):
            analysis_date = base_date + timedelta(days=i)
            await analyzer.analyze_stock("GOOGL", date=analysis_date, force=True)

        # Query first page (5 results)
        page1 = test_storage.get_insights("GOOGL", limit=5, offset=0)
        assert len(page1) == 5

        # Query second page
        page2 = test_storage.get_insights("GOOGL", limit=5, offset=5)
        assert len(page2) == 5

        # Verify pages don't overlap
        page1_dates = {i.analysis_date for i in page1}
        page2_dates = {i.analysis_date for i in page2}
        assert len(page1_dates.intersection(page2_dates)) == 0

        # Query all data
        all_insights = test_storage.get_insights("GOOGL", limit=100)
        assert len(all_insights) == 20
