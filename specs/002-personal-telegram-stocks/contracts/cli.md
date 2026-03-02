# CLI Interface Contract: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Protocol**: Text in/out (stdin/args → stdout, errors → stderr)

## Overview

Command-line interface for personal stock monitoring. Supports JSON and human-readable output formats.

**Changes from Multi-User Version**:
- **REMOVED**: `subscribe`, `unsubscribe`, `list-subscriptions` commands
- **MODIFIED**: `run-daily-job` (reads stock list from config, not subscriptions)
- **RETAINED**: `init-db`, `analyze`, `history`, `validate`, `analyze-batch`

---

## Commands

### init-db

Initialize or migrate database schema.

**Usage**:
```bash
python -m stock_analyzer.cli init-db
```

**Arguments**: None

**Output**:
```text
Database initialized successfully at: ./data/stock_analyzer.db
```

**Exit Codes**:
- `0`: Success
- `1`: Database error

**Contract**:
```python
def init_db() -> int:
    """
    Initialize database schema.

    Behavior:
    - Creates database file if not exists
    - Drops users and subscriptions tables (migration)
    - Creates/updates all other tables
    - Idempotent (safe to run multiple times)

    Returns:
        0 on success, 1 on error
    """
```

**Test Assertions**:
- Running twice produces same result (idempotent)
- Database file created at config path
- All 4 tables exist: stock_analyses, insights, delivery_logs, analysis_jobs
- Users and subscriptions tables do not exist

---

### analyze

Analyze a single stock and display insights.

**Usage**:
```bash
# Human-readable output
python -m stock_analyzer.cli analyze AAPL

# JSON output
python -m stock_analyzer.cli analyze AAPL --json

# Force re-analysis (ignore cached)
python -m stock_analyzer.cli analyze AAPL --force

# Specific date
python -m stock_analyzer.cli analyze AAPL --date 2026-02-28
```

**Arguments**:
- `symbol` (required): Stock ticker symbol
- `--json`: Output as JSON
- `--force`: Force re-analysis even if today's analysis exists
- `--date YYYY-MM-DD`: Analyze for specific date (default: today)

**Output (Human-Readable)**:
```text
======================================================================
Stock Analysis: AAPL
Date: 2026-02-28
Confidence: HIGH
======================================================================

Summary:
Apple stock showed strong performance with 2.3% gain...

Trend Analysis:
Technical indicators suggest continued upward momentum...

Risk Factors:
  • Market volatility concerns
  • Regulatory pressures in EU

Opportunities:
  • Strong iPhone demand
  • Services revenue growth
```

**Output (JSON)**:
```json
{
  "status": "success",
  "stock_symbol": "AAPL",
  "analysis_date": "2026-02-28",
  "summary": "Apple stock showed strong performance...",
  "trend_analysis": "Technical indicators suggest...",
  "risk_factors": [
    "Market volatility concerns",
    "Regulatory pressures in EU"
  ],
  "opportunities": [
    "Strong iPhone demand",
    "Services revenue growth"
  ],
  "confidence_level": "high",
  "metadata": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5",
    "tokens_used": 1543
  }
}
```

**Error Output (JSON)**:
```json
{
  "status": "error",
  "error_type": "invalid_symbol",
  "error_message": "Stock symbol 'INVALID' not found"
}
```

**Exit Codes**:
- `0`: Success
- `1`: Invalid symbol
- `2`: Data fetch error
- `3`: Analysis error (LLM failure)

**Contract**:
```python
async def analyze(
    symbol: str,
    date: Optional[date] = None,
    force: bool = False,
    json_output: bool = False
) -> int:
    """
    Analyze a single stock.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
        date: Analysis date (defaults to today)
        force: Force re-analysis even if exists
        json_output: Output as JSON instead of human-readable

    Returns:
        Exit code (0=success, 1=invalid symbol, 2=fetch error, 3=analysis error)

    Output:
        - stdout: Analysis results (JSON or text)
        - stderr: Error messages (if any)
    """
```

