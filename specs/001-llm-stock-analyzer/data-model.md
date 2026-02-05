# Data Model: AI-Powered Stock Analysis

**Date**: 2026-01-30
**Feature**: 001-llm-stock-analyzer

## Overview

This document defines the data entities, relationships, validation rules, and state transitions for the stock analysis system. The data model is implemented using SQLite with a Git-committed database file for persistence across GitHub Actions runs.

---

## Entity Definitions

### 1. User

Represents a Telegram user receiving stock analysis insights.

**Attributes**:
- `user_id` (TEXT, PRIMARY KEY): Telegram user ID (unique identifier from Telegram)
- `telegram_username` (TEXT, NULLABLE): Telegram username for reference
- `created_at` (TEXT, NOT NULL): ISO 8601 timestamp when user first interacted
- `last_active` (TEXT, NOT NULL): ISO 8601 timestamp of last interaction
- `preferences` (TEXT, NULLABLE): JSON blob with user preferences

**Validation Rules**:
- `user_id` must be non-empty string
- `created_at` and `last_active` must be valid ISO 8601 timestamps
- `preferences` must be valid JSON if present

**Example**:
```json
{
  "user_id": "123456789",
  "telegram_username": "@investor_jane",
  "created_at": "2026-01-30T10:00:00Z",
  "last_active": "2026-01-30T15:30:00Z",
  "preferences": "{\"timezone\": \"America/New_York\", \"notification_time\": \"09:00\"}"
}
```

---

### 2. Stock Subscription

Represents a user's subscription to receive analysis for a specific stock.

**Attributes**:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique subscription identifier
- `user_id` (TEXT, NOT NULL, FOREIGN KEY → User): References the subscribed user
- `stock_symbol` (TEXT, NOT NULL): Stock ticker symbol (e.g., "AAPL", "TSLA")
- `subscription_date` (TEXT, NOT NULL): ISO 8601 timestamp when subscription created
- `active_status` (INTEGER, NOT NULL, DEFAULT 1): 1 = active, 0 = inactive/unsubscribed
- `preferences` (TEXT, NULLABLE): JSON blob with subscription-specific preferences

**Validation Rules**:
- `user_id` must reference existing User
- `stock_symbol` must be 1-10 characters, uppercase letters only
- `stock_symbol` must be validated against stock data API before accepting
- UNIQUE constraint on (`user_id`, `stock_symbol`) - no duplicate subscriptions
- Maximum 10 active subscriptions per user (enforced in application logic)
- Maximum 100 total active subscriptions system-wide (enforced in application logic)
- `subscription_date` must be valid ISO 8601 timestamp
- `active_status` must be 0 or 1

**State Transitions**:
```
[New] --subscribe--> [Active] --unsubscribe--> [Inactive]
                         ^                          |
                         |                          |
                         +-------resubscribe--------+
```

**Example**:
```json
{
  "id": 1,
  "user_id": "123456789",
  "stock_symbol": "AAPL",
  "subscription_date": "2026-01-30T10:05:00Z",
  "active_status": 1,
  "preferences": "{\"alert_threshold\": 5.0}"
}
```

---

### 3. Stock Analysis

Represents a single analysis run for a specific stock on a specific date.

**Attributes**:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique analysis identifier
- `stock_symbol` (TEXT, NOT NULL): Stock ticker symbol analyzed
- `analysis_date` (TEXT, NOT NULL): ISO 8601 date (YYYY-MM-DD) of analysis
- `price_snapshot` (REAL, NOT NULL): Stock price at time of analysis
- `price_change_percent` (REAL, NULLABLE): Percentage change from previous day
- `volume` (INTEGER, NULLABLE): Trading volume
- `analysis_status` (TEXT, NOT NULL): "success", "failed", "pending"
- `error_message` (TEXT, NULLABLE): Error details if status = "failed"
- `created_at` (TEXT, NOT NULL): ISO 8601 timestamp when analysis completed
- `duration_seconds` (REAL, NULLABLE): Time taken to complete analysis

**Validation Rules**:
- `stock_symbol` must be 1-10 characters, uppercase letters only
- `analysis_date` must be valid ISO 8601 date (YYYY-MM-DD)
- UNIQUE constraint on (`stock_symbol`, `analysis_date`) - one analysis per stock per day
- `analysis_status` must be one of: "success", "failed", "pending"
- `price_snapshot` must be positive number
- `created_at` must be valid ISO 8601 timestamp

**State Transitions**:
```
[Pending] --success--> [Success]
   |
   +------failure-----> [Failed]
```

