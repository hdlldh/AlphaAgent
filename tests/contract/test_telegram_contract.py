"""
Contract tests for Telegram bot commands (User Story 2).

These tests define the expected behavior of the bot command handlers.
Tests are marked with [US2] for pytest filtering.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Mark all tests in this module with US2 and asyncio
pytestmark = [pytest.mark.US2, pytest.mark.asyncio]


@pytest.fixture
def mock_storage():
    """Mock storage for testing."""
    storage = MagicMock()
    storage.add_user = MagicMock()
    storage.get_user = MagicMock(return_value=None)
    storage.add_subscription = MagicMock()
    storage.remove_subscription = MagicMock()
    storage.get_subscriptions = MagicMock(return_value=[])
    storage.get_subscription_count = MagicMock(return_value=0)
    return storage


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


class TestStartCommand:
    """Contract tests for /start command."""

    async def test_start_command_creates_new_user(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a new user sends /start
        WHEN the start command handler is called
        THEN it should create a user and send welcome message
        """
        from stock_analyzer.bot import TelegramBot

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.start_command(mock_update, mock_context)

        # Should create user
        mock_storage.add_user.assert_called_once()

        # Should send welcome message
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "welcome" in message.lower() or "hello" in message.lower()

    async def test_start_command_for_existing_user(self, mock_storage, mock_update, mock_context):
        """
        GIVEN an existing user sends /start
        WHEN the start command handler is called
        THEN it should update last_active and send welcome message
        """
        from stock_analyzer.bot import TelegramBot
        from stock_analyzer.models import User

        # User already exists
        existing_user = User(
            user_id="12345",
            telegram_username="testuser",
            created_at=datetime.utcnow()
        )
        mock_storage.get_user = MagicMock(return_value=existing_user)

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.start_command(mock_update, mock_context)

        # Should not create new user
        mock_storage.add_user.assert_not_called()

        # Should send welcome message
        mock_update.message.reply_text.assert_called_once()


class TestHelpCommand:
    """Contract tests for /help command."""

    async def test_help_command_lists_all_commands(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user sends /help
        WHEN the help command handler is called
        THEN it should list all available commands
        """
        from stock_analyzer.bot import TelegramBot

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.help_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]

        # Should mention key commands
        assert "/subscribe" in message
        assert "/unsubscribe" in message
        assert "/list" in message


class TestSubscribeCommand:
    """Contract tests for /subscribe command."""

    async def test_subscribe_valid_symbol(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user sends /subscribe AAPL
        WHEN the subscribe command handler is called with valid symbol
        THEN it should add subscription and confirm
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["AAPL"]
        mock_storage.get_subscription_count.return_value = 5  # Under limit

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            # Mock successful symbol validation
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=mock_storage, token="test-token")
            await bot.subscribe_command(mock_update, mock_context)

        # Should add subscription
        mock_storage.add_subscription.assert_called_once()

        # Should confirm
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "AAPL" in message
        assert "subscribed" in message.lower() or "success" in message.lower()

    async def test_subscribe_missing_symbol(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user sends /subscribe without symbol
        WHEN the subscribe command handler is called
        THEN it should send usage error
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = []  # No symbol provided

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.subscribe_command(mock_update, mock_context)

        # Should NOT add subscription
        mock_storage.add_subscription.assert_not_called()

        # Should send error
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "usage" in message.lower() or "symbol" in message.lower()

    async def test_subscribe_invalid_symbol(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user sends /subscribe INVALID
        WHEN the subscribe command handler is called with invalid symbol
        THEN it should send error message
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["INVALID"]

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            # Mock failed symbol validation
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=False)

            bot = TelegramBot(storage=mock_storage, token="test-token")
            await bot.subscribe_command(mock_update, mock_context)

        # Should NOT add subscription
        mock_storage.add_subscription.assert_not_called()

        # Should send error
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "invalid" in message.lower() or "not found" in message.lower()

    async def test_subscribe_at_user_limit(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user has 10 subscriptions (at limit)
        WHEN they try to subscribe to another stock
        THEN it should reject with limit error
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["TSLA"]
        mock_storage.get_subscription_count.return_value = 10  # At limit

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.subscribe_command(mock_update, mock_context)

        # Should NOT add subscription
        mock_storage.add_subscription.assert_not_called()

        # Should send error
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "limit" in message.lower() or "maximum" in message.lower()

    async def test_subscribe_duplicate_symbol(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user is already subscribed to AAPL
        WHEN they try to subscribe to AAPL again
        THEN it should send appropriate message
        """
        from stock_analyzer.bot import TelegramBot
        from stock_analyzer.models import Subscription

        mock_context.args = ["AAPL"]
        mock_storage.get_subscription_count.return_value = 5

        # User already has AAPL subscription
        existing_sub = Subscription(user_id="12345", stock_symbol="AAPL")
        mock_storage.get_subscriptions.return_value = [existing_sub]

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            MockFetcher.return_value.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=mock_storage, token="test-token")
            await bot.subscribe_command(mock_update, mock_context)

        # Should send message (either error or confirmation)
        mock_update.message.reply_text.assert_called_once()


