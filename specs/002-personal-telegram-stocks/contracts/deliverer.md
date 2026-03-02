# Deliverer Interface Contract: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Channel**: Telegram

## Overview

Insight delivery module for posting analysis results to Telegram channel. Simplified from multi-user version to support single-channel broadcast.

**Changes from Multi-User Version**:
- **REMOVED**: `deliver_to_subscribers()` (multi-user batch delivery)
- **ADDED**: `deliver_to_channel()` (single channel posting)
- **RETAINED**: `send()`, `format_insight()` (low-level methods unchanged)

---

## Channel Delivery

### deliver_to_channel()

Deliver insight to configured Telegram channel.

**Signature**:
```python
async def deliver_to_channel(
    self,
    insight: Insight,
    channel_id: str
) -> DeliveryResult:
    """
    Deliver insight to Telegram channel.

    Args:
        insight: Insight to deliver
        channel_id: Telegram channel ID (@channelname or -1001234567890)

    Returns:
        DeliveryResult with status and details

    Raises:
        DeliveryError: If delivery fails after retries
    """
```

**Contract**:
- Formats insight using `format_insight()`
- Posts message to Telegram channel using `send()`
- Logs delivery to database via `storage.create_delivery_log()`
- Handles Telegram rate limits with retry logic
- Returns delivery result with success/failure status

**Behavior**:
1. Format insight as Markdown message
2. Call `send(user_id=channel_id, message=formatted_message)`
3. On success: Log delivery with status "success" and telegram_message_id
4. On failure: Log delivery with status "failed" and error_message
5. Return DeliveryResult

**Test Assertions**:
```python
async def test_deliver_to_channel_success():
    """Contract: deliver_to_channel posts message and logs success."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = Insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        summary="Strong performance",
        trend_analysis="Upward momentum",
        risk_factors=["Market volatility"],
        opportunities=["iPhone demand"],
        confidence_level="high"
    )

    # Mock Telegram bot
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(return_value=Mock(message_id="123456"))

    deliverer = InsightDeliverer(storage=storage, telegram_token="fake_token")
    deliverer.channel.bot = mock_bot

    result = await deliverer.deliver_to_channel(
        insight=insight,
        channel_id="@testchannel"
    )

    assert result.status == "success"
    assert result.channel_id == "@testchannel"

    # Verify delivery logged
    logs = storage.get_delivery_logs(insight_id=insight.id)
    assert len(logs) == 1
    assert logs[0].delivery_status == "success"
    assert logs[0].channel_id == "@testchannel"

async def test_deliver_to_channel_failure():
    """Contract: deliver_to_channel logs failure on error."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = Insight(...)

    # Mock Telegram bot to raise error
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(side_effect=TelegramError("Channel not found"))

    deliverer = InsightDeliverer(storage=storage, telegram_token="fake_token")
    deliverer.channel.bot = mock_bot

    result = await deliverer.deliver_to_channel(
        insight=insight,
        channel_id="@invalidchannel"
    )

    assert result.status == "failed"
    assert "Channel not found" in result.error_message

    # Verify failure logged
    logs = storage.get_delivery_logs(insight_id=insight.id)
    assert len(logs) == 1
    assert logs[0].delivery_status == "failed"
    assert "Channel not found" in logs[0].error_message
```

---

## Low-Level Methods (Retained)

### send()

Send message via Telegram (low-level).

**Signature**:
```python
async def send(
    self,
    user_id: str,
    message: str
) -> bool:
    """
    Send message via Telegram.

    Args:
        user_id: Telegram chat ID (can be channel ID, e.g., @channel or -100123...)
        message: Message content (Markdown formatted)

    Returns:
        True if successful, False otherwise

    Raises:
        DeliveryError: If delivery fails after retries
    """
```

**Contract**: (Unchanged from multi-user version)
- Sends message to Telegram using `bot.send_message()`
- **Works for channels**: Just pass channel ID as user_id
- Handles rate limits with exponential backoff
- Retries up to 3 times on transient errors
- Raises DeliveryError on permanent failures

**Channel Support**:
- Public channels: `@channelname`
- Private channels: Numeric ID (e.g., `-1001234567890`)
- Bot must be admin with "Post Messages" permission

**Test Assertions**:
```python
async def test_send_to_channel():
    """Contract: send() works with channel IDs."""
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(return_value=Mock(message_id="123"))

    channel = TelegramChannel(token="fake_token")
    channel.bot = mock_bot

    success = await channel.send(
        user_id="@testchannel",
        message="Test message"
    )

    assert success is True
    mock_bot.send_message.assert_called_once_with(
        chat_id="@testchannel",
        text="Test message",
        parse_mode="Markdown"
    )

async def test_send_retries_on_rate_limit():
    """Contract: send() retries on rate limit errors."""
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(
        side_effect=[
            telegram.error.RetryAfter(retry_after=1),
            Mock(message_id="123")
        ]
    )

    channel = TelegramChannel(token="fake_token")
    channel.bot = mock_bot

    success = await channel.send(user_id="@channel", message="Test")

    assert success is True
    assert mock_bot.send_message.call_count == 2  # First failed, second succeeded
```

