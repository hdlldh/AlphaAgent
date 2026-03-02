# Data Model: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Status**: Phase 1 Complete

## Overview

Simplified data model for personal stock monitoring. Removes multi-user tables (`users`, `subscriptions`) and their foreign key relationships. Retains analysis and insight storage for historical queries.

## Schema Changes

### Removed Tables

#### Users (DELETED)
Previously tracked Telegram users receiving insights.

**Why Removed**: Single-user personal application doesn't need user management.

#### Subscriptions (DELETED)
Previously tracked per-user stock subscriptions with limits.

**Why Removed**: Stock list is now configured via environment variable, not database.

---

### Modified Tables

#### insights (MODIFIED)
AI-generated analysis content for stocks.

**Changes**:
- **REMOVED**: `analysis_id` foreign key (simplified relationship)
- **REMOVED**: `user_id` (no longer associated with users)
- **RETAINED**: All analysis content fields

**Schema**:
```sql
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_symbol TEXT NOT NULL,            -- Stock ticker (e.g., "AAPL")
    analysis_date TEXT NOT NULL,           -- Date of analysis (YYYY-MM-DD)
    summary TEXT NOT NULL,                 -- Brief summary (1-2 sentences)
    trend_analysis TEXT NOT NULL,          -- LLM-generated trend interpretation
    risk_factors TEXT NOT NULL,            -- JSON array of risk strings
    opportunities TEXT NOT NULL,           -- JSON array of opportunity strings
    confidence_level TEXT NOT NULL,        -- "high", "medium", or "low"
    metadata TEXT,                         -- JSON object (LLM provider, tokens, etc.)
    created_at TEXT NOT NULL              -- Timestamp (ISO 8601 format)
);

CREATE INDEX idx_insights_symbol_date ON insights(stock_symbol, analysis_date);
```

**Field Details**:
- `risk_factors`: JSON array, e.g., `["Market volatility", "Regulatory risks"]`
- `opportunities`: JSON array, e.g., `["Strong earnings growth", "New product launch"]`
- `metadata`: JSON object, e.g., `{"provider": "anthropic", "model": "claude-sonnet-4-5", "tokens": 1543}`

**Validation Rules**:
- `stock_symbol`: Uppercase, 1-5 characters, alphanumeric
- `confidence_level`: Must be "high", "medium", or "low"
- `risk_factors`, `opportunities`: Valid JSON arrays
- `metadata`: Valid JSON object

#### delivery_logs (MODIFIED)
Tracks delivery of insights to Telegram channel.

**Changes**:
- **REMOVED**: `user_id` foreign key
- **ADDED**: `channel_id` - Telegram channel identifier
- **RETAINED**: Delivery status and error tracking

**Schema**:
```sql
CREATE TABLE delivery_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,           -- References insights.id
    channel_id TEXT NOT NULL,              -- Telegram channel ID (@channel or -100123...)
    delivery_status TEXT NOT NULL DEFAULT 'pending',  -- "success", "failed", "pending"
    delivery_method TEXT NOT NULL DEFAULT 'telegram',
    delivered_at TEXT,                     -- Timestamp when delivered (ISO 8601)
    error_message TEXT,                    -- Error details if failed
    telegram_message_id TEXT,              -- Telegram message ID for reference
    FOREIGN KEY (insight_id) REFERENCES insights(id)
);

CREATE INDEX idx_delivery_logs_insight ON delivery_logs(insight_id);
```

**Field Details**:
- `channel_id`: Telegram channel identifier (e.g., `@mystockchannel` or `-1001234567890`)
- `delivery_status`: "success" (delivered), "failed" (error), "pending" (not yet attempted)
- `telegram_message_id`: Telegram's unique message identifier for tracking

**Validation Rules**:
- `delivery_status`: Must be "success", "failed", or "pending"
- `delivery_method`: Must be "telegram" (extensible for future methods)

---

### Unchanged Tables

#### stock_analyses
Tracks individual analysis runs for stocks.