class TestUnsubscribeCommand:
    """Contract tests for /unsubscribe command."""

    async def test_unsubscribe_existing_subscription(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user is subscribed to AAPL
        WHEN they send /unsubscribe AAPL
        THEN it should remove subscription and confirm
        """
        from stock_analyzer.bot import TelegramBot
        from stock_analyzer.models import Subscription

        mock_context.args = ["AAPL"]
        existing_sub = Subscription(user_id="12345", stock_symbol="AAPL")
        mock_storage.get_subscriptions.return_value = [existing_sub]

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.unsubscribe_command(mock_update, mock_context)

        # Should remove subscription
        mock_storage.remove_subscription.assert_called_once()

        # Should confirm
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "AAPL" in message
        assert "unsubscribed" in message.lower() or "removed" in message.lower()

    async def test_unsubscribe_missing_symbol(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user sends /unsubscribe without symbol
        WHEN the unsubscribe command handler is called
        THEN it should send usage error
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = []  # No symbol provided

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.unsubscribe_command(mock_update, mock_context)

        # Should NOT remove subscription
        mock_storage.remove_subscription.assert_not_called()

        # Should send error
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "usage" in message.lower() or "symbol" in message.lower()

    async def test_unsubscribe_nonexistent_subscription(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user is NOT subscribed to TSLA
        WHEN they send /unsubscribe TSLA
        THEN it should send error message
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["TSLA"]
        mock_storage.get_subscriptions.return_value = []  # No subscription

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.unsubscribe_command(mock_update, mock_context)

        # Should NOT remove subscription
        mock_storage.remove_subscription.assert_not_called()

        # Should send error
        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "not subscribed" in message.lower() or "no subscription" in message.lower()


class TestListCommand:
    """Contract tests for /list command."""

    async def test_list_with_subscriptions(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user has 3 subscriptions
        WHEN they send /list
        THEN it should list all their subscriptions
        """
        from stock_analyzer.bot import TelegramBot
        from stock_analyzer.models import Subscription

        subscriptions = [
            Subscription(user_id="12345", stock_symbol="AAPL"),
            Subscription(user_id="12345", stock_symbol="MSFT"),
            Subscription(user_id="12345", stock_symbol="GOOGL"),
        ]
        mock_storage.get_subscriptions.return_value = subscriptions

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.list_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]

        # Should list all stocks
        assert "AAPL" in message
        assert "MSFT" in message
        assert "GOOGL" in message
        assert "3" in message  # Count

    async def test_list_with_no_subscriptions(self, mock_storage, mock_update, mock_context):
        """
        GIVEN a user has no subscriptions
        WHEN they send /list
        THEN it should inform them they have no subscriptions
        """
        from stock_analyzer.bot import TelegramBot

        mock_storage.get_subscriptions.return_value = []

        bot = TelegramBot(storage=mock_storage, token="test-token")
        await bot.list_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        message = mock_update.message.reply_text.call_args[0][0]

        # Should indicate no subscriptions
        assert "no" in message.lower() or "empty" in message.lower()


class TestErrorHandling:
    """Contract tests for error handling."""

    async def test_database_error_handling(self, mock_storage, mock_update, mock_context):
        """
        GIVEN database operation fails
        WHEN any command is executed
        THEN it should send user-friendly error message
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["AAPL"]
        mock_storage.add_subscription.side_effect = Exception("Database error")

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.validate_symbol = AsyncMock(return_value=True)

            bot = TelegramBot(storage=mock_storage, token="test-token")
            await bot.subscribe_command(mock_update, mock_context)

        # Should send error message to user
        mock_update.message.reply_text.assert_called()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "error" in message.lower() or "failed" in message.lower()

    async def test_network_error_handling(self, mock_storage, mock_update, mock_context):
        """
        GIVEN symbol validation fails due to network error
        WHEN /subscribe is called
        THEN it should handle gracefully with error message
        """
        from stock_analyzer.bot import TelegramBot

        mock_context.args = ["AAPL"]

        with patch('stock_analyzer.bot.StockFetcher') as MockFetcher:
            MockFetcher.return_value.validate_symbol = AsyncMock(
                side_effect=Exception("Network error")
            )

            bot = TelegramBot(storage=mock_storage, token="test-token")
            await bot.subscribe_command(mock_update, mock_context)

        # Should send error message
        mock_update.message.reply_text.assert_called()
        message = mock_update.message.reply_text.call_args[0][0]
        assert "could not" in message.lower() or "error" in message.lower() or "failed" in message.lower()
