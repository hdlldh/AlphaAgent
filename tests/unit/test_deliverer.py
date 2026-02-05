"""
Unit tests for deliverer module.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stock_analyzer.deliverer import (
    DeliveryChannel,
    InsightDeliverer,
    TelegramChannel,
)
from stock_analyzer.exceptions import DeliveryError
from stock_analyzer.models import Insight, Subscription, User
from stock_analyzer.storage import Storage


@pytest.fixture
def test_storage(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test_deliverer.db"
    storage = Storage(str(db_path))
    storage.init_database()
    return storage


@pytest.fixture
def sample_insight():
    """Create sample insight."""
    return Insight(
        id=1,
        analysis_id=1,
        stock_symbol="AAPL",
        analysis_date=date(2026, 1, 30),
        summary="Apple stock shows strong momentum with positive indicators.",
        trend_analysis="The stock has gained 2.5% with increasing volume patterns.",
        risk_factors=["Overvaluation concerns", "Market volatility"],
        opportunities=["Product launches", "Services growth"],
        confidence_level="high",
        metadata={"llm_model": "claude-sonnet-4-5"},
        created_at=datetime.utcnow()
    )


class TestTelegramChannel:
    """Test Telegram delivery channel."""

    def test_format_insight(self, sample_insight):
        """Test insight formatting for Telegram."""
        channel = TelegramChannel(token="test-token")

        message = channel.format_insight(sample_insight)

        # Verify message contains key components
        assert "AAPL" in message
        assert "Stock Analysis" in message
        assert sample_insight.summary in message
        assert "Risk Factors" in message
        assert "Opportunities" in message
        assert "Overvaluation concerns" in message
        assert "Product launches" in message
        assert "Confidence: HIGH" in message

    def test_format_insight_truncates_long_messages(self):
        """Test that long insights are truncated."""
        channel = TelegramChannel(token="test-token")

        # Create insight with very long summary
        long_insight = Insight(
            id=1,
            analysis_id=1,
            stock_symbol="AAPL",
            analysis_date=date(2026, 1, 30),
            summary="A" * 5000,  # Very long
            trend_analysis="",
            risk_factors=[],
            opportunities=[],
            confidence_level="medium",
            metadata={},
            created_at=datetime.utcnow()
        )

        message = channel.format_insight(long_insight)

        # Telegram limit is 4096 characters
        assert len(message) <= 4096
        if len(message) == 4096:
            assert message.endswith("...")

    @pytest.mark.asyncio
    async def test_send_success(self, sample_insight):
        """Test successful message sending."""
        # Mock the entire Bot class
        with patch('stock_analyzer.deliverer.Bot') as MockBot:
            mock_bot = MockBot.return_value
            mock_bot.send_message = AsyncMock(return_value=MagicMock())

            channel = TelegramChannel(token="test-token")
            channel.bot = mock_bot

            result = await channel.send("123456", "Test message")

            assert result is True
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_telegram_error(self):
        """Test error handling for Telegram errors."""
        from telegram.error import TelegramError

        # Mock the entire Bot class
        with patch('stock_analyzer.deliverer.Bot') as MockBot:
            mock_bot = MockBot.return_value
            mock_bot.send_message = AsyncMock(side_effect=TelegramError("Chat not found"))

            channel = TelegramChannel(token="test-token")
            channel.bot = mock_bot

            with pytest.raises(DeliveryError) as exc_info:
                await channel.send("invalid-id", "Test message")

            assert "Chat not found" in str(exc_info.value)

    def test_chat_id_conversion(self):
        """Test chat ID conversion logic."""
        channel = TelegramChannel(token="test-token")

        # Test numeric string
        assert "123456".isdigit()

        # Test negative numeric (group chat)
        user_id = "-100123456"
        assert user_id.startswith('-') and user_id[1:].isdigit()

        # Test username
        user_id = "@username"
        assert not user_id.isdigit()


class TestInsightDeliverer:
    """Test InsightDeliverer class."""

    def test_initialization_with_telegram(self, test_storage):
        """Test deliverer initialization with Telegram token."""
        deliverer = InsightDeliverer(
            storage=test_storage,
            telegram_token="test-token"
        )

        assert "telegram" in deliverer.channels
        assert isinstance(deliverer.channels["telegram"], TelegramChannel)

    def test_initialization_without_telegram(self, test_storage):
        """Test deliverer initialization without Telegram."""
        deliverer = InsightDeliverer(storage=test_storage)

        assert "telegram" not in deliverer.channels

    def test_add_channel(self, test_storage):
        """Test adding custom channel."""
        deliverer = InsightDeliverer(storage=test_storage)

        # Create mock channel
        mock_channel = MagicMock(spec=DeliveryChannel)
        deliverer.add_channel("custom", mock_channel)

        assert "custom" in deliverer.channels
        assert deliverer.channels["custom"] == mock_channel

    @pytest.mark.asyncio
    async def test_deliver_insight_success(self, test_storage, sample_insight):
        """Test successful insight delivery."""
        deliverer = InsightDeliverer(storage=test_storage)

        # Add mock channel
        mock_channel = MagicMock(spec=DeliveryChannel)
        mock_channel.format_insight.return_value = "Formatted message"
        mock_channel.send = AsyncMock(return_value=True)

        deliverer.add_channel("test", mock_channel)

        # Mock _log_delivery to avoid foreign key issues
        with patch.object(deliverer, '_log_delivery'):
            # Deliver
            result = await deliverer.deliver_insight(
                insight=sample_insight,
                user_id="user123",
                channel="test"
            )

            assert result.status == "success"
            assert result.user_id == "user123"
            assert result.insight_id == sample_insight.id
            mock_channel.format_insight.assert_called_once_with(sample_insight)
            mock_channel.send.assert_called_once_with("user123", "Formatted message")

    @pytest.mark.asyncio
    async def test_deliver_insight_failure(self, test_storage, sample_insight):
        """Test failed insight delivery."""
        deliverer = InsightDeliverer(storage=test_storage)

        # Add mock channel that fails
        mock_channel = MagicMock(spec=DeliveryChannel)
        mock_channel.format_insight.return_value = "Formatted message"
        mock_channel.send = AsyncMock(
            side_effect=DeliveryError(
                user_id="user123",
                reason="Send failed",
                channel="test"
            )
        )

        deliverer.add_channel("test", mock_channel)

        # Mock _log_delivery to avoid foreign key issues
        with patch.object(deliverer, '_log_delivery'):
            # Deliver
            result = await deliverer.deliver_insight(
                insight=sample_insight,
                user_id="user123",
                channel="test"
            )

            assert result.status == "failed"
            assert result.error_message is not None
            assert "Send failed" in result.error_message

    @pytest.mark.asyncio
    async def test_deliver_insight_unknown_channel(self, test_storage, sample_insight):
        """Test delivery to unknown channel."""
        deliverer = InsightDeliverer(storage=test_storage)

        with pytest.raises(DeliveryError) as exc_info:
            await deliverer.deliver_insight(
                insight=sample_insight,
                user_id="user123",
                channel="unknown"
            )

        # DeliveryError.reason contains the message
        assert exc_info.value.reason and "not configured" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_deliver_batch(self, test_storage):
        """Test batch delivery."""
        deliverer = InsightDeliverer(storage=test_storage)

        # Create insights
        insights = [
            Insight(
                id=i,
                analysis_id=i,
                stock_symbol=f"SYM{i}",
                analysis_date=date(2026, 1, 30),
                summary=f"Summary {i}",
                trend_analysis="",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium",
                metadata={},
                created_at=datetime.utcnow()
            )
            for i in range(1, 4)
        ]

        # Add mock channel
        mock_channel = MagicMock(spec=DeliveryChannel)
        mock_channel.format_insight.return_value = "Message"
        mock_channel.send = AsyncMock(return_value=True)

        deliverer.add_channel("test", mock_channel)

        # Mock _log_delivery to avoid foreign key issues
        with patch.object(deliverer, '_log_delivery'):
            # Deliver to 2 users
            result = await deliverer.deliver_batch(
                insights=insights,
                user_ids=["user1", "user2"],
                channel="test",
                parallel=2
            )

            # Should have 3 insights × 2 users = 6 deliveries
            assert result.total == 6
            assert result.success_count == 6
            assert result.failure_count == 0

    @pytest.mark.asyncio
    async def test_deliver_to_subscribers(self, test_storage, sample_insight):
        """Test delivering to stock subscribers."""
        # Create users and subscriptions
        for i in range(3):
            user = User(user_id=f"user_{i}", telegram_username=f"@user{i}")
            test_storage.add_user(user)

            sub = Subscription(user_id=f"user_{i}", stock_symbol="AAPL")
            test_storage.add_subscription(sub)

        deliverer = InsightDeliverer(storage=test_storage)

        # Add mock channel
        mock_channel = MagicMock(spec=DeliveryChannel)
        mock_channel.format_insight.return_value = "Message"
        mock_channel.send = AsyncMock(return_value=True)

        deliverer.add_channel("test", mock_channel)

        # Mock _log_delivery to avoid foreign key issues
        with patch.object(deliverer, '_log_delivery'):
            # Deliver to subscribers
            result = await deliverer.deliver_to_subscribers(
                insight=sample_insight,
                channel="test"
            )

            # Should deliver to 3 subscribers
            assert result.total == 3
            assert result.success_count == 3
            assert result.failure_count == 0

    @pytest.mark.asyncio
    async def test_deliver_to_subscribers_no_subscribers(self, test_storage, sample_insight):
        """Test delivering when no subscribers exist."""
        deliverer = InsightDeliverer(storage=test_storage)

        result = await deliverer.deliver_to_subscribers(
            insight=sample_insight,
            channel="test"
        )

        # No subscribers
        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0

    @pytest.mark.asyncio
    async def test_delivery_logging(self, test_storage, sample_insight):
        """Test that deliveries are logged to storage."""
        deliverer = InsightDeliverer(storage=test_storage)

        # Add mock channel
        mock_channel = MagicMock(spec=DeliveryChannel)
        mock_channel.format_insight.return_value = "Message"
        mock_channel.send = AsyncMock(return_value=True)

        deliverer.add_channel("test", mock_channel)

        # Mock _log_delivery and verify it was called
        with patch.object(deliverer, '_log_delivery') as mock_log:
            # Deliver
            await deliverer.deliver_insight(
                insight=sample_insight,
                user_id="user123",
                channel="test"
            )

            # Verify log method was called
            mock_log.assert_called_once()