---

### format_insight()

Format insight as Markdown message.

**Signature**:
```python
def format_insight(
    self,
    insight: Insight
) -> str:
    """
    Format insight for Telegram channel.

    Args:
        insight: Insight to format

    Returns:
        Markdown-formatted message string
    """
```

**Contract**: (Unchanged from multi-user version)
- Formats insight as Markdown
- Includes stock symbol, date, summary, risks, opportunities
- Respects Telegram message length limit (4096 characters)
- Truncates if necessary with "..." indicator

**Output Format**:
```markdown
📊 *AAPL Analysis* | 2026-02-28 | Confidence: HIGH

*Summary*
Strong performance with 2.3% gain driven by solid iPhone demand.

*Trend Analysis*
Technical indicators suggest continued upward momentum...

*⚠️ Risk Factors*
• Market volatility concerns
• Regulatory pressures in EU

*🚀 Opportunities*
• Strong iPhone demand
• Services revenue growth
```

**Test Assertions**:
```python
def test_format_insight():
    """Contract: format_insight returns Markdown-formatted message."""
    channel = TelegramChannel(token="fake_token")

    insight = Insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        summary="Strong performance",
        trend_analysis="Upward momentum",
        risk_factors=["Market volatility", "Regulatory pressures"],
        opportunities=["iPhone demand", "Services growth"],
        confidence_level="high"
    )

    message = channel.format_insight(insight)

    assert "AAPL" in message
    assert "2026-02-28" in message
    assert "HIGH" in message
    assert "Strong performance" in message
    assert "Market volatility" in message
    assert "iPhone demand" in message

def test_format_insight_truncates_long_content():
    """Contract: format_insight truncates messages exceeding 4096 chars."""
    channel = TelegramChannel(token="fake_token")

    insight = Insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        summary="A" * 5000,  # Very long summary
        trend_analysis="B" * 5000,
        risk_factors=["Risk"],
        opportunities=["Opportunity"],
        confidence_level="high"
    )

    message = channel.format_insight(insight)

    assert len(message) <= 4096
    assert "..." in message  # Truncation indicator
```

---

## Data Transfer Objects

### DeliveryResult

Result of a single delivery operation.

**Structure**:
```python
@dataclass
class DeliveryResult:
    """Result of a delivery operation."""
    insight_id: int
    channel_id: str  # Changed from user_id
    status: str  # "success" or "failed"
    error_message: Optional[str] = None
    telegram_message_id: Optional[str] = None  # Telegram's message ID
```

**Fields**:
- `insight_id`: ID of delivered insight
- `channel_id`: Telegram channel identifier (NEW - replaces user_id)
- `status`: "success" or "failed"
- `error_message`: Error details if failed
- `telegram_message_id`: Telegram's unique message ID if successful

---

## Removed Methods

These methods are **no longer available** in the personal version:

### deliver_to_subscribers() (REMOVED)

Previously delivered insight to all users subscribed to a stock.

**Signature (old)**:
```python
async def deliver_to_subscribers(
    self,
    insight: Insight,
    channel: str = "telegram"
) -> BatchDeliveryResult:
    """
    Deliver insight to all subscribers of the stock.

    REMOVED: No longer needed for personal use.
    Use deliver_to_channel() instead.
    """
```

**Reason for Removal**: Multi-user batch delivery not needed for personal channel broadcasting.

**Migration**:
```python
# Before (multi-user)
result = await deliverer.deliver_to_subscribers(
    insight=insight,
    channel="telegram"
)

# After (personal)
result = await deliverer.deliver_to_channel(
    insight=insight,
    channel_id=config.telegram_channel
)
```

---

## Error Handling

### DeliveryError

Exception for delivery failures.

**Structure**:
```python
class DeliveryError(StockAnalyzerError):
    """Delivery operation failed."""
    def __init__(self, channel: str, message: str):
        self.channel = channel
        super().__init__(message)
```

**Common Errors**:
- **Channel not found**: Bot not added to channel, or channel doesn't exist
- **Permission denied**: Bot lacks "Post Messages" permission
- **Rate limit**: Too many messages sent (retry with backoff)
- **Message too long**: Message exceeds 4096 characters (truncate)

**Handling**:
```python
try:
    await deliverer.deliver_to_channel(insight, channel_id)
except DeliveryError as e:
    logger.error(f"Failed to deliver to {e.channel}: {e}")
    # Log to database with failed status
    storage.create_delivery_log(
        insight_id=insight.id,
        channel_id=e.channel,
        delivery_status="failed",
        error_message=str(e)
    )
```

