# CLI Interface Contract

**Feature**: AI-Powered Stock Analysis
**Date**: 2026-01-30
**Version**: 1.0.0

## Overview

The command-line interface provides text-based access to all stock analyzer functionality. Following the AlphaAgent Constitution's CLI Interface principle, all commands follow a text in/out protocol: input via stdin or arguments, output to stdout, errors to stderr, with support for both JSON and human-readable formats.

---

## Installation

```bash
# Install with uv
uv pip install stock-analyzer

# Verify installation
stock-analyzer --version
```

---

## Global Options

Available for all commands:

```
--json                Output in JSON format instead of human-readable
--verbose, -v        Enable verbose logging to stderr
--config FILE        Path to configuration file (default: ~/.stock-analyzer/config.toml)
--help, -h           Show help message
```

---

## Commands

### 1. analyze

Analyze a single stock and output insights.

**Usage**:
```bash
stock-analyzer analyze <SYMBOL> [OPTIONS]
```

**Arguments**:
- `SYMBOL` (required): Stock ticker symbol (e.g., AAPL, TSLA)

**Options**:
- `--date DATE`: Analysis date (ISO 8601, default: today)
- `--force`: Force re-analysis even if already exists for date
- `--no-cache`: Skip using cached stock data

**Output (Human-Readable)**:
```
Stock Analysis: AAPL
Date: 2026-01-30
Price: $185.75 (+2.3%)
Confidence: High

Summary:
Apple shows strong upward momentum with increased volume, indicating positive investor sentiment.

Trend Analysis:
The stock has gained 2.3% with volume 15% above average, suggesting sustained buying interest.
Technical indicators show bullish divergence.

Risk Factors:
  • Overvaluation concerns at current P/E ratio
  • Dependence on iPhone revenue
  • Supply chain vulnerabilities

Opportunities:
  • Upcoming product launches in Q2
  • Growing services revenue segment
  • Market expansion in emerging economies
```

**Output (JSON)**:
```json
{
  "status": "success",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-01-30",
  "price_snapshot": 185.75,
  "price_change_percent": 2.3,
  "confidence_level": "high",
  "summary": "Apple shows strong upward momentum...",
  "trend_analysis": "The stock has gained 2.3%...",
  "risk_factors": [
    "Overvaluation concerns at current P/E ratio",
    "Dependence on iPhone revenue",
    "Supply chain vulnerabilities"
  ],
  "opportunities": [
    "Upcoming product launches in Q2",
    "Growing services revenue segment",
    "Market expansion in emerging economies"
  ],
  "metadata": {
    "duration_seconds": 4.2,
    "data_sources": ["yfinance"],
    "llm_model": "claude-sonnet-4-5"
  }
}
```

**Exit Codes**:
- `0`: Success
- `1`: Invalid stock symbol
- `2`: Data fetch failed
- `3`: Analysis failed
- `4`: Rate limit exceeded

---

### 2. analyze-batch

Analyze multiple stocks from a file or stdin.

**Usage**:
```bash
stock-analyzer analyze-batch [FILE] [OPTIONS]
stock-analyzer analyze-batch --stdin [OPTIONS]
```

**Arguments**:
- `FILE` (optional): File containing stock symbols (one per line)
- If no FILE provided and no --stdin, reads from `subscriptions.txt`

**Options**:
- `--stdin`: Read stock symbols from stdin
- `--parallel N`: Number of parallel analysis tasks (default: 1)
- `--continue-on-error`: Don't stop on first failure
- `--progress`: Show progress bar

**Input Format**:
```
AAPL
TSLA
MSFT
GOOGL
```

**Output (Human-Readable)**:
```
Analyzing 4 stocks...
[1/4] AAPL... ✓ (4.2s)
[2/4] TSLA... ✓ (3.8s)
[3/4] MSFT... ✓ (4.5s)
[4/4] GOOGL... ✓ (4.1s)

Summary:
  Analyzed: 4
  Success: 4
  Failed: 0
  Duration: 16.6s
```

**Output (JSON)**:
```json
{
  "status": "success",
  "total": 4,
  "success_count": 4,
  "failure_count": 0,
  "duration_seconds": 16.6,
  "results": [
    {
      "stock_symbol": "AAPL",
      "status": "success",
      "analysis_date": "2026-01-30"
    },
    ...
  ]
}
```

---

### 3. subscribe

Add a stock subscription for a user.

**Usage**:
```bash
stock-analyzer subscribe <USER_ID> <SYMBOL> [OPTIONS]
```

**Arguments**:
- `USER_ID` (required): Telegram user ID
- `SYMBOL` (required): Stock ticker symbol

**Options**:
- `--validate`: Validate stock symbol before subscribing
- `--preferences JSON`: User preferences as JSON string

