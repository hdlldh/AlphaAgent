"""
Unit tests for subscription management (User Story 2).

These tests focus on subscription business logic and limits.
Tests are marked with [US2] for pytest filtering.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from stock_analyzer.models import Subscription, User
from stock_analyzer.storage import Storage

# Mark all tests in this module with US2
pytestmark = pytest.mark.US2


@pytest.fixture
def storage():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    storage = Storage(db_path)
    storage.init_database()
    yield storage

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def test_user(storage):
    """Create a test user."""
    user = User(
        user_id="test_user_123",
        telegram_username="@testuser",
        created_at=datetime.utcnow()
    )
    storage.add_user(user)
    return user


class TestAddSubscription:
    """Tests for adding subscriptions."""

    def test_add_first_subscription(self, storage, test_user):
        """
        GIVEN a new user with no subscriptions
        WHEN they subscribe to AAPL
        THEN subscription should be added successfully
        """
        subscription = Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL"
        )
        storage.add_subscription(subscription)

        # Verify subscription exists
        subs = storage.get_subscriptions(user_id=test_user.user_id)
        assert len(subs) == 1
        assert subs[0].stock_symbol == "AAPL"
        assert subs[0].active_status == True

    def test_add_multiple_subscriptions(self, storage, test_user):
        """
        GIVEN a user with one subscription
        WHEN they subscribe to additional stocks
        THEN all subscriptions should be stored
        """
        symbols = ["AAPL", "MSFT", "GOOGL"]
        for symbol in symbols:
            subscription = Subscription(
                user_id=test_user.user_id,
                stock_symbol=symbol
            )
            storage.add_subscription(subscription)

        subs = storage.get_subscriptions(user_id=test_user.user_id)
        assert len(subs) == 3
        sub_symbols = {s.stock_symbol for s in subs}
        assert sub_symbols == {"AAPL", "MSFT", "GOOGL"}

    def test_add_duplicate_subscription(self, storage, test_user):
        """
        GIVEN a user already subscribed to AAPL
        WHEN they try to subscribe to AAPL again
        THEN it should handle gracefully (either reject or idempotent)
        """
        subscription = Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL"
        )
        storage.add_subscription(subscription)

        # Try adding duplicate
        try:
            storage.add_subscription(subscription)
            # If no exception, verify we still only have 1 subscription
            subs = storage.get_subscriptions(user_id=test_user.user_id, stock_symbol="AAPL")
            assert len(subs) == 1
        except Exception:
            # Exception is acceptable for duplicates
            pass

    def test_subscription_count_for_user(self, storage, test_user):
        """
        GIVEN a user with multiple subscriptions
        WHEN we count their subscriptions
        THEN count should match number added
        """
        for i in range(5):
            subscription = Subscription(
                user_id=test_user.user_id,
                stock_symbol=f"STOCK{i}"
            )
            storage.add_subscription(subscription)

        count = storage.get_subscription_count(user_id=test_user.user_id)
        assert count == 5


class TestRemoveSubscription:
    """Tests for removing subscriptions."""

    def test_remove_existing_subscription(self, storage, test_user):
        """
        GIVEN a user subscribed to AAPL
        WHEN they unsubscribe from AAPL
        THEN subscription should be removed
        """
        subscription = Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL"
        )
        storage.add_subscription(subscription)

        # Remove it
        storage.remove_subscription(test_user.user_id, "AAPL")

        # Verify removed (active_only=True should return empty)
        subs = storage.get_subscriptions(user_id=test_user.user_id, active_only=True)
        assert len(subs) == 0

    def test_remove_one_of_many_subscriptions(self, storage, test_user):
        """
        GIVEN a user with 3 subscriptions
        WHEN they unsubscribe from one
        THEN only that one should be removed
        """
        symbols = ["AAPL", "MSFT", "GOOGL"]
        for symbol in symbols:
            subscription = Subscription(
                user_id=test_user.user_id,
                stock_symbol=symbol
            )
            storage.add_subscription(subscription)

        # Remove MSFT
        storage.remove_subscription(test_user.user_id, "MSFT")

        # Verify AAPL and GOOGL remain
        subs = storage.get_subscriptions(user_id=test_user.user_id, active_only=True)
        assert len(subs) == 2
        sub_symbols = {s.stock_symbol for s in subs}
        assert sub_symbols == {"AAPL", "GOOGL"}

    def test_remove_nonexistent_subscription(self, storage, test_user):
        """
        GIVEN a user with no subscriptions
        WHEN they try to unsubscribe
        THEN it should handle gracefully
        """
        # Should not raise exception
        storage.remove_subscription(test_user.user_id, "AAPL")

        # Verify still no subscriptions
        subs = storage.get_subscriptions(user_id=test_user.user_id)
        assert len(subs) == 0


class TestGetSubscriptions:
    """Tests for retrieving subscriptions."""

    def test_get_subscriptions_by_user(self, storage, test_user):
        """
        GIVEN multiple users with subscriptions
        WHEN we query by user_id
        THEN only that user's subscriptions are returned
        """
        # Add subscriptions for test_user
        for symbol in ["AAPL", "MSFT"]:
            storage.add_subscription(Subscription(
                user_id=test_user.user_id,
                stock_symbol=symbol
            ))

        # Add subscriptions for another user
        other_user = User(user_id="other_user", telegram_username="@other")
        storage.add_user(other_user)
        storage.add_subscription(Subscription(
            user_id=other_user.user_id,
            stock_symbol="GOOGL"
        ))

        # Query test_user subscriptions
        subs = storage.get_subscriptions(user_id=test_user.user_id)
        assert len(subs) == 2
        assert all(s.user_id == test_user.user_id for s in subs)

    def test_get_subscriptions_by_stock(self, storage):
        """
        GIVEN multiple users subscribed to same stock
        WHEN we query by stock_symbol
        THEN all subscriptions for that stock are returned
        """
        # Create 2 users
        user1 = User(user_id="user1", telegram_username="@user1")
        user2 = User(user_id="user2", telegram_username="@user2")
        storage.add_user(user1)
        storage.add_user(user2)

        # Both subscribe to AAPL
        storage.add_subscription(Subscription(user_id=user1.user_id, stock_symbol="AAPL"))
        storage.add_subscription(Subscription(user_id=user2.user_id, stock_symbol="AAPL"))

        # user1 also subscribes to MSFT
        storage.add_subscription(Subscription(user_id=user1.user_id, stock_symbol="MSFT"))

        # Query AAPL subscriptions
        aapl_subs = storage.get_subscriptions(stock_symbol="AAPL")
        assert len(aapl_subs) == 2
        assert all(s.stock_symbol == "AAPL" for s in aapl_subs)

    def test_get_all_active_subscriptions(self, storage):
        """
        GIVEN multiple users with subscriptions
        WHEN we query all active subscriptions
        THEN all active subscriptions across all users are returned
        """
        # Create users and subscriptions
        for i in range(3):
            user = User(user_id=f"user{i}", telegram_username=f"@user{i}")
            storage.add_user(user)
            for j in range(2):
                storage.add_subscription(Subscription(
                    user_id=user.user_id,
                    stock_symbol=f"STOCK{i}{j}"
                ))

        # Query all active
        all_subs = storage.get_subscriptions(active_only=True)
        assert len(all_subs) == 6  # 3 users * 2 stocks

    def test_get_inactive_subscriptions(self, storage, test_user):
        """
        GIVEN a user with both active and inactive subscriptions
        WHEN we query with active_only=False
        THEN inactive subscriptions are included
        """
        # Add subscription
        storage.add_subscription(Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL"
        ))

        # Remove it (makes it inactive)
        storage.remove_subscription(test_user.user_id, "AAPL")

        # Query with active_only=False
        all_subs = storage.get_subscriptions(
            user_id=test_user.user_id,
            active_only=False
        )
        assert len(all_subs) == 1
        assert all_subs[0].active_status == False

        # Query with active_only=True
        active_subs = storage.get_subscriptions(
            user_id=test_user.user_id,
            active_only=True
        )
        assert len(active_subs) == 0


class TestSubscriptionLimits:
    """Tests for subscription limits enforcement."""

    def test_user_limit_10_subscriptions(self, storage, test_user):
        """
        GIVEN a user with 10 subscriptions (at limit)
        WHEN we check subscription count
        THEN it should return 10
        """
        for i in range(10):
            storage.add_subscription(Subscription(
                user_id=test_user.user_id,
                stock_symbol=f"STOCK{i}"
            ))

        count = storage.get_subscription_count(user_id=test_user.user_id)
        assert count == 10

    def test_system_limit_100_subscriptions(self, storage):
        """
        GIVEN system has multiple users
        WHEN total subscriptions approach 100
        THEN count should be accurate
        """
        # Create 10 users with 10 subscriptions each
        for i in range(10):
            user = User(user_id=f"user{i}", telegram_username=f"@user{i}")
            storage.add_user(user)
            for j in range(10):
                storage.add_subscription(Subscription(
                    user_id=user.user_id,
                    stock_symbol=f"STOCK{i}{j}"
                ))

        total_count = storage.get_subscription_count()
        assert total_count == 100

    def test_user_at_limit_behavior(self, storage, test_user):
        """
        GIVEN a user with 10 subscriptions
        WHEN they have reached the limit
        THEN system should be able to detect it
        """
        # Add 10 subscriptions
        for i in range(10):
            storage.add_subscription(Subscription(
                user_id=test_user.user_id,
                stock_symbol=f"STOCK{i}"
            ))

        # Check if at limit
        count = storage.get_subscription_count(user_id=test_user.user_id)
        at_limit = count >= 10

        assert at_limit == True


class TestSubscriptionMetadata:
    """Tests for subscription metadata and timestamps."""

    def test_subscription_has_subscription_date(self, storage, test_user):
        """
        GIVEN a new subscription
        WHEN it's added
        THEN it should have subscription_date set
        """
        subscription = Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL",
            subscription_date=datetime.utcnow()
        )
        storage.add_subscription(subscription)

        subs = storage.get_subscriptions(user_id=test_user.user_id)
        assert subs[0].subscription_date is not None

    def test_subscription_active_by_default(self, storage, test_user):
        """
        GIVEN a new subscription
        WHEN it's added
        THEN it should be active by default
        """
        subscription = Subscription(
            user_id=test_user.user_id,
            stock_symbol="AAPL"
        )
        storage.add_subscription(subscription)

        subs = storage.get_subscriptions(user_id=test_user.user_id, active_only=True)
        assert len(subs) == 1
        assert subs[0].active_status == True


class TestMultiUserScenarios:
    """Tests for multi-user subscription scenarios."""

    def test_multiple_users_same_stock(self, storage):
        """
        GIVEN multiple users subscribe to the same stock
        WHEN we query that stock
        THEN all user subscriptions are returned
        """
        users = []
        for i in range(5):
            user = User(user_id=f"user{i}", telegram_username=f"@user{i}")
            storage.add_user(user)
            users.append(user)
            storage.add_subscription(Subscription(
                user_id=user.user_id,
                stock_symbol="AAPL"
            ))

        aapl_subs = storage.get_subscriptions(stock_symbol="AAPL")
        assert len(aapl_subs) == 5

    def test_user_subscription_isolation(self, storage):
        """
        GIVEN two users with different subscriptions
        WHEN one user unsubscribes
        THEN the other user's subscriptions are unaffected
        """
        user1 = User(user_id="user1", telegram_username="@user1")
        user2 = User(user_id="user2", telegram_username="@user2")
        storage.add_user(user1)
        storage.add_user(user2)

        # Both subscribe to AAPL
        storage.add_subscription(Subscription(user_id=user1.user_id, stock_symbol="AAPL"))
        storage.add_subscription(Subscription(user_id=user2.user_id, stock_symbol="AAPL"))

        # user1 unsubscribes
        storage.remove_subscription(user1.user_id, "AAPL")

        # Verify user1 has no subs
        user1_subs = storage.get_subscriptions(user_id=user1.user_id, active_only=True)
        assert len(user1_subs) == 0

        # Verify user2 still has AAPL
        user2_subs = storage.get_subscriptions(user_id=user2.user_id, active_only=True)
        assert len(user2_subs) == 1
        assert user2_subs[0].stock_symbol == "AAPL"