**Test Assertions**:
- Valid symbol returns 0 and prints insight
- Invalid symbol returns 1 and prints error to stderr
- JSON output is valid JSON
- Human output contains symbol, date, confidence, summary, risks, opportunities
- Force flag bypasses cached analysis
- Same symbol analyzed twice without force returns cached result

---

### history

Query historical analysis insights for a stock.

**Usage**:
```bash
# All history for AAPL
python -m stock_analyzer.cli history AAPL

# With date range
python -m stock_analyzer.cli history AAPL --start 2026-02-01 --end 2026-02-28

# With pagination
python -m stock_analyzer.cli history AAPL --limit 10 --offset 0

# JSON output
python -m stock_analyzer.cli history AAPL --json
```

**Arguments**:
- `symbol` (required): Stock ticker symbol
- `--start YYYY-MM-DD`: Start date (default: no limit)
- `--end YYYY-MM-DD`: End date (default: no limit)
- `--limit N`: Max results (default: 100)
- `--offset N`: Skip first N results (default: 0)
- `--json`: Output as JSON

**Output (Human-Readable)**:
```text
Historical Insights for AAPL
Found 15 insights from 2026-02-01 to 2026-02-28

========================================
Date: 2026-02-28 | Confidence: HIGH
========================================
Summary: Apple stock showed strong performance...
Risks: Market volatility, Regulatory pressures
Opportunities: Strong iPhone demand, Services growth

[... more insights ...]
```

**Output (JSON)**:
```json
{
  "status": "success",
  "stock_symbol": "AAPL",
  "total_count": 15,
  "insights": [
    {
      "analysis_date": "2026-02-28",
      "summary": "...",
      "trend_analysis": "...",
      "risk_factors": ["..."],
      "opportunities": ["..."],
      "confidence_level": "high",
      "created_at": "2026-02-28T22:15:30Z"
    }
  ]
}
```

**Exit Codes**:
- `0`: Success (even if 0 results)
- `1`: Invalid arguments

**Contract**:
```python
def history(
    symbol: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
    json_output: bool = False
) -> int:
    """
    Query historical insights for a stock.

    Args:
        symbol: Stock ticker symbol
        start: Start date (inclusive)
        end: End date (inclusive)
        limit: Maximum results
        offset: Skip first N results
        json_output: Output as JSON

    Returns:
        Exit code (0=success, 1=invalid args)

    Output:
        - stdout: Historical insights (JSON or text)
        - stderr: Error messages (if any)
    """
```

**Test Assertions**:
- Returns all insights for symbol within date range
- Results sorted by date descending (newest first)
- Pagination works correctly (limit + offset)
- Empty result returns success (0) with "No insights found" message
- JSON output is valid JSON array

---

### validate

Validate a stock symbol without running analysis.

**Usage**:
```bash
python -m stock_analyzer.cli validate AAPL
python -m stock_analyzer.cli validate INVALID
```

**Arguments**:
- `symbol` (required): Stock ticker symbol

**Output (Valid)**:
```text
✓ AAPL is a valid stock symbol
```

**Output (Invalid)**:
```text
✗ INVALID is not a valid stock symbol
```

**Exit Codes**:
- `0`: Valid symbol
- `1`: Invalid symbol

**Contract**:
```python
def validate(symbol: str) -> int:
    """
    Validate stock symbol.

    Args:
        symbol: Stock ticker to validate

    Returns:
        0 if valid, 1 if invalid

    Output:
        - stdout: Validation result
    """
```

**Test Assertions**:
- Known valid symbols (AAPL, MSFT, GOOGL) return 0
- Invalid symbols (INVALID, 123, empty) return 1
- Output includes checkmark/cross and clear message

---

### analyze-batch

Analyze multiple stocks in parallel.

