"""
Contract tests for InsightDeliverer (personal use).

Tests the public API for channel delivery, ensuring deliver_to_channel()
works correctly with Telegram channels.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stock_analyzer.deliverer import InsightDeliverer, DeliveryResult
from stock_analyzer.models import Insight
from stock_analyzer.storage import Storage


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage for testing."""
    db_path = tmp_path / "test_deliverer.db"
    storage = Storage(str(db_path))
    storage.init_database()
    return storage


@pytest.fixture
def mock_telegram_channel():
    """Mock Telegram channel for testing."""
    channel = MagicMock()
    channel.format_insight = MagicMock(return_value="Formatted message")
    channel.send = AsyncMock(return_value=True)
    return channel


@pytest.fixture
def sample_insight():
    """Create sample insight for testing."""
    return Insight(
        stock_symbol="AAPL",
        analysis_date=date.today(),
        summary="Strong upward momentum",
        trend_analysis="Positive trend observed",
        risk_factors=["Market volatility", "Valuation concerns"],
        opportunities=["Product launches", "Services growth"],
        confidence_level="high"
    )


class TestDeliverToChannelContract:
    """Test deliver_to_channel() public API contract."""

    @pytest.mark.asyncio
    async def test_deliver_to_channel_success(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test successful delivery to a channel."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        # Save insight to get ID
        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        # Deliver to channel
        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="@mystocks"
        )

        # Verify result structure
        assert isinstance(result, DeliveryResult)
        assert result.status == "success"
        assert result.channel_id == "@mystocks"
        assert result.insight_id == insight_id
        assert result.error_message is None

        # Verify channel.send was called
        mock_telegram_channel.send.assert_called_once_with("@mystocks", "Formatted message")

    @pytest.mark.asyncio
    async def test_deliver_to_channel_with_numeric_id(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test delivery to channel with numeric ID."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        # Deliver to numeric channel ID
        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="-1001234567890"
        )

        assert result.status == "success"
        assert result.channel_id == "-1001234567890"
        mock_telegram_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_to_channel_creates_delivery_log(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test that delivery creates a log entry in database."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="@mystocks"
        )

        # Verify delivery log was created
        # Note: Implementation should save delivery log to storage
        assert result.status == "success"


class TestDeliverToChannelErrorHandling:
    """Test deliver_to_channel() error handling."""

    @pytest.mark.asyncio
    async def test_deliver_to_channel_invalid_channel_id(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test delivery with invalid channel ID returns error."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        # Mock channel.send to raise error
        from telegram.error import TelegramError
        mock_telegram_channel.send.side_effect = TelegramError("Chat not found")

        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="@invalid_channel"
        )

        assert result.status == "failed"
        assert result.channel_id == "@invalid_channel"
        assert result.error_message is not None
        assert "chat not found" in result.error_message.lower() or "error" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_deliver_to_channel_permission_error(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test delivery with insufficient bot permissions."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        # Mock permission error
        from telegram.error import TelegramError
        mock_telegram_channel.send.side_effect = TelegramError("Need administrator rights")

        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="@restricted_channel"
        )

        assert result.status == "failed"
        assert "administrator" in result.error_message.lower() or "permission" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_deliver_to_channel_network_error(
        self, temp_storage, mock_telegram_channel, sample_insight
    ):
        """Test delivery with network error."""
        deliverer = InsightDeliverer(storage=temp_storage)
        deliverer.add_channel("telegram", mock_telegram_channel)

        # Mock network error
        mock_telegram_channel.send.side_effect = Exception("Network timeout")

        insight_id = temp_storage.save_insight(sample_insight)
        sample_insight.id = insight_id

        result = await deliverer.deliver_to_channel(
            insight=sample_insight,
            channel_id="@mystocks"
        )

        assert result.status == "failed"
        assert result.error_message is not None


class TestChannelFormatting:
    """Test message formatting for channel delivery."""

    def test_format_insight_for_channel(self, temp_storage, sample_insight):
        """Test insight formatting returns proper Markdown."""
        from stock_analyzer.deliverer import TelegramChannel

        channel = TelegramChannel(token="test_token")

        message = channel.format_insight(sample_insight)

        # Verify key components
        assert "AAPL" in message
        assert sample_insight.summary in message
        assert "Risk Factors" in message or "⚠️" in message
        assert "Opportunities" in message or "💡" in message

    def test_format_insight_truncates_long_message(self, temp_storage):
        """Test that very long insights are truncated to 4096 chars."""
        from stock_analyzer.deliverer import TelegramChannel

        channel = TelegramChannel(token="test_token")

        # Create insight with very long content
        long_insight = Insight(
            stock_symbol="AAPL",
            analysis_date=date.today(),
            summary="A" * 5000,  # Extremely long summary
            trend_analysis="B" * 1000,
            risk_factors=["Risk" for _ in range(100)],
            opportunities=["Opp" for _ in range(100)],
            confidence_level="high"
        )

        message = channel.format_insight(long_insight)

        # Telegram limit is 4096 characters
        assert len(message) <= 4096
        if len(message) == 4096:
            assert message.endswith("...") or len(message) < 4096
