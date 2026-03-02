# Research & Design Decisions: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Status**: Phase 0 Complete

## Overview

This document captures research findings and design decisions for refactoring the multi-user stock analyzer into a personal monitoring tool.

## Research Topics

### 1. Stock List Configuration

**Question**: How should the personal user configure their stock watchlist?

**Options Evaluated**:
1. **Environment variable (comma-separated)** - `STOCK_ANALYZER_STOCK_LIST="AAPL,MSFT,GOOGL"`
2. Configuration file (TOML/JSON) - `config.toml` with `stocks = ["AAPL", "MSFT"]`
3. Database table - `watchlist` table with stock symbols
4. Text file - `stocks.txt` with one symbol per line

**Decision**: Environment variable (Option 1)

**Rationale**:
- **Simplicity**: No additional file parsing logic required; leverages existing `Config.from_env()` pattern
- **GitHub Actions friendly**: Easy to configure in workflow secrets/variables without committing sensitive data
- **Backward compatible**: Existing config loading mechanism (`dotenv`) handles this naturally
- **Validation**: Can validate and sanitize (trim whitespace, deduplicate, filter empty) at runtime
- **Standard pattern**: Follows the existing `STOCK_ANALYZER_*` environment variable convention

**Alternatives Rejected**:
- **Option 2 (Config file)**: Adds file I/O complexity; requires TOML parsing library; less GitHub Actions friendly
- **Option 3 (Database table)**: Contradicts the goal of removing database complexity; requires separate management CLI
- **Option 4 (Text file)**: Requires file reading logic; version control of stock list creates unnecessary commits

**Implementation Details**:
```python
# In config.py
stock_list: str = ""  # Comma-separated stock symbols

@classmethod
def from_env(cls) -> "Config":
    return cls(
        stock_list=os.getenv("STOCK_ANALYZER_STOCK_LIST", ""),
        # ... other config
    )

def get_stock_symbols(self) -> List[str]:
    """Parse and validate stock list."""
    if not self.stock_list:
        return []

    # Split by comma, strip whitespace, filter empty, deduplicate
    symbols = [s.strip().upper() for s in self.stock_list.split(",")]
    symbols = [s for s in symbols if s]  # Remove empty strings
    symbols = list(dict.fromkeys(symbols))  # Deduplicate while preserving order

    return symbols
```

