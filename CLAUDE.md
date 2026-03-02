# AlphaAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-02

## Version

**Current**: 2.0.0 (Personal Use Edition)

## Active Technologies

- Python 3.11+ (001-llm-stock-analyzer)
- SQLite database (`./data/stock_analyzer.db`) (002-personal-telegram-stocks)
- Multi-Provider LLM Support: Anthropic Claude, OpenAI, Google Gemini
- Telegram Bot API (channel posting)
- yfinance + Alpha Vantage (stock data)
- pytest (testing framework)

## Project Structure

```text
src/
  stock_analyzer/
    __init__.py
    cli.py              # CLI interface
    models.py           # Data models (personal use - no User/Subscription)
    config.py           # Configuration management
    storage.py          # SQLite operations (simplified schema)
    analyzer.py         # LLM-based analysis
    deliverer.py        # Telegram channel delivery
    fetcher.py          # Stock data fetching
    llm_client.py       # Multi-provider LLM abstraction
  scripts/
    daily_analysis.py   # Automated daily workflow
tests/
  contract/             # Contract tests
  integration/          # Integration tests
  unit/                 # Unit tests
data/
  stock_analyzer.db     # Git-tracked database
docs/
  MIGRATION.md          # v1.x → v2.0 migration guide
```

## Commands

```bash
# Setup
uv pip install -e .                    # Install dependencies
python -m stock_analyzer.cli init-db   # Initialize database

# Analysis
python -m stock_analyzer.cli analyze AAPL
python -m stock_analyzer.cli run-daily-job --dry-run

# Testing
pytest                                  # Run all tests
pytest tests/unit/                      # Unit tests only
pytest -k US1                           # User story 1 tests

# Code Quality
ruff check .                            # Linting
black src/ tests/                       # Formatting
```

## Code Style

Python 3.11+: Follow standard conventions
- Black formatting (line length: 100)
- isort for imports
- Type hints where beneficial
- Docstrings for public APIs

## Architecture Notes

**Personal Use Design**:
- Environment-based configuration (no user accounts)
- Direct channel delivery (no bot commands)
- Simplified database schema (no users/subscriptions tables)
- Stock list configured via STOCK_ANALYZER_STOCK_LIST
- Delivers to STOCK_ANALYZER_TELEGRAM_CHANNEL

**Database Schema**:
- `stock_analyses`: Stock price data and analysis metadata
- `insights`: AI-generated insights (no user_id, uses channel_id)
- `delivery_logs`: Channel delivery tracking
- `analysis_jobs`: Job execution history

## Recent Changes

- 002-personal-telegram-stocks (v2.0): Refactored to personal use, removed multi-user support
- 001-llm-stock-analyzer (v1.0): Initial multi-user implementation

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