**Example**:
```json
{
  "id": 1,
  "stock_symbol": "AAPL",
  "analysis_date": "2026-01-30",
  "price_snapshot": 185.75,
  "price_change_percent": 2.3,
  "volume": 52000000,
  "analysis_status": "success",
  "error_message": null,
  "created_at": "2026-01-30T22:15:30Z",
  "duration_seconds": 4.2
}
```

---

### 4. Insight

Represents the AI-generated analysis content for a stock.

**Attributes**:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique insight identifier
- `analysis_id` (INTEGER, NOT NULL, FOREIGN KEY → Stock Analysis): References the analysis run
- `stock_symbol` (TEXT, NOT NULL): Stock ticker symbol (denormalized for query performance)
- `analysis_date` (TEXT, NOT NULL): ISO 8601 date (denormalized for query performance)
- `summary` (TEXT, NOT NULL): Brief summary of the analysis (1-2 sentences)
- `trend_analysis` (TEXT, NOT NULL): LLM-generated trend interpretation
- `risk_factors` (TEXT, NOT NULL): Identified risks (JSON array or newline-separated)
- `opportunities` (TEXT, NOT NULL): Identified opportunities (JSON array or newline-separated)
- `confidence_level` (TEXT, NOT NULL): "high", "medium", "low"
- `metadata` (TEXT, NULLABLE): JSON blob with additional context (sources, prompt version, etc.)
- `created_at` (TEXT, NOT NULL): ISO 8601 timestamp when insight generated

**Validation Rules**:
- `analysis_id` must reference existing Stock Analysis
- `stock_symbol` and `analysis_date` must match referenced Stock Analysis
- `summary` must be 10-500 characters
- `trend_analysis`, `risk_factors`, `opportunities` must be non-empty
- `confidence_level` must be one of: "high", "medium", "low"
- `metadata` must be valid JSON if present
- `created_at` must be valid ISO 8601 timestamp

**Example**:
```json
{
  "id": 1,
  "analysis_id": 1,
  "stock_symbol": "AAPL",
  "analysis_date": "2026-01-30",
  "summary": "Apple shows strong upward momentum with increased volume, indicating positive investor sentiment.",
  "trend_analysis": "The stock has gained 2.3% with volume 15% above average, suggesting sustained buying interest. Technical indicators show bullish divergence.",
  "risk_factors": "[\"Overvaluation concerns at current P/E ratio\", \"Dependence on iPhone revenue\", \"Supply chain vulnerabilities\"]",
  "opportunities": "[\"Upcoming product launches in Q2\", \"Growing services revenue segment\", \"Market expansion in emerging economies\"]",
  "confidence_level": "high",
  "metadata": "{\"prompt_version\": \"1.0\", \"llm_model\": \"claude-sonnet-4-5\", \"data_sources\": [\"yfinance\"], \"tokens_used\": 2500}",
  "created_at": "2026-01-30T22:15:30Z"
}
```

---

### 5. Delivery Log

Tracks delivery of insights to users via Telegram.

**Attributes**:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique delivery log identifier
- `insight_id` (INTEGER, NOT NULL, FOREIGN KEY → Insight): References the delivered insight
- `user_id` (TEXT, NOT NULL, FOREIGN KEY → User): References the recipient user
- `delivery_status` (TEXT, NOT NULL): "success", "failed", "pending"
- `delivery_method` (TEXT, NOT NULL): "telegram" (extensible for future methods)
- `delivered_at` (TEXT, NULLABLE): ISO 8601 timestamp when delivered (null if failed)
- `error_message` (TEXT, NULLABLE): Error details if status = "failed"
- `telegram_message_id` (TEXT, NULLABLE): Telegram message ID for reference

**Validation Rules**:
- `insight_id` must reference existing Insight
- `user_id` must reference existing User
- `delivery_status` must be one of: "success", "failed", "pending"
- `delivery_method` must be "telegram" (currently only supported method)
- `delivered_at` must be valid ISO 8601 timestamp if present

**State Transitions**:
```
[Pending] --success--> [Success]
   |
   +------failure-----> [Failed] --retry--> [Pending]
```

**Example**:
```json
{
  "id": 1,
  "insight_id": 1,
  "user_id": "123456789",
  "delivery_status": "success",
  "delivery_method": "telegram",
  "delivered_at": "2026-01-30T22:16:00Z",
  "error_message": null,
  "telegram_message_id": "987654321"
}
```

---

### 6. Analysis Job

Represents a scheduled execution of the daily analysis workflow.