**Output (Human-Readable)**:
```
✓ Subscribed user 123456789 to AAPL
Active subscriptions: 3/10
```

**Output (JSON)**:
```json
{
  "status": "success",
  "user_id": "123456789",
  "stock_symbol": "AAPL",
  "subscription_date": "2026-01-30T10:05:00Z",
  "active_subscriptions": 3,
  "max_subscriptions": 10
}
```

**Exit Codes**:
- `0`: Success
- `1`: Invalid stock symbol
- `2`: User at subscription limit
- `3`: System at capacity
- `4`: Already subscribed

---

### 4. unsubscribe

Remove a stock subscription for a user.

**Usage**:
```bash
stock-analyzer unsubscribe <USER_ID> <SYMBOL>
```

**Arguments**:
- `USER_ID` (required): Telegram user ID
- `SYMBOL` (required): Stock ticker symbol

**Output (Human-Readable)**:
```
✓ Unsubscribed user 123456789 from AAPL
Active subscriptions: 2/10
```

**Output (JSON)**:
```json
{
  "status": "success",
  "user_id": "123456789",
  "stock_symbol": "AAPL",
  "active_subscriptions": 2,
  "max_subscriptions": 10
}
```

---

### 5. list-subscriptions

List subscriptions for a user or all users.

**Usage**:
```bash
stock-analyzer list-subscriptions [USER_ID] [OPTIONS]
```

**Arguments**:
- `USER_ID` (optional): Telegram user ID (omit for all users)

**Options**:
- `--active-only`: Show only active subscriptions
- `--with-stats`: Include subscription statistics

**Output (Human-Readable)**:
```
Subscriptions for user 123456789:
  1. AAPL  (subscribed: 2026-01-28)
  2. TSLA  (subscribed: 2026-01-29)
  3. MSFT  (subscribed: 2026-01-30)

Total: 3/10
```

**Output (JSON)**:
```json
{
  "user_id": "123456789",
  "subscriptions": [
    {
      "stock_symbol": "AAPL",
      "subscription_date": "2026-01-28T14:30:00Z",
      "active_status": 1
    },
    ...
  ],
  "total": 3,
  "max": 10
}
```

---

### 6. history

Query historical insights for a stock.

**Usage**:
```bash
stock-analyzer history <SYMBOL> [OPTIONS]
```

**Arguments**:
- `SYMBOL` (required): Stock ticker symbol

**Options**:
- `--start DATE`: Start date (ISO 8601, default: 1 year ago)
- `--end DATE`: End date (ISO 8601, default: today)
- `--limit N`: Maximum number of results (default: 30)
- `--format FORMAT`: Output format (table, list, json)

**Output (Human-Readable - Table)**:
```
Historical Analysis: AAPL

Date         Price    Change   Confidence  Summary
────────────────────────────────────────────────────────────────
2026-01-30  $185.75   +2.3%   High        Strong upward momentum...
2026-01-29  $181.60   -0.5%   Medium      Consolidation phase...
2026-01-28  $182.50   +1.2%   High        Positive earnings reaction...

Total: 3 records
```

**Output (JSON)**:
```json
{
  "stock_symbol": "AAPL",
  "start_date": "2025-01-30",
  "end_date": "2026-01-30",
  "total_records": 3,
  "insights": [
    {
      "analysis_date": "2026-01-30",
      "price_snapshot": 185.75,
      "price_change_percent": 2.3,
      "confidence_level": "high",
      "summary": "Strong upward momentum..."
    },
    ...
  ]
}
```

---

### 7. deliver

Manually trigger insight delivery to users.

**Usage**:
```bash
stock-analyzer deliver [SYMBOL] [OPTIONS]
```

**Arguments**:
- `SYMBOL` (optional): Deliver only for specific stock (default: all pending)

**Options**:
- `--user USER_ID`: Deliver only to specific user
- `--date DATE`: Deliver insights from specific date (default: today)
- `--dry-run`: Show what would be delivered without actually sending

**Output (Human-Readable)**:
```
Delivering insights...
  AAPL → user 123456789... ✓
  AAPL → user 987654321... ✓
  TSLA → user 123456789... ✓

Summary:
  Delivered: 3
  Failed: 0
```

**Output (JSON)**:
```json
{
  "status": "success",
  "delivered": 3,
  "failed": 0,
  "deliveries": [
    {
      "stock_symbol": "AAPL",
      "user_id": "123456789",
      "status": "success",
      "telegram_message_id": "987654321"
    },
    ...
  ]
}
```

---

### 8. run-daily-job

Execute the full daily analysis workflow.

**Usage**:
```bash
stock-analyzer run-daily-job [OPTIONS]
```

