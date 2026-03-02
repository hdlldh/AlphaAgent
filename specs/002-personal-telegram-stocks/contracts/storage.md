# Storage Interface Contract: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Storage**: SQLite

## Overview

Storage layer for personal stock monitoring. Simplified interface with user/subscription methods removed.

**Changes from Multi-User Version**:
- **REMOVED**: `create_user()`, `get_user()`, `update_user()`
- **REMOVED**: `create_subscription()`, `delete_subscription()`, `get_subscriptions()`
- **MODIFIED**: `create_insight()`, `create_delivery_log()` (no user_id parameter)
- **RETAINED**: All analysis and job management methods

---

## Initialization

### init_database()

Initialize or migrate database schema.

**Signature**:
```python
def init_database(self) -> None:
    """
    Create or migrate database schema.

    Migration behavior:
    - Drops users and subscriptions tables
    - Creates/updates all other tables
    - Preserves existing analysis and insight data
    - Idempotent (safe to run multiple times)

    Raises:
        StorageError: If schema initialization fails
    """
```

**Contract**:
- Creates database file if not exists
- Drops `users` and `subscriptions` tables
- Creates 4 tables: `stock_analyses`, `insights`, `delivery_logs`, `analysis_jobs`
- Creates indexes for query performance
- Idempotent: Running twice produces same result
- Preserves existing data in analyses and insights tables

**Test Assertions**:
```python
def test_init_database_creates_tables():
    storage = Storage(":memory:")
    storage.init_database()

    conn = storage._get_connection()
    cursor = conn.cursor()

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "stock_analyses" in tables
    assert "insights" in tables
    assert "delivery_logs" in tables
    assert "analysis_jobs" in tables

    # Verify multi-user tables removed
    assert "users" not in tables
    assert "subscriptions" not in tables

def test_init_database_idempotent():
    storage = Storage(":memory:")
    storage.init_database()
    storage.init_database()  # Should not error

    # Database should still be valid
    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    count = cursor.fetchone()[0]
    assert count == 4
```

---

## Analysis Management

### create_analysis()

Create a stock analysis record.

**Signature**:
```python
def create_analysis(
    self,
    stock_symbol: str,
    analysis_date: date,
    price_snapshot: float,
    price_change_percent: Optional[float] = None,
    volume: Optional[int] = None,
    analysis_status: str = "pending"
) -> StockAnalysis:
    """
    Create stock analysis record.

    Args:
        stock_symbol: Stock ticker (e.g., "AAPL")
        analysis_date: Date of analysis
        price_snapshot: Current stock price
        price_change_percent: Percentage change from previous day
        volume: Trading volume
        analysis_status: "success", "failed", or "pending"

    Returns:
        StockAnalysis instance with assigned ID

    Raises:
        StorageError: If creation fails
    """
```

**Contract**:
- Inserts new analysis record
- Returns StockAnalysis with assigned ID
- UNIQUE constraint on (stock_symbol, analysis_date) prevents duplicates
- Timestamps recorded automatically

**Test Assertions**:
```python
def test_create_analysis():
    storage = Storage(":memory:")
    storage.init_database()

    analysis = storage.create_analysis(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        price_snapshot=185.50,
        price_change_percent=2.3,
        volume=50000000,
        analysis_status="success"
    )

    assert analysis.id is not None
    assert analysis.stock_symbol == "AAPL"
    assert analysis.price_snapshot == 185.50
```

### get_analysis()

Retrieve analysis by symbol and date.

**Signature**:
```python
def get_analysis(
    self,
    stock_symbol: str,
    analysis_date: date
) -> Optional[StockAnalysis]:
    """
    Get analysis for specific stock and date.

    Args:
        stock_symbol: Stock ticker
        analysis_date: Date of analysis

    Returns:
        StockAnalysis if found, None otherwise
    """
```

**Contract**:
- Returns most recent analysis for (symbol, date) pair
- Returns None if not found
- No user filtering (personal use)

---

## Insight Management

### create_insight()

Create an analysis insight.

**Signature**:
```python
def create_insight(
    self,
    stock_symbol: str,
    analysis_date: date,
    summary: str,
    trend_analysis: str,
    risk_factors: List[str],
    opportunities: List[str],
    confidence_level: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Insight:
    """
    Create analysis insight.

    Args:
        stock_symbol: Stock ticker
        analysis_date: Date of analysis
        summary: Brief summary text
        trend_analysis: Detailed trend analysis
        risk_factors: List of risk strings
        opportunities: List of opportunity strings
        confidence_level: "high", "medium", or "low"
        metadata: Optional metadata dict (LLM provider, tokens, etc.)

    Returns:
        Insight instance with assigned ID

    Raises:
        StorageError: If creation fails
        ValueError: If confidence_level invalid
    """
```