---

## Rate Limiting

### Telegram API Limits

**Limits**:
- 30 messages/second per bot (across all channels)
- 20 messages/minute per channel/group

**Strategy**: Exponential backoff retry

**Implementation**:
```python
@retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
async def send(self, user_id: str, message: str) -> bool:
    """Send with automatic retry on rate limit."""
    try:
        result = await self.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=self.parse_mode
        )
        return True
    except telegram.error.RetryAfter as e:
        logger.warning(f"Rate limited. Retrying after {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        raise  # Retry decorator will handle it
```

**Test Assertions**:
```python
async def test_send_respects_rate_limits():
    """Contract: send() respects Telegram rate limits."""
    mock_bot = Mock()

    # First call: rate limited
    # Second call: success
    mock_bot.send_message = AsyncMock(
        side_effect=[
            telegram.error.RetryAfter(retry_after=1),
            Mock(message_id="123")
        ]
    )

    channel = TelegramChannel(token="fake_token")
    channel.bot = mock_bot

    start_time = time.time()
    success = await channel.send(user_id="@channel", message="Test")
    elapsed = time.time() - start_time

    assert success is True
    assert elapsed >= 1.0  # Waited for retry_after
    assert mock_bot.send_message.call_count == 2
```

---

## Channel Setup

### Prerequisites

1. **Create Telegram Channel**:
   - Open Telegram app
   - Menu → New Channel
   - Set name and description
   - Choose "Public" or "Private"

2. **Get Channel ID**:
   - **Public**: Channel username (e.g., `@mystockchannel`)
   - **Private**: Use `@userinfobot` to get numeric ID (e.g., `-1001234567890`)

3. **Add Bot as Admin**:
   - Open channel settings → Administrators
   - Add Bot → Grant "Post Messages" permission

4. **Configure Environment**:
   ```bash
   STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockchannel
   ```

### Verification

Test channel posting:
```python
from telegram import Bot

bot = Bot(token="your_token")
await bot.send_message(chat_id="@mystockchannel", text="Test message")
```

If successful, bot is configured correctly.

---

## Testing Strategy

### Contract Tests

```python
async def test_deliverer_posts_to_channel():
    """Contract: deliver_to_channel posts message to channel."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = create_test_insight()

    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(return_value=Mock(message_id="123"))

    deliverer = InsightDeliverer(storage=storage, telegram_token="fake")
    deliverer.channel.bot = mock_bot

    result = await deliverer.deliver_to_channel(
        insight=insight,
        channel_id="@testchannel"
    )

    # Verify message sent
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == "@testchannel"
    assert "AAPL" in call_args.kwargs["text"]

    # Verify result
    assert result.status == "success"
    assert result.channel_id == "@testchannel"

async def test_deliverer_handles_permission_error():
    """Contract: deliver_to_channel handles permission errors gracefully."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = create_test_insight()

    mock_bot = Mock()
    mock_bot.send_message = AsyncMock(
        side_effect=telegram.error.Forbidden("Bot is not a member of the channel")
    )

    deliverer = InsightDeliverer(storage=storage, telegram_token="fake")
    deliverer.channel.bot = mock_bot

    result = await deliverer.deliver_to_channel(
        insight=insight,
        channel_id="@testchannel"
    )

    assert result.status == "failed"
    assert "not a member" in result.error_message.lower()
```

### Integration Tests

```python
async def test_deliverer_integration_with_real_telegram():
    """Integration: Post real message to test Telegram channel."""
    config = Config.from_env()
    storage = Storage(":memory:")
    storage.init_database()

    deliverer = InsightDeliverer(
        storage=storage,
        telegram_token=config.telegram_token
    )

    insight = Insight(
        stock_symbol="AAPL",
        analysis_date=date.today(),
        summary="Integration test insight",
        trend_analysis="Test",
        risk_factors=["Test risk"],
        opportunities=["Test opportunity"],
        confidence_level="medium"
    )

    result = await deliverer.deliver_to_channel(
        insight=insight,
        channel_id=config.telegram_channel
    )

    assert result.status == "success"
    assert result.telegram_message_id is not None
```

---

## Summary

**Total Methods**: 3
- **Removed**: 1 (`deliver_to_subscribers`)
- **Added**: 1 (`deliver_to_channel`)
- **Unchanged**: 2 (`send`, `format_insight`)

**Key Changes**:
- `deliver_to_channel()` replaces `deliver_to_subscribers()` (single channel vs multi-user)
- `DeliveryResult.channel_id` replaces `DeliveryResult.user_id`
- `send()` unchanged - already works with channel IDs

**Migration Impact**: Simplified from O(n) multi-user delivery to O(1) single channel posting

**Status**: ✅ Deliverer Contract Complete
