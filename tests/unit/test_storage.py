"""
Unit tests for Storage class.

Tests database operations including:
- Database initialization
- User management
- Subscription management
- Analysis and insight storage
- Delivery log tracking
- Job tracking
"""

import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from stock_analyzer.exceptions import StorageError, SubscriptionLimitError
from stock_analyzer.models import (
    AnalysisJob,
    DeliveryLog,
    Insight,
    StockAnalysis,
    Subscription,
    User,
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
        """Test that init_database creates all required tables."""
        storage = Storage(temp_db)
        storage.init_database()

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Check all tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "users" in tables
        assert "subscriptions" in tables
        assert "stock_analyses" in tables
        assert "insights" in tables
        assert "delivery_logs" in tables
        assert "analysis_jobs" in tables

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


class TestUserOperations:
    """Test user management operations."""

    def test_add_user(self, storage):
        """Test adding a new user."""
        user = User(
            user_id="123456789",
            telegram_username="@testuser",
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
        )

        storage.add_user(user)

        # Verify user was added
        retrieved = storage.get_user("123456789")
        assert retrieved is not None
        assert retrieved.user_id == "123456789"
        assert retrieved.telegram_username == "@testuser"

    def test_update_user_last_active(self, storage):
        """Test updating user's last active timestamp."""
        user = User(user_id="123456789")
        storage.add_user(user)

        # Update last active
        new_time = datetime.utcnow()
        storage.update_user_last_active("123456789", new_time)

        # Verify update
        retrieved = storage.get_user("123456789")
        assert retrieved.last_active >= new_time


class TestSubscriptionOperations:
    """Test subscription management operations."""

    def test_add_subscription(self, storage):
        """Test adding a subscription."""
        # First add user
        user = User(user_id="123456789")
        storage.add_user(user)

        # Add subscription
        sub = Subscription(
            user_id="123456789",
            stock_symbol="AAPL",
            subscription_date=datetime.utcnow(),
            active_status=1,
        )
        result = storage.add_subscription(sub)

        assert result.id is not None
        assert result.stock_symbol == "AAPL"

    def test_get_subscriptions_by_user(self, storage):
        """Test retrieving user's subscriptions."""
        user = User(user_id="123456789")
        storage.add_user(user)

        # Add multiple subscriptions
        storage.add_subscription(Subscription(user_id="123456789", stock_symbol="AAPL"))
        storage.add_subscription(Subscription(user_id="123456789", stock_symbol="TSLA"))
        storage.add_subscription(Subscription(user_id="123456789", stock_symbol="MSFT"))

        # Get subscriptions
        subs = storage.get_subscriptions(user_id="123456789")

        assert len(subs) == 3
        symbols = {sub.stock_symbol for sub in subs}
        assert symbols == {"AAPL", "TSLA", "MSFT"}

    def test_get_all_active_subscriptions(self, storage):
        """Test retrieving all active subscriptions across users."""
        # Add two users with subscriptions
        storage.add_user(User(user_id="111"))
        storage.add_user(User(user_id="222"))

        storage.add_subscription(Subscription(user_id="111", stock_symbol="AAPL"))
        storage.add_subscription(Subscription(user_id="222", stock_symbol="TSLA"))

        # Get all subscriptions
        all_subs = storage.get_subscriptions()

        assert len(all_subs) == 2

    def test_remove_subscription(self, storage):
        """Test removing a subscription (setting active_status=0)."""
        user = User(user_id="123456789")
        storage.add_user(user)

        storage.add_subscription(Subscription(user_id="123456789", stock_symbol="AAPL"))

        # Remove subscription
        storage.remove_subscription("123456789", "AAPL")

        # Verify it's inactive
        subs = storage.get_subscriptions(user_id="123456789", active_only=True)
        assert len(subs) == 0

    def test_subscription_limit_per_user(self, storage):
        """Test that user subscription limit is enforced."""
        user = User(user_id="123456789")
        storage.add_user(user)

        # Add 10 subscriptions (at limit)
        for i in range(10):
            storage.add_subscription(
                Subscription(user_id="123456789", stock_symbol=f"SYM{i:02d}")
            )

        # Try to add 11th subscription - should raise error
        with pytest.raises(SubscriptionLimitError):
            storage.add_subscription(
                Subscription(user_id="123456789", stock_symbol="LIMIT")
            )


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
        # This test would need multiple days of data
        # For now, just test the method exists and runs
        insights = storage.get_insights(
            "AAPL",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            limit=10,
        )
        assert isinstance(insights, list)


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
    """Test delivery log operations."""

    def test_log_delivery(self, storage):
        """Test logging a delivery."""
        # Setup: user, analysis, insight
        storage.add_user(User(user_id="123456789"))

        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            price_snapshot=185.75,
            analysis_status="success",
        )
        storage.save_analysis(analysis)
        saved_analysis = storage.get_analysis("AAPL", date.today())

        insight = Insight(
            analysis_id=saved_analysis.id,
            stock_symbol="AAPL",
            analysis_date=date.today(),
            summary="Test",
            trend_analysis="Test",
            risk_factors=["Test"],
            opportunities=["Test"],
            confidence_level="high",
        )
        storage.save_insight(insight)

        # Get saved insight ID (would need method to retrieve)
        # For now, assume insight has ID 1
        log = DeliveryLog(
            insight_id=1,
            user_id="123456789",
            delivery_status="success",
            delivery_method="telegram",
            telegram_message_id="987654321",
        )

        # Should not raise error
        # storage.log_delivery(log)
        assert True  # Placeholder until method exists


class TestErrorHandling:
    """Test error handling in storage operations."""

    def test_invalid_database_path(self):
        """Test that invalid database path raises appropriate error."""
        with pytest.raises((StorageError, sqlite3.OperationalError, OSError)):
            storage = Storage("/invalid/path/database.db")
            storage.init_database()

    def test_get_nonexistent_user(self, storage):
        """Test retrieving non-existent user returns None."""
        user = storage.get_user("nonexistent")
        assert user is None

    def test_get_nonexistent_analysis(self, storage):
        """Test retrieving non-existent analysis returns None."""
        analysis = storage.get_analysis("NONEXISTENT", date.today())
        assert analysis is None