**Contract**:
- Inserts new insight record
- Returns Insight with assigned ID
- JSON-encodes risk_factors and opportunities arrays
- JSON-encodes metadata dict
- **No user_id parameter** (removed from multi-user version)
- Timestamps recorded automatically

**Test Assertions**:
```python
def test_create_insight():
    storage = Storage(":memory:")
    storage.init_database()

    insight = storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        summary="Strong performance with 2.3% gain",
        trend_analysis="Technical indicators suggest upward momentum",
        risk_factors=["Market volatility", "Regulatory pressures"],
        opportunities=["Strong iPhone demand", "Services growth"],
        confidence_level="high",
        metadata={"provider": "anthropic", "tokens": 1543}
    )

    assert insight.id is not None
    assert insight.stock_symbol == "AAPL"
    assert len(insight.risk_factors) == 2
    assert insight.confidence_level == "high"
```

### get_insights()

Retrieve insights for a stock.

**Signature**:
```python
def get_insights(
    self,
    stock_symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Insight]:
    """
    Get insights for a stock.

    Args:
        stock_symbol: Stock ticker
        start_date: Start date (inclusive, optional)
        end_date: End date (inclusive, optional)
        limit: Maximum results
        offset: Skip first N results

    Returns:
        List of Insight instances, sorted by date descending

    Note:
        No user_id filtering (personal use)
    """
```

**Contract**:
- Returns all insights for stock symbol
- Filters by date range if provided
- Sorted by analysis_date descending (newest first)
- Supports pagination (limit + offset)
- **No user_id parameter** (removed from multi-user version)
- Returns empty list if no insights found

**Test Assertions**:
```python
def test_get_insights_with_date_range():
    storage = Storage(":memory:")
    storage.init_database()

    # Create insights for different dates
    storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 20),
        # ... other fields
    )
    storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 25),
        # ... other fields
    )
    storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        # ... other fields
    )

    # Query with date range
    insights = storage.get_insights(
        stock_symbol="AAPL",
        start_date=date(2026, 2, 21),
        end_date=date(2026, 2, 28)
    )

    assert len(insights) == 2  # 2/25 and 2/28
    assert insights[0].analysis_date == date(2026, 2, 28)  # Descending order
```

---

## Delivery Log Management

### create_delivery_log()

Record insight delivery to Telegram channel.

**Signature**:
```python
def create_delivery_log(
    self,
    insight_id: int,
    channel_id: str,
    delivery_status: str = "pending",
    delivery_method: str = "telegram",
    delivered_at: Optional[datetime] = None,
    error_message: Optional[str] = None,
    telegram_message_id: Optional[str] = None
) -> DeliveryLog:
    """
    Create delivery log entry.

    Args:
        insight_id: References insights.id
        channel_id: Telegram channel ID (@channel or -100123...)
        delivery_status: "success", "failed", or "pending"
        delivery_method: Delivery channel (default: "telegram")
        delivered_at: Delivery timestamp (None if pending/failed)
        error_message: Error details if failed
        telegram_message_id: Telegram message ID

    Returns:
        DeliveryLog instance with assigned ID

    Raises:
        StorageError: If creation fails
    """
```

**Contract**:
- Inserts new delivery log record
- Returns DeliveryLog with assigned ID
- **channel_id replaces user_id** (changed from multi-user version)
- Foreign key to insights table enforced
- Timestamps recorded automatically

**Test Assertions**:
```python
def test_create_delivery_log():
    storage = Storage(":memory:")
    storage.init_database()

    # Create insight first
    insight = storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date(2026, 2, 28),
        # ... other fields
    )

    # Create delivery log
    log = storage.create_delivery_log(
        insight_id=insight.id,
        channel_id="@mystockchannel",
        delivery_status="success",
        delivered_at=datetime.utcnow(),
        telegram_message_id="123456"
    )

    assert log.id is not None
    assert log.channel_id == "@mystockchannel"
    assert log.delivery_status == "success"
```

### get_delivery_logs()

Retrieve delivery logs for an insight.

**Signature**:
```python
def get_delivery_logs(
    self,
    insight_id: int
) -> List[DeliveryLog]:
    """
    Get delivery logs for an insight.

    Args:
        insight_id: Insight ID to query

    Returns:
        List of DeliveryLog instances

    Note:
        No user_id filtering (personal use)
    """
```

**Contract**:
- Returns all delivery logs for insight
- Sorted by delivered_at descending
- Returns empty list if no logs found

---

## Job Management

### create_job()