**Attributes**:
- `id` (INTEGER, PRIMARY KEY AUTOINCREMENT): Unique job identifier
- `execution_time` (TEXT, NOT NULL): ISO 8601 timestamp when job started
- `completion_time` (TEXT, NULLABLE): ISO 8601 timestamp when job completed
- `job_status` (TEXT, NOT NULL): "running", "completed", "failed"
- `stocks_scheduled` (INTEGER, NOT NULL): Number of stocks planned to analyze
- `stocks_processed` (INTEGER, NOT NULL DEFAULT 0): Number of stocks actually processed
- `success_count` (INTEGER, NOT NULL DEFAULT 0): Number of successful analyses
- `failure_count` (INTEGER, NOT NULL DEFAULT 0): Number of failed analyses
- `insights_delivered` (INTEGER, NOT NULL DEFAULT 0): Number of insights successfully delivered
- `errors` (TEXT, NULLABLE): JSON array of error messages
- `duration_seconds` (REAL, NULLABLE): Total job duration

**Validation Rules**:
- `execution_time` must be valid ISO 8601 timestamp
- `completion_time` must be valid ISO 8601 timestamp if present, and >= execution_time
- `job_status` must be one of: "running", "completed", "failed"
- `stocks_processed` <= `stocks_scheduled`
- `success_count` + `failure_count` = `stocks_processed`
- `errors` must be valid JSON array if present

**State Transitions**:
```
[Running] --all processed--> [Completed]
   |
   +------error---------> [Failed]
```

**Example**:
```json
{
  "id": 1,
  "execution_time": "2026-01-30T22:00:00Z",
  "completion_time": "2026-01-30T22:45:30Z",
  "job_status": "completed",
  "stocks_scheduled": 100,
  "stocks_processed": 100,
  "success_count": 98,
  "failure_count": 2,
  "insights_delivered": 195,
  "errors": "[\"DELISTED: Stock XYZ not found\", \"TIMEOUT: Analysis for ABC exceeded 60s\"]",
  "duration_seconds": 2730.5
}
```

---

## Entity Relationships

```
User (1) <---> (N) Stock Subscription
User (1) <---> (N) Delivery Log

Stock Subscription (N) ---> (1) User

Stock Analysis (1) <---> (1) Insight
Stock Analysis (N) <---> (1) Stock Symbol (implicit)

Insight (1) <---> (N) Delivery Log
Insight (N) ---> (1) Stock Analysis

Delivery Log (N) ---> (1) User
Delivery Log (N) ---> (1) Insight

Analysis Job (1) <---> (N) Stock Analysis (implicit via date)
```

### Key Relationships

1. **User → Subscriptions** (1:N): A user can have multiple stock subscriptions (max 10)
2. **Subscription → User** (N:1): Each subscription belongs to exactly one user
3. **Analysis → Insight** (1:1): Each analysis generates exactly one insight
4. **Insight → Deliveries** (1:N): One insight can be delivered to multiple users
5. **Job → Analyses** (1:N): One job processes multiple stock analyses

---

## Database Schema (SQLite)

```sql
-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    telegram_username TEXT,
    created_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    preferences TEXT
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    stock_symbol TEXT NOT NULL,
    subscription_date TEXT NOT NULL,
    active_status INTEGER NOT NULL DEFAULT 1,
    preferences TEXT,
    UNIQUE(user_id, stock_symbol),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id, active_status);
CREATE INDEX idx_subscriptions_symbol ON subscriptions(stock_symbol, active_status);

-- Stock analyses table
CREATE TABLE stock_analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_symbol TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    price_snapshot REAL NOT NULL,
    price_change_percent REAL,
    volume INTEGER,
    analysis_status TEXT NOT NULL,
    error_message TEXT,
    created_at TEXT NOT NULL,
    duration_seconds REAL,
    UNIQUE(stock_symbol, analysis_date)
);

CREATE INDEX idx_analyses_symbol_date ON stock_analyses(stock_symbol, analysis_date DESC);
CREATE INDEX idx_analyses_date ON stock_analyses(analysis_date DESC);

-- Insights table
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    summary TEXT NOT NULL,
    trend_analysis TEXT NOT NULL,
    risk_factors TEXT NOT NULL,
    opportunities TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES stock_analyses(id) ON DELETE CASCADE
);

CREATE INDEX idx_insights_analysis ON insights(analysis_id);
CREATE INDEX idx_insights_symbol_date ON insights(stock_symbol, analysis_date DESC);

-- Delivery logs table
CREATE TABLE delivery_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    delivery_status TEXT NOT NULL,
    delivery_method TEXT NOT NULL,
    delivered_at TEXT,
    error_message TEXT,
    telegram_message_id TEXT,
    FOREIGN KEY (insight_id) REFERENCES insights(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_delivery_user ON delivery_logs(user_id, delivery_status);
CREATE INDEX idx_delivery_insight ON delivery_logs(insight_id);

-- Analysis jobs table
CREATE TABLE analysis_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_time TEXT NOT NULL,
    completion_time TEXT,
    job_status TEXT NOT NULL,
    stocks_scheduled INTEGER NOT NULL,
    stocks_processed INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    insights_delivered INTEGER NOT NULL DEFAULT 0,
    errors TEXT,
    duration_seconds REAL
);

CREATE INDEX idx_jobs_execution_time ON analysis_jobs(execution_time DESC);
CREATE INDEX idx_jobs_status ON analysis_jobs(job_status);
```

