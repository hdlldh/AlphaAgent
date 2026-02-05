"""
Integration tests for Telegram bot workflow (User Story 2).

These tests verify end-to-end bot command processing with database.
Tests are marked with [US2] for pytest filtering.
"""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from stock_analyzer.models import User, Subscription
from stock_analyzer.storage import Storage

# Mark all tests in this module with US2 and asyncio
pytestmark = [pytest.mark.US2, pytest.mark.asyncio]


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
def mock_update():
    """Mock Telegram Update object."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_chat.id = 12345
    update.message.text = ""
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context object."""
    context = MagicMock()
    context.args = []
    return context


class TestEndToEndSubscriptionWorkflow:
    """Integration tests for complete subscription workflows."""

    async def test_new_user_subscription_flow(self, storage, mock_update, mock_context):
        """
        GIVEN a brand new user
        WHEN they interact with the bot
        THEN complete workflow should work: start → subscribe → list → unsubscribe
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")

            # Step 1: New user sends /start
            await bot.start_command(mock_update, mock_context)

            # Verify user was created
            user = storage.get_user("12345")
            assert user is not None
            assert user.telegram_username == "@testuser"

            # Step 2: User subscribes to AAPL
            mock_context.args = ["AAPL"]
            await bot.subscribe_command(mock_update, mock_context)

            # Verify subscription added
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 1
            assert subs[0].stock_symbol == "AAPL"

            # Step 3: User lists subscriptions
            mock_context.args = []
            await bot.list_command(mock_update, mock_context)

            # Verify list was called successfully
            assert mock_update.message.reply_text.called

            # Step 4: User unsubscribes from AAPL
            mock_context.args = ["AAPL"]
            await bot.unsubscribe_command(mock_update, mock_context)

            # Verify subscription removed
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 0

    async def test_multi_stock_subscription_workflow(self, storage, mock_update, mock_context):
        """
        GIVEN a user wants to track multiple stocks
        WHEN they subscribe to multiple symbols
        THEN all subscriptions should be managed correctly
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")

            # Create user
            await bot.start_command(mock_update, mock_context)

            # Subscribe to multiple stocks
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
            for symbol in symbols:
                mock_context.args = [symbol]
                await bot.subscribe_command(mock_update, mock_context)

            # Verify all subscriptions added
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 5

            # Unsubscribe from 2 stocks
            for symbol in ["MSFT", "TSLA"]:
                mock_context.args = [symbol]
                await bot.unsubscribe_command(mock_update, mock_context)

            # Verify correct subscriptions remain
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 3
            sub_symbols = {s.stock_symbol for s in subs}
            assert sub_symbols == {"AAPL", "GOOGL", "AMZN"}

    async def test_subscription_limit_enforcement(self, storage, mock_update, mock_context):
        """
        GIVEN a user approaching subscription limit
        WHEN they try to exceed 10 subscriptions
        THEN limit should be enforced
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")

            # Create user
            await bot.start_command(mock_update, mock_context)

            # Subscribe to 10 stocks (at limit)
            for i in range(10):
                mock_context.args = [f"STOCK{i}"]
                await bot.subscribe_command(mock_update, mock_context)

            # Verify 10 subscriptions
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 10

            # Try to subscribe to 11th stock
            mock_update.message.reply_text.reset_mock()
            mock_context.args = ["STOCK11"]
            await bot.subscribe_command(mock_update, mock_context)

            # Verify limit error was sent
            assert mock_update.message.reply_text.called
            message = mock_update.message.reply_text.call_args[0][0]
            assert "limit" in message.lower() or "maximum" in message.lower()

            # Verify still only 10 subscriptions
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 10


class TestMultiUserScenarios:
    """Integration tests for multiple users interacting with bot."""

    async def test_two_users_independent_subscriptions(self, storage, mock_context):
        """
        GIVEN two different users
        WHEN they each manage their subscriptions
        THEN subscriptions should be isolated per user
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")

            # User 1
            update1 = MagicMock()
            update1.effective_user.id = 11111
            update1.effective_user.username = "user1"
            update1.effective_chat.id = 11111
            update1.message.reply_text = AsyncMock()

            # User 2
            update2 = MagicMock()
            update2.effective_user.id = 22222
            update2.effective_user.username = "user2"
            update2.effective_chat.id = 22222
            update2.message.reply_text = AsyncMock()

            # Both users start
            await bot.start_command(update1, mock_context)
            await bot.start_command(update2, mock_context)

            # User 1 subscribes to AAPL, MSFT
            for symbol in ["AAPL", "MSFT"]:
                mock_context.args = [symbol]
                await bot.subscribe_command(update1, mock_context)

            # User 2 subscribes to GOOGL, AMZN
            for symbol in ["GOOGL", "AMZN"]:
                mock_context.args = [symbol]
                await bot.subscribe_command(update2, mock_context)

            # Verify user 1's subscriptions
            user1_subs = storage.get_subscriptions(user_id="11111", active_only=True)
            assert len(user1_subs) == 2
            user1_symbols = {s.stock_symbol for s in user1_subs}
            assert user1_symbols == {"AAPL", "MSFT"}

            # Verify user 2's subscriptions
            user2_subs = storage.get_subscriptions(user_id="22222", active_only=True)
            assert len(user2_subs) == 2
            user2_symbols = {s.stock_symbol for s in user2_subs}
            assert user2_symbols == {"GOOGL", "AMZN"}

    async def test_multiple_users_same_stock(self, storage, mock_context):
        """
        GIVEN multiple users subscribe to the same stock
        WHEN daily analysis runs
        THEN each user should receive their own delivery
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")

            # Create 3 users, all subscribe to AAPL
            for user_id in [11111, 22222, 33333]:
                update = MagicMock()
                update.effective_user.id = user_id
                update.effective_user.username = f"user{user_id}"
                update.effective_chat.id = user_id
                update.message.reply_text = AsyncMock()

                await bot.start_command(update, mock_context)

                mock_context.args = ["AAPL"]
                await bot.subscribe_command(update, mock_context)

            # Verify all 3 users subscribed to AAPL
            aapl_subs = storage.get_subscriptions(stock_symbol="AAPL", active_only=True)
            assert len(aapl_subs) == 3


class TestErrorScenarios:
    """Integration tests for error handling."""

    async def test_invalid_symbol_subscription(self, storage, mock_update, mock_context):
        """
        GIVEN user tries to subscribe to invalid symbol
        WHEN validation fails
        THEN subscription should not be added
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            # Invalid symbol
            mock_fetcher.validate_symbol = AsyncMock(return_value=False)

            bot = TelegramBot(storage=storage, token="test-token")

            # Create user
            await bot.start_command(mock_update, mock_context)

            # Try to subscribe to invalid symbol
            mock_context.args = ["INVALID123"]
            await bot.subscribe_command(mock_update, mock_context)

            # Verify no subscription added
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 0

            # Verify error message sent
            assert mock_update.message.reply_text.called
            message = mock_update.message.reply_text.call_args[0][0]
            assert "invalid" in message.lower() or "not found" in message.lower()

    async def test_unsubscribe_without_subscription(self, storage, mock_update, mock_context):
        """
        GIVEN user has no subscriptions
        WHEN they try to unsubscribe
        THEN appropriate error message should be sent
        """
        from stock_analyzer.bot import TelegramBot

        bot = TelegramBot(storage=storage, token="test-token")

        # Create user
        await bot.start_command(mock_update, mock_context)

        # Try to unsubscribe without any subscriptions
        mock_context.args = ["AAPL"]
        await bot.unsubscribe_command(mock_update, mock_context)

        # Verify error message
        assert mock_update.message.reply_text.called
        message = mock_update.message.reply_text.call_args[0][0]
        assert "not subscribed" in message.lower() or "no subscription" in message.lower()

    async def test_database_persistence_across_bot_instances(self, storage, mock_update, mock_context):
        """
        GIVEN user subscribes via one bot instance
        WHEN new bot instance is created
        THEN subscriptions should persist
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            # First bot instance
            bot1 = TelegramBot(storage=storage, token="test-token")
            await bot1.start_command(mock_update, mock_context)

            mock_context.args = ["AAPL"]
            await bot1.subscribe_command(mock_update, mock_context)

            # Create second bot instance with same storage
            bot2 = TelegramBot(storage=storage, token="test-token")

            # List subscriptions via second bot
            mock_context.args = []
            await bot2.list_command(mock_update, mock_context)

            # Verify subscriptions persisted
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 1
            assert subs[0].stock_symbol == "AAPL"


class TestCommandValidation:
    """Integration tests for command input validation."""

    async def test_subscribe_without_arguments(self, storage, mock_update, mock_context):
        """
        GIVEN user sends /subscribe without symbol
        WHEN command is processed
        THEN usage error should be sent
        """
        from stock_analyzer.bot import TelegramBot

        bot = TelegramBot(storage=storage, token="test-token")
        await bot.start_command(mock_update, mock_context)

        mock_context.args = []  # No arguments
        await bot.subscribe_command(mock_update, mock_context)

        # Verify error message
        assert mock_update.message.reply_text.called
        message = mock_update.message.reply_text.call_args[0][0]
        assert "usage" in message.lower() or "symbol" in message.lower()

    async def test_unsubscribe_without_arguments(self, storage, mock_update, mock_context):
        """
        GIVEN user sends /unsubscribe without symbol
        WHEN command is processed
        THEN usage error should be sent
        """
        from stock_analyzer.bot import TelegramBot

        bot = TelegramBot(storage=storage, token="test-token")
        await bot.start_command(mock_update, mock_context)

        mock_context.args = []  # No arguments
        await bot.unsubscribe_command(mock_update, mock_context)

        # Verify error message
        assert mock_update.message.reply_text.called
        message = mock_update.message.reply_text.call_args[0][0]
        assert "usage" in message.lower() or "symbol" in message.lower()

    async def test_subscribe_case_insensitive(self, storage, mock_update, mock_context):
        """
        GIVEN user sends /subscribe aapl (lowercase)
        WHEN command is processed
        THEN it should be converted to uppercase and work
        """
        from stock_analyzer.bot import TelegramBot

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=storage, token="test-token")
            await bot.start_command(mock_update, mock_context)

            # Subscribe with lowercase
            mock_context.args = ["aapl"]
            await bot.subscribe_command(mock_update, mock_context)

            # Verify subscription stored as uppercase
            subs = storage.get_subscriptions(user_id="12345", active_only=True)
            assert len(subs) == 1
            assert subs[0].stock_symbol == "AAPL"