Create an analysis job record.

**Signature**:
```python
def create_job(
    self,
    stocks_scheduled: int
) -> AnalysisJob:
    """
    Create analysis job record.

    Args:
        stocks_scheduled: Number of stocks to analyze

    Returns:
        AnalysisJob instance with assigned ID

    Raises:
        StorageError: If creation fails
    """
```

**Contract**: (Unchanged from multi-user version)
- Inserts new job record with status "running"
- execution_time set to current UTC time
- Returns AnalysisJob with assigned ID

### update_job()

Update job execution status.

**Signature**:
```python
def update_job(
    self,
    job_id: int,
    stocks_processed: Optional[int] = None,
    success_count: Optional[int] = None,
    failure_count: Optional[int] = None,
    insights_delivered: Optional[int] = None,
    job_status: Optional[str] = None,
    completion_time: Optional[datetime] = None,
    duration_seconds: Optional[float] = None,
    errors: Optional[List[str]] = None
) -> None:
    """
    Update job record.

    Args:
        job_id: Job ID to update
        stocks_processed: Number processed
        success_count: Successful analyses
        failure_count: Failed analyses
        insights_delivered: Insights successfully delivered
        job_status: "running", "completed", or "failed"
        completion_time: Job end time
        duration_seconds: Total job duration
        errors: List of error messages

    Raises:
        StorageError: If update fails
    """
```

**Contract**: (Unchanged from multi-user version)
- Updates specified fields only (None values ignored)
- JSON-encodes errors list
- Raises StorageError if job_id not found

---

## Removed Methods

These methods are **no longer available** in the personal version:

### User Management (REMOVED)
- `create_user(user_id, telegram_username)` → No users table
- `get_user(user_id)` → No users table
- `update_user_activity(user_id)` → No users table

### Subscription Management (REMOVED)
- `create_subscription(user_id, stock_symbol)` → Stock list is env-configured
- `delete_subscription(subscription_id)` → No subscriptions table
- `get_subscriptions(user_id, stock_symbol, active_only)` → No subscriptions table
- `count_user_subscriptions(user_id)` → No subscription limits
- `count_system_subscriptions()` → No system-wide limits

**Migration Note**: Applications should use `config.get_stock_symbols()` instead of querying subscriptions.

---

## Error Handling

### StorageError

Base exception for storage operations.

**Fields**:
- `operation`: Operation that failed (e.g., "create_insight", "schema_init")
- `message`: Error description

**Usage**:
```python
try:
    storage.create_insight(...)
except StorageError as e:
    logger.error(f"Storage operation '{e.operation}' failed: {e.message}")
```

---

## Testing Strategy

### Contract Tests

```python
def test_storage_init_removes_multi_user_tables():
    """Contract: init_database removes users and subscriptions tables."""
    storage = Storage(":memory:")
    storage.init_database()

    conn = storage._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "users" not in tables
    assert "subscriptions" not in tables

def test_storage_create_insight_without_user_id():
    """Contract: create_insight works without user_id parameter."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = storage.create_insight(
        stock_symbol="AAPL",
        analysis_date=date.today(),
        summary="Test",
        trend_analysis="Test",
        risk_factors=[],
        opportunities=[],
        confidence_level="medium"
    )

    # Should succeed without user_id
    assert insight.id is not None

def test_storage_get_insights_without_user_filter():
    """Contract: get_insights returns all insights for symbol (no user filter)."""
    storage = Storage(":memory:")
    storage.init_database()

    # Create insights
    storage.create_insight(stock_symbol="AAPL", ...)
    storage.create_insight(stock_symbol="AAPL", ...)

    # Should return all insights for symbol
    insights = storage.get_insights(stock_symbol="AAPL")
    assert len(insights) == 2

def test_storage_create_delivery_log_with_channel_id():
    """Contract: create_delivery_log uses channel_id instead of user_id."""
    storage = Storage(":memory:")
    storage.init_database()

    insight = storage.create_insight(...)

    log = storage.create_delivery_log(
        insight_id=insight.id,
        channel_id="@mystockchannel",
        delivery_status="success"
    )

    assert log.channel_id == "@mystockchannel"
```

---

## Summary

**Total Methods**: 12
- **Removed**: 8 (all user/subscription methods)
- **Modified**: 2 (`create_insight`, `create_delivery_log`)
- **Unchanged**: 10 (analysis and job methods)

**Key Changes**:
- `create_insight()`: No user_id parameter
- `create_delivery_log()`: channel_id replaces user_id
- `get_insights()`: No user_id filtering

**Migration Impact**: ~40% reduction in storage interface methods

**Status**: ✅ Storage Contract Complete