**Options**:
- `--dry-run`: Simulate job without making changes
- `--force`: Run even if already executed today
- `--parallel N`: Number of parallel analysis tasks (default: 4)

**Output (Human-Readable)**:
```
Daily Analysis Job - 2026-01-30
════════════════════════════════

Phase 1: Fetch Subscriptions
  Active users: 15
  Unique stocks: 42

Phase 2: Stock Analysis
  [====================================] 42/42 (100%)
  Success: 40
  Failed: 2
  Duration: 8m 30s

Phase 3: Insight Delivery
  Deliveries: 120
  Success: 118
  Failed: 2

Job Summary:
  Status: Completed
  Total Duration: 10m 15s
  Next Run: 2026-01-31 22:00 UTC
```

**Output (JSON)**:
```json
{
  "job_id": 1,
  "execution_time": "2026-01-30T22:00:00Z",
  "completion_time": "2026-01-30T22:10:15Z",
  "job_status": "completed",
  "stocks_scheduled": 42,
  "stocks_processed": 42,
  "success_count": 40,
  "failure_count": 2,
  "insights_delivered": 118,
  "duration_seconds": 615.3
}
```

---

### 9. validate

Validate stock symbols.

**Usage**:
```bash
stock-analyzer validate <SYMBOL...>
stock-analyzer validate --file FILE
```

**Arguments**:
- `SYMBOL...`: One or more stock symbols to validate

**Options**:
- `--file FILE`: Read symbols from file
- `--api API`: Validation API (yfinance, alpha_vantage)

**Output (Human-Readable)**:
```
Validating symbols...
  AAPL... ✓ Valid
  TSLA... ✓ Valid
  INVALID... ✗ Not found
  XYZ... ✗ Delisted

Valid: 2/4
```

**Output (JSON)**:
```json
{
  "validated": 4,
  "valid": 2,
  "invalid": 2,
  "results": [
    {"symbol": "AAPL", "valid": true},
    {"symbol": "TSLA", "valid": true},
    {"symbol": "INVALID", "valid": false, "reason": "not_found"},
    {"symbol": "XYZ", "valid": false, "reason": "delisted"}
  ]
}
```

---

### 10. stats

Display system statistics.

**Usage**:
```bash
stock-analyzer stats [OPTIONS]
```

**Options**:
- `--period DAYS`: Statistics period in days (default: 30)
- `--include-jobs`: Include job execution stats
- `--include-users`: Include user statistics

**Output (Human-Readable)**:
```
System Statistics (Last 30 Days)
═════════════════════════════════

Users:
  Total: 15
  Active (last 7 days): 12
  Average subscriptions: 2.8

Subscriptions:
  Total active: 42
  System capacity: 42/100 (42%)

Analyses:
  Total runs: 1260 (42/day)
  Success rate: 95.2%
  Average duration: 4.3s

Deliveries:
  Total sent: 3780
  Success rate: 98.5%
  Average delay: 45s

Jobs:
  Total runs: 30
  Success rate: 100%
  Average duration: 9m 15s
```

**Output (JSON)**:
```json
{
  "period_days": 30,
  "users": {
    "total": 15,
    "active_last_7_days": 12,
    "average_subscriptions": 2.8
  },
  "subscriptions": {
    "total_active": 42,
    "system_capacity_used": 42,
    "system_capacity_max": 100,
    "capacity_percent": 42.0
  },
  "analyses": {
    "total_runs": 1260,
    "daily_average": 42.0,
    "success_rate": 95.2,
    "average_duration_seconds": 4.3
  },
  "deliveries": {
    "total_sent": 3780,
    "success_rate": 98.5,
    "average_delay_seconds": 45.0
  },
  "jobs": {
    "total_runs": 30,
    "success_rate": 100.0,
    "average_duration_seconds": 555.0
  }
}
```

---

## Environment Variables

```bash
# LLM API Keys (configure based on chosen provider)
STOCK_ANALYZER_LLM_PROVIDER      # LLM provider: "anthropic", "openai", or "gemini" (default: anthropic)
STOCK_ANALYZER_LLM_MODEL         # Model name (default varies by provider)

# Provider-specific API keys (set the one you're using)
ANTHROPIC_API_KEY                # Anthropic API key (for Claude models)
OPENAI_API_KEY                   # OpenAI API key (for GPT models)
GEMINI_API_KEY                   # Google Gemini API key

# Alternative: Single unified key variable (will use based on provider)
STOCK_ANALYZER_LLM_API_KEY       # Generic LLM API key

# Stock Data API
STOCK_ANALYZER_STOCK_API_KEY     # Stock data API key (Alpha Vantage, optional)
STOCK_ANALYZER_TELEGRAM_TOKEN    # Telegram bot token

# Configuration
STOCK_ANALYZER_DB_PATH           # Database file path (default: ./data/stock_analyzer.db)
STOCK_ANALYZER_LOG_LEVEL         # Log level (DEBUG, INFO, WARNING, ERROR)
STOCK_ANALYZER_CONFIG_FILE       # Config file path (default: ~/.stock-analyzer/config.toml)

# Limits
STOCK_ANALYZER_USER_LIMIT        # Max subscriptions per user (default: 10)
STOCK_ANALYZER_SYSTEM_LIMIT      # Max total subscriptions (default: 100)
STOCK_ANALYZER_ANALYSIS_TIMEOUT  # Analysis timeout in seconds (default: 60)
```