**Usage**:
```bash
# Analyze 3 stocks sequentially
python -m stock_analyzer.cli analyze-batch AAPL MSFT GOOGL

# Analyze with parallelism
python -m stock_analyzer.cli analyze-batch AAPL MSFT GOOGL --parallel 2

# JSON output
python -m stock_analyzer.cli analyze-batch AAPL MSFT GOOGL --json
```

**Arguments**:
- `symbols...` (required): One or more stock symbols
- `--parallel N`: Number of parallel workers (default: 1)
- `--continue-on-error`: Continue if one stock fails (default: true)
- `--json`: Output as JSON

**Output (Human-Readable)**:
```text
Analyzing 3 stocks with parallelism=2...

[1/3] AAPL: ✓ Success (12.3s)
[2/3] MSFT: ✓ Success (10.8s)
[3/3] GOOGL: ✗ Failed: Rate limit exceeded

========================================
Batch Analysis Complete
========================================
Total: 3 | Success: 2 | Failed: 1
Duration: 23.5 seconds
```

**Output (JSON)**:
```json
{
  "status": "completed",
  "total": 3,
  "success_count": 2,
  "failure_count": 1,
  "duration_seconds": 23.5,
  "results": [
    {
      "stock_symbol": "AAPL",
      "status": "success",
      "duration_seconds": 12.3
    },
    {
      "stock_symbol": "MSFT",
      "status": "success",
      "duration_seconds": 10.8
    },
    {
      "stock_symbol": "GOOGL",
      "status": "failed",
      "error_message": "Rate limit exceeded",
      "duration_seconds": 0.2
    }
  ]
}
```

**Exit Codes**:
- `0`: All succeeded
- `1`: Some failed (with --continue-on-error)
- `2`: All failed

**Contract**:
```python
async def analyze_batch(
    symbols: List[str],
    parallel: int = 1,
    continue_on_error: bool = True,
    json_output: bool = False
) -> int:
    """
    Analyze multiple stocks in parallel.

    Args:
        symbols: List of stock symbols
        parallel: Number of parallel workers
        continue_on_error: Continue if one fails
        json_output: Output as JSON

    Returns:
        0 if all succeeded, 1 if some failed, 2 if all failed

    Output:
        - stdout: Batch results (JSON or text)
        - stderr: Individual stock errors
    """
```

**Test Assertions**:
- Processes all symbols
- Parallelism reduces total time (parallel=2 is ~2x faster than parallel=1)
- continue_on_error=True processes all stocks despite failures
- Exit code reflects overall status

---

### run-daily-job

Run the automated daily analysis workflow.

**Usage**:
```bash
# Run analysis for configured stock list
python -m stock_analyzer.cli run-daily-job

# Dry run (show what would be analyzed)
python -m stock_analyzer.cli run-daily-job --dry-run
```

**Arguments**:
- `--dry-run`: Show stock list without analyzing

**Output (Normal)**:
```text
Starting daily analysis job...
Configuration loaded. Database: ./data/stock_analyzer.db

Stock list from STOCK_ANALYZER_STOCK_LIST: AAPL, MSFT, GOOGL, TSLA, NVDA
Analyzing 5 stocks...

[1/5] AAPL: ✓ Success (11.2s)
[2/5] MSFT: ✓ Success (10.5s)
[3/5] GOOGL: ✓ Success (12.8s)
[4/5] TSLA: ✗ Failed: Invalid symbol
[5/5] NVDA: ✓ Success (9.7s)

Analysis complete: 4 success, 1 failed, duration=44.2s

Delivering insights to Telegram channel: @mystockchannel
[1/4] AAPL insight delivered
[2/4] MSFT insight delivered
[3/4] GOOGL insight delivered
[4/4] NVDA insight delivered

Delivery complete: 4 total, 4 success, 0 failed

Daily analysis job completed successfully
```