---

## Business Rules

### Subscription Limits

1. **Per-User Limit**: Maximum 10 active subscriptions per user
   - Enforced in application logic when adding subscription
   - Error message: "Maximum subscription limit reached (10 stocks)"

2. **System-Wide Limit**: Maximum 100 total active subscriptions
   - Enforced in application logic when adding subscription
   - Error message: "System capacity reached. Please try again later."

3. **Duplicate Prevention**: Cannot subscribe to same stock twice
   - Enforced by UNIQUE constraint on (user_id, stock_symbol)
   - Application should handle gracefully: "Already subscribed to {symbol}"

### Analysis Scheduling

1. **Daily Execution**: Analysis runs once per trading day (Monday-Friday)
2. **Timing**: Scheduled for 22:00 UTC (after US market close at 21:00 UTC / 4:00 PM ET)
3. **Completion Window**: Must complete within 1 hour (by 23:00 UTC)
4. **Trading Day Detection**: Skip weekends and US market holidays

### Data Retention

1. **Insights**: Retained for minimum 1 year (365 days)
2. **Delivery Logs**: Retained for 90 days
3. **Job Logs**: Retained indefinitely (for monitoring trends)
4. **Inactive Subscriptions**: Retained indefinitely (can be reactivated)
5. **Cleanup Strategy**: Periodic archive job moves old data to compressed backups

### Delivery Rules

1. **Delivery Window**: Insights delivered within 2 hours of generation
2. **Retry Logic**: Failed deliveries retried up to 3 times with exponential backoff
3. **User Notification**: Users receive one message per subscribed stock per day
4. **Batch Delivery**: All insights for a user sent in single session to avoid spam

---

## Query Patterns

### Common Queries

```sql
-- Get active subscriptions for a user
SELECT stock_symbol FROM subscriptions
WHERE user_id = ? AND active_status = 1;

-- Get latest insight for a stock
SELECT * FROM insights
WHERE stock_symbol = ?
ORDER BY analysis_date DESC LIMIT 1;

-- Get historical insights for date range
SELECT * FROM insights
WHERE stock_symbol = ?
  AND analysis_date BETWEEN ? AND ?
ORDER BY analysis_date DESC;

-- Get all stocks needing analysis today
SELECT DISTINCT stock_symbol
FROM subscriptions
WHERE active_status = 1
  AND stock_symbol NOT IN (
    SELECT stock_symbol FROM stock_analyses
    WHERE analysis_date = date('now')
  );

-- Get users subscribed to a stock
SELECT DISTINCT user_id FROM subscriptions
WHERE stock_symbol = ? AND active_status = 1;

-- Get recent job statistics
SELECT
  DATE(execution_time) as date,
  COUNT(*) as jobs,
  AVG(success_count) as avg_success,
  AVG(failure_count) as avg_failure,
  AVG(duration_seconds) as avg_duration
FROM analysis_jobs
WHERE job_status = 'completed'
  AND execution_time >= datetime('now', '-30 days')
GROUP BY DATE(execution_time)
ORDER BY date DESC;
```

---

## Data Migration Strategy

### Initial Setup

```python
def init_database(db_path):
    """Initialize database with schema and indexes."""
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        -- Create tables (full schema from above)
        -- Create indexes
    """)
    conn.commit()
    conn.close()
```

### Schema Evolution

Use Alembic or simple migration scripts:

```python
# migrations/001_add_user_preferences.py
def upgrade(conn):
    conn.execute("ALTER TABLE users ADD COLUMN preferences TEXT")

def downgrade(conn):
    # SQLite doesn't support DROP COLUMN, need to recreate table
    pass
```

---

## Conclusion

This data model provides a robust foundation for the stock analysis system with:
- Clear entity definitions and relationships
- Comprehensive validation rules
- Efficient query patterns with proper indexing
- Business rule enforcement
- Data retention and cleanup strategies

The SQLite implementation offers simplicity and zero infrastructure while meeting all performance requirements for the system's scale (100 stocks, ~36K records/year).