---

## Configuration File

`~/.stock-analyzer/config.toml`:

```toml
[api]
# Primary LLM provider configuration
llm_provider = "anthropic"  # Options: "anthropic", "openai", "gemini"
llm_model = "claude-sonnet-4-5"  # Model name (provider-specific)

# Fallback provider (optional)
llm_fallback_provider = "openai"
llm_fallback_model = "gpt-4o-mini"

# Stock data providers
stock_data_provider = "yfinance"
stock_data_backup = "alpha_vantage"

# Provider-specific settings
[api.anthropic]
enable_prompt_caching = true
max_tokens = 2048

[api.openai]
temperature = 0.7
max_tokens = 2048

[api.gemini]
temperature = 0.7
max_output_tokens = 2048

[limits]
user_subscriptions_max = 10
system_subscriptions_max = 100
analysis_timeout_seconds = 60
delivery_retry_max = 3

[storage]
db_path = "./data/stock_analyzer.db"
retention_days = 365

[telegram]
parse_mode = "Markdown"
disable_notification = false

[scheduling]
cron_schedule = "0 22 * * 1-5"  # 10 PM UTC, Mon-Fri
timezone = "UTC"
```

---

## Error Handling

All commands follow consistent error handling:

**Exit Codes**:
- `0`: Success
- `1`: Invalid arguments or input
- `2`: External service failure (API, database)
- `3`: Business logic error (limit exceeded, duplicate)
- `4`: System error (unexpected exception)

**Error Output (stderr)**:
```
Error: Invalid stock symbol 'INVALID'
  Symbol not found in market data API
  Use 'stock-analyzer validate INVALID' for details
```

**Error Output (JSON)**:
```json
{
  "status": "error",
  "error_code": "INVALID_SYMBOL",
  "error_message": "Invalid stock symbol 'INVALID'",
  "details": "Symbol not found in market data API",
  "suggestion": "Use 'stock-analyzer validate INVALID' for details"
}
```

---

## Testing

Test CLI commands without side effects:

```bash
# Dry run mode
stock-analyzer analyze AAPL --dry-run

# Use test database
STOCK_ANALYZER_DB_PATH=./test.db stock-analyzer analyze AAPL

# Mock external APIs (via environment variables or config)
STOCK_ANALYZER_MOCK_MODE=true stock-analyzer analyze AAPL
```

---

## Examples

```bash
# Analyze single stock with JSON output
stock-analyzer analyze AAPL --json

# Analyze with specific provider
STOCK_ANALYZER_LLM_PROVIDER=openai stock-analyzer analyze AAPL

# Analyze with Claude
export ANTHROPIC_API_KEY=sk-ant-...
stock-analyzer analyze AAPL

# Analyze with OpenAI
export OPENAI_API_KEY=sk-...
STOCK_ANALYZER_LLM_PROVIDER=openai stock-analyzer analyze TSLA

# Analyze with Gemini
export GEMINI_API_KEY=...
STOCK_ANALYZER_LLM_PROVIDER=gemini STOCK_ANALYZER_LLM_MODEL=gemini-2.5-flash stock-analyzer analyze MSFT

# Analyze batch from file
stock-analyzer analyze-batch stocks.txt --parallel 4 --progress

# Subscribe user to stock
stock-analyzer subscribe 123456789 AAPL --validate

# Query historical data
stock-analyzer history AAPL --start 2025-01-01 --limit 90

# Run daily job manually
stock-analyzer run-daily-job --dry-run

# Run daily job with specific provider
STOCK_ANALYZER_LLM_PROVIDER=gemini stock-analyzer run-daily-job

# Check system stats
stock-analyzer stats --period 30

# Pipe stock symbols to analyzer
echo -e "AAPL\nTSLA\nMSFT" | stock-analyzer analyze-batch --stdin --json
```

---

## Compatibility

- **Python**: 3.11+
- **Operating Systems**: Linux, macOS, Windows
- **Shell**: bash, zsh, fish, PowerShell
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins

---

## Version History

- **1.0.0** (2026-01-30): Initial CLI interface