**Output (Dry Run)**:
```text
DRY RUN MODE - No analysis will be performed

Configuration:
- Stock list: AAPL, MSFT, GOOGL, TSLA, NVDA
- Telegram channel: @mystockchannel
- Database: ./data/stock_analyzer.db

Would analyze 5 stocks:
  1. AAPL
  2. MSFT
  3. GOOGL
  4. TSLA
  5. NVDA
```

**Exit Codes**:
- `0`: Success (all or most stocks analyzed)
- `1`: Configuration error (stock list empty, channel not configured)
- `2`: Complete failure (no stocks analyzed)

**Contract**:
```python
async def run_daily_job(dry_run: bool = False) -> int:
    """
    Run automated daily analysis workflow.

    Workflow:
    1. Load config and parse stock list
    2. Validate stock symbols
    3. Analyze each stock (parallel=2)
    4. Deliver insights to Telegram channel
    5. Log job execution

    Args:
        dry_run: Show config without running analysis

    Returns:
        0=success, 1=config error, 2=complete failure

    Output:
        - stdout: Job progress and results
        - stderr: Errors
    """
```

**Test Assertions**:
- Dry run shows stock list and exits without analyzing
- Reads stock list from STOCK_ANALYZER_STOCK_LIST env var
- Fails with clear error if stock list empty
- Analyzes all stocks in list
- Posts insights to STOCK_ANALYZER_TELEGRAM_CHANNEL
- Logs job execution to analysis_jobs table
- Invalid symbols are skipped with warning (don't block job)

---

## Removed Commands

These commands are **no longer available** in the personal version:

### subscribe (REMOVED)
Previously: Subscribe user to stock
Reason: Stock list is now environment-configured

### unsubscribe (REMOVED)
Previously: Unsubscribe user from stock
Reason: No user-based subscriptions

### list-subscriptions (REMOVED)
Previously: List user's subscriptions
Reason: Stock list is in config, not database

**Migration Note**: Users should set `STOCK_ANALYZER_STOCK_LIST` environment variable instead of using subscribe commands.

---

## Testing Strategy

### Contract Tests

```python
def test_cli_analyze_valid_symbol():
    """Contract: analyze returns 0 for valid symbol and prints insight."""
    result = subprocess.run(
        ["python", "-m", "stock_analyzer.cli", "analyze", "AAPL", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert data["stock_symbol"] == "AAPL"

def test_cli_analyze_invalid_symbol():
    """Contract: analyze returns 1 for invalid symbol and prints error."""
    result = subprocess.run(
        ["python", "-m", "stock_analyzer.cli", "analyze", "INVALID"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "error" in result.stderr.lower() or "invalid" in result.stderr.lower()

def test_cli_history_returns_insights():
    """Contract: history returns all insights for symbol."""
    # Setup: Create test insights
    # ...

    result = subprocess.run(
        ["python", "-m", "stock_analyzer.cli", "history", "AAPL", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert len(data["insights"]) > 0

def test_cli_run_daily_job_reads_stock_list():
    """Contract: run-daily-job reads STOCK_ANALYZER_STOCK_LIST."""
    env = os.environ.copy()
    env["STOCK_ANALYZER_STOCK_LIST"] = "AAPL,MSFT"
    env["STOCK_ANALYZER_TELEGRAM_CHANNEL"] = "@testchannel"

    result = subprocess.run(
        ["python", "-m", "stock_analyzer.cli", "run-daily-job", "--dry-run"],
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0
    assert "AAPL" in result.stdout
    assert "MSFT" in result.stdout
```

---

## Summary

**Total Commands**: 6
- **Removed**: 3 (`subscribe`, `unsubscribe`, `list-subscriptions`)
- **Modified**: 1 (`run-daily-job`)
- **Unchanged**: 5 (`init-db`, `analyze`, `history`, `validate`, `analyze-batch`)

**Key Changes**:
- `run-daily-job` reads `STOCK_ANALYZER_STOCK_LIST` instead of querying subscriptions
- All commands work without user context
- CLI interface protocol unchanged (text in/out, JSON support)

**Status**: ✅ CLI Contract Complete