**Validation Strategy**:
- Empty list → Error on startup (exit with clear message)
- Invalid symbols → Warn and skip during analysis (don't block other stocks)
- Duplicate symbols → Deduplicate automatically
- Whitespace → Strip automatically
- Mixed case → Normalize to uppercase

---

### 2. Telegram Channel Posting

**Question**: How should the bot post insights to a Telegram channel?

**Options Evaluated**:
1. **Bot with channel admin privileges** - Bot posts to channel using `send_message(chat_id=channel_id)`
2. **Webhook to channel** - Use Telegram webhook API (more complex)
3. **Manual forwarding** - Bot sends to user, user forwards to channel (not automated)

**Decision**: Bot with channel admin privileges (Option 1)

**Rationale**:
- **Standard Telegram Bot API**: Uses `telegram.Bot.send_message()` with channel ID (same API as user messages)
- **Channel ID format**: Supports both `@channelname` (public) or numeric ID (private channels)
- **Setup steps**: User creates channel → adds bot as admin → bot can post
- **No code changes needed**: Existing `TelegramChannel.send()` method works for channels if bot has permission
- **Rate limits**: Same as user messages (30 msg/s per bot)

**Alternatives Rejected**:
- **Option 2 (Webhook)**: Over-engineered for this use case; requires server to receive webhooks
- **Option 3 (Manual forwarding)**: Not automated; defeats the purpose of the refactoring

**Channel vs Group**:
- **Channel**: One-way broadcast, bot can post, users cannot reply → **RECOMMENDED** for personal monitoring
- **Group**: Two-way discussion, bot and users can post → Not needed for personal use

**Implementation Details**:
```python
# In config.py
telegram_channel: Optional[str] = None  # Channel ID or @username

@classmethod
def from_env(cls) -> "Config":
    return cls(
        telegram_channel=os.getenv("STOCK_ANALYZER_TELEGRAM_CHANNEL"),
        # ... other config
    )

# In deliverer.py - existing code works!
async def send(self, user_id: str, message: str) -> bool:
    """
    Send message via Telegram.

    Args:
        user_id: Telegram chat ID (can be username, numeric ID, or CHANNEL ID)
        message: Message to send
    """
    # This already works for channels! Just pass channel ID as user_id
    await self.bot.send_message(chat_id=user_id, text=message, parse_mode=self.parse_mode)
```

**Channel Setup Instructions** (for quickstart.md):
1. Create a Telegram channel via Telegram app
2. Get channel ID:
   - For public channels: `@channelname`
   - For private channels: Use `@userinfobot` or Telegram API to get numeric ID (e.g., `-1001234567890`)
3. Add bot as channel administrator with "Post Messages" permission
4. Set environment variable: `STOCK_ANALYZER_TELEGRAM_CHANNEL=@channelname`

**Error Handling**:
- Channel not found → Clear error: "Channel not found. Ensure bot is added as admin."
- Permission denied → Clear error: "Bot lacks permission to post. Grant 'Post Messages' permission."
- Rate limit → Retry with exponential backoff (existing retry logic applies)

---

### 3. Database Migration Strategy

**Question**: How should we handle database schema changes (removing users and subscriptions)?

**Options Evaluated**:
1. **Drop tables only** - `DROP TABLE IF EXISTS users, subscriptions;`
2. **Drop and remove foreign keys** - Drop tables + remove user_id FK from insights/delivery_logs
3. **Create migration script** - Versioned migration with rollback support
4. **Keep tables but ignore** - Leave schema intact, just don't use tables

**Decision**: Drop tables and remove foreign keys (Option 2)

**Rationale**:
- **Simplicity**: Single SQL migration script run during `init_database()` check
- **Backward compatibility**: Existing `insights` and `analyses` tables remain; historical data preserved
- **No data loss**: Historical analyses are retained (no user_id association needed for personal use)
- **Clean schema**: Removes unused tables and constraints; reduces maintenance burden
- **Safe migration**: Check if tables exist before dropping (idempotent operation)

**Alternatives Rejected**:
- **Option 1 (Drop only)**: Leaves orphaned foreign key constraints; causes errors on insert
- **Option 3 (Migration script)**: Over-engineered for a personal tool; no multi-version support needed
- **Option 4 (Keep tables)**: Violates simplicity principle; leaves dead code in schema

**Implementation Details**:
```python
# In storage.py - init_database()
def init_database(self):
    """Create or migrate database schema."""
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
        # Migration: Drop multi-user tables if they exist
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        cursor.execute("DROP TABLE IF EXISTS users")

        # Create stock_analyses table (NO user_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                price_snapshot REAL NOT NULL,
                price_change_percent REAL,
                volume INTEGER,
                analysis_status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL,
                duration_seconds REAL,
                UNIQUE(stock_symbol, analysis_date)
            )
        """)

        # Create insights table (NO user_id, NO analysis_id FK)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                trend_analysis TEXT NOT NULL,
                risk_factors TEXT NOT NULL,  -- JSON array
                opportunities TEXT NOT NULL,  -- JSON array
                confidence_level TEXT NOT NULL,
                metadata TEXT,  -- JSON object
                created_at TEXT NOT NULL
            )
        """)

        # Create delivery_logs table (NO user_id, channel_id instead)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,  -- Telegram channel ID
                delivery_status TEXT NOT NULL DEFAULT 'pending',
                delivery_method TEXT NOT NULL DEFAULT 'telegram',
                delivered_at TEXT,
                error_message TEXT,
                telegram_message_id TEXT,
                FOREIGN KEY (insight_id) REFERENCES insights(id)
            )
        """)

        # Create analysis_jobs table (unchanged)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT NOT NULL,
                completion_time TEXT,
                job_status TEXT NOT NULL DEFAULT 'running',
                stocks_scheduled INTEGER NOT NULL,
                stocks_processed INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                insights_delivered INTEGER DEFAULT 0,
                errors TEXT,  -- JSON array
                duration_seconds REAL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_symbol_date ON insights(stock_symbol, analysis_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_symbol_date ON stock_analyses(stock_symbol, analysis_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_delivery_logs_insight ON delivery_logs(insight_id)")

        conn.commit()

    finally:
        conn.close()
```

**Migration Safety**:
- Idempotent: Safe to run multiple times (IF EXISTS checks)
- No data loss: Historical insights/analyses preserved
- Backward compatible: Existing analyses remain queryable
- Forward only: No rollback needed (personal use, no production users)

---

### 4. Bot Removal Strategy

**Question**: Should we delete the bot code or just disable it?

**Options Evaluated**:
1. **Delete bot.py and run_bot.py** - Remove files entirely
2. **Disable bot commands** - Keep files, comment out command handlers
3. **Keep for future use** - Leave bot intact but undocumented

**Decision**: Delete bot files (Option 1)

**Rationale**:
- **Simplicity**: Removes unused code; reduces maintenance burden
- **Git history**: Code is preserved in version control if needed later
- **Clear intent**: Signals that interactive bot is not part of personal use
- **Test cleanup**: Removes associated bot tests (cleaner test suite)
- **Fewer dependencies**: No need to maintain bot-specific test fixtures

**Alternatives Rejected**:
- **Option 2 (Disable)**: Leaves dead code; tests still reference disabled commands
- **Option 3 (Keep)**: Violates YAGNI principle; adds confusion about supported features

**Files to Remove**:
- `src/stock_analyzer/bot.py` - Telegram bot with interactive commands
- `src/scripts/run_bot.py` - Bot startup script
- `tests/contract/test_telegram_contract.py` - Bot command contract tests (portions testing bot commands)
- `.github/workflows/telegram-bot.yml` - Bot deployment workflow

**Files to Keep** (used by deliverer):
- `src/stock_analyzer/deliverer.py` - Channel posting functionality (refactored, not removed)
- `telegram` dependency (python-telegram-bot) - Still needed for channel posting

**Deliverer Refactoring**:
```python
# Before (multi-user)
async def deliver_to_subscribers(self, insight: Insight, channel: str) -> BatchDeliveryResult:
    """Deliver insight to all subscribers of the stock."""
    subscriptions = self.storage.get_subscriptions(stock_symbol=insight.stock_symbol, active_only=True)

    for sub in subscriptions:
        await self.send(user_id=sub.user_id, message=formatted_message)

# After (personal)
async def deliver_to_channel(self, insight: Insight) -> DeliveryResult:
    """Deliver insight to configured Telegram channel."""
    channel_id = self.channel_id  # From config
    formatted_message = self.format_insight(insight)

    await self.send(user_id=channel_id, message=formatted_message)  # Same API!
```

---

## Best Practices

### Environment Variable Validation

**Pattern**: Fail fast on startup with clear error messages

```python
def validate(self) -> None:
    """Validate configuration."""
    # ... existing validations ...

    # Stock list validation
    if not self.stock_list:
        raise ValueError(
            "STOCK_ANALYZER_STOCK_LIST is required. "
            "Set it to a comma-separated list of stock symbols (e.g., 'AAPL,MSFT,GOOGL')."
        )

    # Channel validation
    if not self.telegram_channel:
        raise ValueError(
            "STOCK_ANALYZER_TELEGRAM_CHANNEL is required. "
            "Set it to your channel ID (e.g., '@mychannel' or '-1001234567890')."
        )
```

### Error Handling for Invalid Symbols

**Pattern**: Warn and continue (don't block entire job)

```python
# In daily_analysis.py
for symbol in config.get_stock_symbols():
    try:
        # Validate symbol
        if not fetcher.is_valid_symbol(symbol):
            logger.warning(f"Invalid stock symbol: {symbol}. Skipping.")
            continue

        # Analyze
        insight = await analyzer.analyze_stock(symbol)
        success_count += 1

    except Exception as e:
        logger.error(f"Failed to analyze {symbol}: {e}", exc_info=True)
        failure_count += 1
        continue  # Continue with next stock
```

### Telegram Channel Rate Limiting

**Pattern**: Use existing retry logic with exponential backoff

```python
# In deliverer.py (existing pattern applies)
@retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
async def send(self, user_id: str, message: str) -> bool:
    """Send with automatic retry on rate limit errors."""
    try:
        await self.bot.send_message(chat_id=user_id, text=message, parse_mode=self.parse_mode)
        return True
    except telegram.error.RetryAfter as e:
        logger.warning(f"Rate limited. Retrying after {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        raise  # Retry decorator will handle it
```

---

## Integration Patterns

### Daily Job Workflow

**Before (Multi-User)**:
```text
1. Load config
2. Get all active subscriptions from database
3. Extract unique stock symbols
4. Analyze each stock
5. For each insight:
   - Get subscribers for that stock
   - Deliver to each subscriber's Telegram chat
```

**After (Personal)**:
```text
1. Load config
2. Parse stock list from STOCK_ANALYZER_STOCK_LIST
3. Validate and deduplicate symbols
4. Analyze each stock
5. For each insight:
   - Post to STOCK_ANALYZER_TELEGRAM_CHANNEL
```

**Simplification**: Removes 2 database queries (subscriptions, users) and O(n*m) delivery loop (n=stocks, m=subscribers per stock). New flow is O(n) with single channel delivery.

---

## Summary of Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Stock List Configuration** | Environment variable (comma-separated) | Simplicity, GitHub Actions friendly, follows existing pattern |
| **Telegram Posting** | Bot with channel admin privileges | Standard API, same as user messages, easy setup |
| **Database Migration** | Drop tables, remove foreign keys | Clean schema, preserves historical data, idempotent |
| **Bot Code** | Delete bot files | Remove unused code, Git preserves history, reduce maintenance |
| **Validation** | Fail fast on startup | Clear error messages, prevent runtime failures |
| **Error Handling** | Warn and continue for invalid symbols | Don't block entire job due to one bad symbol |
| **Rate Limiting** | Use existing retry logic | Exponential backoff, handles Telegram rate limits |

**Phase 0 Status**: ✅ Complete - All design decisions documented and justified.

**Next Phase**: Phase 1 - Data Model & Contracts