**Schema** (unchanged):
```sql
CREATE TABLE stock_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_symbol TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    price_snapshot REAL NOT NULL,
    price_change_percent REAL,
    volume INTEGER,
    analysis_status TEXT NOT NULL DEFAULT 'pending',  -- "success", "failed", "pending"
    error_message TEXT,
    created_at TEXT NOT NULL,
    duration_seconds REAL,
    UNIQUE(stock_symbol, analysis_date)  -- Prevent duplicate analyses
);

CREATE INDEX idx_analyses_symbol_date ON stock_analyses(stock_symbol, analysis_date);
```

**Purpose**: Track analysis execution metadata (price, status, duration) separate from insight content.

#### analysis_jobs
Tracks daily analysis workflow execution.

**Schema** (unchanged):
```sql
CREATE TABLE analysis_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_time TEXT NOT NULL,          -- Job start time
    completion_time TEXT,                  -- Job end time
    job_status TEXT NOT NULL DEFAULT 'running',  -- "running", "completed", "failed"
    stocks_scheduled INTEGER NOT NULL,     -- Number of stocks to analyze
    stocks_processed INTEGER DEFAULT 0,    -- Number actually processed
    success_count INTEGER DEFAULT 0,       -- Successful analyses
    failure_count INTEGER DEFAULT 0,       -- Failed analyses
    insights_delivered INTEGER DEFAULT 0,  -- Insights successfully delivered
    errors TEXT,                           -- JSON array of error messages
    duration_seconds REAL                  -- Total job duration
);
```

**Purpose**: Track daily job execution for monitoring and debugging.

---

## Entity Relationships

### Before (Multi-User)
```text
users (1) ─── (M) subscriptions (M) ─── (1) stock_analyses
                                                 │
                                                 ▼
                                            insights (1) ─── (M) delivery_logs
                                                 │
                                                 ▼
                                            users (via user_id FK)
```

### After (Personal)
```text
stock_analyses (1) ─── (1) insights
                              │
                              ▼
                        delivery_logs (channel_id: TEXT)
                              │
                              ▼
                        Telegram Channel (external)
```

**Simplification**: Removed 2 entity types (`users`, `subscriptions`) and 3 foreign key relationships.

---

## Data Model Classes

### Removed Models

```python
# DELETED from models.py
@dataclass
class User:
    """REMOVED - No longer needed for personal use."""
    pass

@dataclass
class Subscription:
    """REMOVED - Stock list is now environment-configured."""
    pass
```

### Modified Models

```python
@dataclass
class Insight:
    """
    AI-generated analysis content for a stock.

    Changes from multi-user version:
    - REMOVED: user_id association
    - REMOVED: analysis_id foreign key (simplified)
    """
    stock_symbol: str
    analysis_date: date
    summary: str
    trend_analysis: str
    risk_factors: List[str]
    opportunities: List[str]
    confidence_level: Literal["high", "medium", "low"]
    id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DeliveryLog:
    """
    Tracks delivery of insights to Telegram channel.

    Changes from multi-user version:
    - REMOVED: user_id (replaced with channel_id)
    - ADDED: channel_id (Telegram channel identifier)
    """
    insight_id: int
    channel_id: str  # NEW: Telegram channel ID
    delivery_status: Literal["success", "failed", "pending"] = "pending"
    delivery_method: str = "telegram"
    id: Optional[int] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    telegram_message_id: Optional[str] = None
```

### Unchanged Models

```python
@dataclass
class StockAnalysis:
    """Tracks analysis execution metadata (unchanged)."""
    stock_symbol: str
    analysis_date: date
    price_snapshot: float
    analysis_status: Literal["success", "failed", "pending"] = "pending"
    id: Optional[int] = None
    price_change_percent: Optional[float] = None
    volume: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None

@dataclass
class AnalysisJob:
    """Tracks daily job execution (unchanged)."""
    execution_time: datetime
    stocks_scheduled: int
    job_status: Literal["running", "completed", "failed"] = "running"
    id: Optional[int] = None
    completion_time: Optional[datetime] = None
    stocks_processed: int = 0
    success_count: int = 0
    failure_count: int = 0
    insights_delivered: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: Optional[float] = None

@dataclass
class StockData:
    """Stock market data from APIs (unchanged)."""
    symbol: str
    current_price: float
    price_change_percent: float
    volume: int
    historical_prices: pd.DataFrame
    fundamentals: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResponse:
    """Response from LLM API (unchanged)."""
    text: str
    tokens_used: int
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Migration Script

### Schema Migration

```python
def init_database(self):
    """
    Initialize or migrate database schema.

    Migration from multi-user to personal:
    1. Drop users and subscriptions tables
    2. Create simplified schema without user FKs
    3. Preserve existing insights and analyses
    """
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
        # MIGRATION STEP 1: Drop multi-user tables
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        cursor.execute("DROP TABLE IF EXISTS users")

        # MIGRATION STEP 2: Create simplified tables
        # (See schema definitions above)

        # MIGRATION STEP 3: Existing data preserved
        # insights and analyses tables are recreated with IF NOT EXISTS
        # so existing data is retained

        conn.commit()
        logger.info("Database schema initialized successfully")

    except sqlite3.Error as e:
        conn.rollback()
        raise StorageError("schema_init", f"Failed to initialize schema: {e}")

    finally:
        conn.close()
