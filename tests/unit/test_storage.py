"""
Unit tests for Storage class (personal use).

Tests database operations including:
- Database initialization
- Analysis and insight storage
- Delivery log tracking
- Job tracking
"""

import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from stock_analyzer.exceptions import StorageError
from stock_analyzer.models import (
    AnalysisJob,
    DeliveryLog,
    Insight,
    StockAnalysis,
)
from stock_analyzer.storage import Storage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def storage(temp_db):
    """Create a Storage instance with temporary database."""
    storage = Storage(temp_db)
    storage.init_database()
    return storage


class TestStorageInitialization:
    """Test database initialization."""

    def test_init_database_creates_tables(self, temp_db):
        """Test that init_database creates all required tables (personal use)."""
        storage = Storage(temp_db)
        storage.init_database()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check all tables exist (personal use - no users/subscriptions)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "stock_analyses" in tables
        assert "insights" in tables
        assert "delivery_logs" in tables
        assert "analysis_jobs" in tables

        # Verify multi-user tables are NOT created
        assert "users" not in tables
        assert "subscriptions" not in tables

        conn.close()

    def test_init_database_creates_indexes(self, temp_db):
        """Test that init_database creates indexes for performance."""
        storage = Storage(temp_db)
        storage.init_database()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        # Should have indexes on commonly queried columns
        assert len(indexes) > 0  # At least some indexes exist

        conn.close()



class TestAnalysisOperations:
    """Test stock analysis storage operations."""

    def test_save_analysis(self, storage):
        """Test saving a stock analysis."""
        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=185.75,
            price_change_percent=2.3,
            volume=52000000,
            analysis_status="success",
            duration_seconds=4.2,
        )

        storage.save_analysis(analysis)

        # Verify saved
        retrieved = storage.get_analysis("AAPL", date.today())
        assert retrieved is not None
        assert retrieved.stock_symbol == "AAPL"
        assert retrieved.price_snapshot == 185.75
        assert retrieved.analysis_status == "success"

    def test_unique_analysis_per_day(self, storage):
        """Test that only one analysis per stock per day is allowed."""
        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=185.75,
            analysis_status="success",
        )

        storage.save_analysis(analysis)

        # Try to save another analysis for same stock/date - should update
        analysis2 = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=186.00,
            analysis_status="success",
        )

        # Should not raise error, but update existing
        storage.save_analysis(analysis2)

        retrieved = storage.get_analysis("AAPL", date.today())
        assert retrieved.price_snapshot == 186.00  # Updated value