```

### Data Migration (Not Needed)

**Reason**: Historical `insights` and `stock_analyses` data remain intact. The `user_id` column is simply not present in the new schema, but existing insights can still be queried by `stock_symbol` and `analysis_date`.

**Backward Compatibility**: CLI `history` command queries by stock symbol only (no user filtering needed), so historical data is immediately accessible without migration.

---

## Query Patterns

### Before (Multi-User)
```python
# Get subscriptions for a user
subscriptions = storage.get_subscriptions(user_id="123456", active_only=True)

# Get insights for user's subscribed stocks
for sub in subscriptions:
    insights = storage.get_insights(stock_symbol=sub.stock_symbol, user_id=sub.user_id)
```

### After (Personal)
```python
# Get stock list from config
stock_symbols = config.get_stock_symbols()  # ["AAPL", "MSFT", "GOOGL"]

# Get insights for any stock (no user filtering)
insights = storage.get_insights(stock_symbol="AAPL")  # All AAPL insights
```

**Simplification**: Removes 2-step query pattern (get subscriptions → get insights). Personal user queries any stock directly.

---

## Validation Rules

### Stock Symbol Validation
```python
def validate_stock_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.

    Rules:
    - 1-5 characters
    - Uppercase letters only
    - Alphanumeric (A-Z, 0-9)
    """
    if not symbol:
        return False
    if len(symbol) < 1 or len(symbol) > 5:
        return False
    if not symbol.isupper():
        return False
    if not symbol.isalnum():
        return False
    return True
```

### Stock List Validation
```python
def validate_stock_list(stock_list: str) -> List[str]:
    """
    Parse and validate stock list from environment variable.

    Steps:
    1. Split by comma
    2. Strip whitespace
    3. Convert to uppercase
    4. Filter empty strings
    5. Deduplicate (preserve order)
    6. Validate each symbol

    Returns:
        List of valid stock symbols

    Raises:
        ValueError: If stock list is empty after validation
    """
    if not stock_list:
        raise ValueError("Stock list cannot be empty")

    # Parse
    symbols = [s.strip().upper() for s in stock_list.split(",")]
    symbols = [s for s in symbols if s]  # Remove empty
    symbols = list(dict.fromkeys(symbols))  # Deduplicate

    # Validate
    invalid = [s for s in symbols if not validate_stock_symbol(s)]
    if invalid:
        logger.warning(f"Invalid stock symbols will be skipped: {invalid}")

    valid = [s for s in symbols if validate_stock_symbol(s)]

    if not valid:
        raise ValueError("No valid stock symbols found in stock list")

    return valid
```

---

## Summary

**Tables**: 4 (down from 6)
- **Removed**: `users`, `subscriptions`
- **Modified**: `insights`, `delivery_logs`
- **Unchanged**: `stock_analyses`, `analysis_jobs`

**Relationships**: 1 FK (down from 4)
- **Removed**: `subscriptions.user_id → users.user_id`
- **Removed**: `insights.analysis_id → analyses.id`
- **Removed**: `delivery_logs.user_id → users.user_id`
- **Retained**: `delivery_logs.insight_id → insights.id`

**Complexity Reduction**: ~60% fewer foreign keys, 33% fewer tables

**Migration**: Idempotent schema initialization with table drops; existing data preserved

**Status**: ✅ Phase 1 (Data Model) Complete