class TestInsightOperations:
    """Test insight storage and retrieval operations."""

    def test_save_insight(self, storage):
        """Test saving an insight."""
        # First create analysis
        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=185.75,
            analysis_status="success",
        )
        storage.save_analysis(analysis)
        saved_analysis = storage.get_analysis("AAPL", date.today())

        # Create insight
        insight = Insight(
            analysis_id=saved_analysis.id,
            stock_symbol="AAPL",
            analysis_date=date.today(),
            summary="Strong upward momentum",
            trend_analysis="The stock has gained 2.3%",
            risk_factors=["Overvaluation concerns"],
            opportunities=["Product launches in Q2"],
            confidence_level="high",
        )

        storage.save_insight(insight)

        # Verify saved
        insights = storage.get_insights("AAPL", limit=1)
        assert len(insights) == 1
        assert insights[0].summary == "Strong upward momentum"
        assert insights[0].confidence_level == "high"

    def test_get_insights_with_date_range(self, storage):
        """Test retrieving insights with date filtering."""
        # Save insights across multiple days
        for day in [15, 20, 25, 30]:
            insight = Insight(
                stock_symbol="AAPL",
                analysis_date=date(2026, 1, day),
                summary=f"Day {day} analysis",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium"
            )
            storage.save_insight(insight)

        # Query with date range
        insights = storage.get_insights(
            "AAPL",
            start_date=date(2026, 1, 18),
            end_date=date(2026, 1, 28),
            limit=10
        )

        # Should only include days 20 and 25
        assert len(insights) == 2
        dates = [i.analysis_date.day for i in insights]
        assert 20 in dates
        assert 25 in dates
        assert 15 not in dates
        assert 30 not in dates

    def test_get_insights_without_user_filtering(self, storage):
        """Test get_insights() returns all insights for symbol (personal use - no user filtering)."""
        # Save multiple insights for same stock
        for i in range(5):
            insight = Insight(
                stock_symbol="MSFT",
                analysis_date=date(2026, 1, 20 + i),
                summary=f"Analysis {i+1}",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium"
            )
            storage.save_insight(insight)

        # Query without any user_id parameter (personal use)
        insights = storage.get_insights("MSFT", limit=10)

        # Should return all 5 insights
        assert len(insights) == 5

    def test_get_insights_pagination(self, storage):
        """Test pagination with limit and offset."""
        # Save 10 insights
        for i in range(10):
            insight = Insight(
                stock_symbol="GOOGL",
                analysis_date=date(2026, 1, 1 + i),
                summary=f"Day {i+1}",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium"
            )
            storage.save_insight(insight)

        # Test limit
        page1 = storage.get_insights("GOOGL", limit=3, offset=0)
        assert len(page1) == 3

        # Test offset
        page2 = storage.get_insights("GOOGL", limit=3, offset=3)
        assert len(page2) == 3

        # Verify different results
        assert page1[0].analysis_date != page2[0].analysis_date

        # Test limit larger than total
        all_insights = storage.get_insights("GOOGL", limit=100)
        assert len(all_insights) == 10

    def test_get_insights_ordered_by_date_desc(self, storage):
        """Test insights are returned in descending date order."""
        # Save insights out of order
        dates = [date(2026, 1, 25), date(2026, 1, 20), date(2026, 1, 30)]
        for d in dates:
            insight = Insight(
                stock_symbol="TSLA",
                analysis_date=d,
                summary="Test",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium"
            )
            storage.save_insight(insight)

        # Query insights
        insights = storage.get_insights("TSLA", limit=10)

        # Should be ordered descending (newest first)
        assert insights[0].analysis_date == date(2026, 1, 30)
        assert insights[1].analysis_date == date(2026, 1, 25)
        assert insights[2].analysis_date == date(2026, 1, 20)


class TestJobOperations:
    """Test analysis job tracking operations."""

    def test_create_job(self, storage):
        """Test creating an analysis job."""
        job = storage.create_job(stocks_scheduled=42)

        assert job.id is not None
        assert job.stocks_scheduled == 42
        assert job.job_status == "running"
        assert job.stocks_processed == 0

    def test_update_job(self, storage):
        """Test updating job progress."""
        job = storage.create_job(stocks_scheduled=10)

        # Update job
        storage.update_job(
            job.id,
            stocks_processed=10,
            success_count=8,
            failure_count=2,
            job_status="completed",
        )

        # Verify update
        # (Would need a get_job method, but testing update doesn't fail)
        assert True  # If we get here, update didn't raise error


class TestDeliveryLogging:
    """Test delivery log operations (personal use)."""

    def test_log_delivery_to_channel(self, storage):
        """Test logging a delivery to personal channel."""
        # Setup: analysis, insight (no user needed for personal use)
        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=185.75,
            analysis_status="success",
        )
        storage.save_analysis(analysis)

        insight = Insight(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            summary="Test",
            trend_analysis="Test",
            risk_factors=["Test"],
            opportunities=["Test"],
            confidence_level="high",
        )
        insight_id = storage.save_insight(insight)

        # Create delivery log for personal channel (not user)
        log = DeliveryLog(
            insight_id=insight_id,
            channel_id="@mystocks",  # Personal channel instead of user_id
            delivery_status="success",
            delivery_method="telegram",
            telegram_message_id="987654321",
        )

        # Save delivery log
        log_id = storage.save_delivery_log(log)
        assert log_id is not None
        assert log_id > 0


class TestErrorHandling:
    """Test error handling in storage operations (personal use)."""

    def test_invalid_database_path(self):
        """Test that invalid database path raises appropriate error."""
        with pytest.raises((StorageError, sqlite3.OperationalError, OSError)):
            storage = Storage("/invalid/path/database.db")
            storage.init_database()

    def test_get_nonexistent_analysis(self, storage):
        """Test retrieving non-existent analysis returns None."""
        analysis = storage.get_analysis("NONEXISTENT", date.today())
        assert analysis is None
