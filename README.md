# AlphaAgent - AI-Powered Personal Stock Analysis

Automated personal stock analysis system that uses AI (LLM) to analyze your stock watchlist daily and deliver insights to your Telegram channel.

**Status:** ✅ Production Ready | **Tests:** 229 passing (100%)

## Features

- 🤖 **Multi-Provider LLM Support**: Claude, OpenAI, and Gemini
- 📊 **Daily Stock Analysis**: Automated analysis powered by AI for your personal watchlist
- 📱 **Telegram Channel Delivery**: Receive insights directly to your personal Telegram channel
- ⚡ **On-Demand Analysis**: Get instant insights for any stock
- 📈 **Historical Insights**: Query past analyses with date filtering
- 🔄 **Automated Workflow**: Runs daily via GitHub Actions
- 💾 **Git-Committed Storage**: SQLite database persisted across workflow runs
- 🧪 **Comprehensive Testing**: 229 tests (contract, integration, unit)
- 📝 **Personal Use**: Designed for individual use without multi-user complexity

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram account with a channel
- API key for one of: Anthropic Claude, OpenAI, or Google Gemini

### Installation

```bash
# Clone repository
git clone <repository-url>
cd AlphaAgent

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

### Personal Setup (5 Minutes)

#### 1. Create Your Telegram Channel

1. Open Telegram and create a new channel (Settings → New Channel)
2. Choose a name like "My Stock Insights"
3. Make it private or public (your choice)
4. Copy your channel username (e.g., `@mystockinsights`) or numeric ID

#### 2. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token provided (looks like `123456:ABC-DEF...`)
4. Add your bot as an administrator to your channel with "Post Messages" permission

#### 3. Configure Your Stock List

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure your personal settings:
   ```bash
   # Choose your LLM provider
   STOCK_ANALYZER_LLM_PROVIDER=anthropic  # or "openai" or "gemini"

   # Add your API key (choose one)
   ANTHROPIC_API_KEY=sk-ant-...
   # OR
   OPENAI_API_KEY=sk-...
   # OR
   GEMINI_API_KEY=...

   # Add your personal stock list (comma-separated)
   STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL,TSLA,NVDA

   # Add your Telegram channel ID
   STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockinsights

   # Add Telegram bot token from @BotFather
   STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...

   # Optional: Alpha Vantage for fallback stock data
   STOCK_ANALYZER_STOCK_API_KEY=...
   ```

#### 4. Test Your Setup

```bash
# Initialize database
python -m stock_analyzer.cli init-db

# Test analysis for one stock
python -m stock_analyzer.cli analyze AAPL

# Test daily job in dry-run mode
python -m stock_analyzer.cli run-daily-job --dry-run

# Run actual daily job (posts to your channel)
python -m stock_analyzer.cli run-daily-job
```

✅ **You're all set!** Your channel will now receive daily insights for your stock list.

### Usage

#### Command Line Interface

**Database Management:**
```bash
# Initialize database (creates tables)
python -m stock_analyzer.cli init-db
```

**Stock Analysis:**
```bash
# Analyze a single stock
python -m stock_analyzer.cli analyze AAPL

# Analyze with JSON output
python -m stock_analyzer.cli analyze MSFT --json

# Analyze multiple stocks in parallel
python -m stock_analyzer.cli analyze-batch AAPL MSFT GOOGL --parallel 2

# Validate a stock symbol
python -m stock_analyzer.cli validate AAPL
```

**Historical Data:**
```bash
# View all historical insights for a stock
python -m stock_analyzer.cli history AAPL

# Filter by date range
python -m stock_analyzer.cli history AAPL --start 2026-01-01 --end 2026-02-01

# Pagination (first 10 results)
python -m stock_analyzer.cli history AAPL --limit 10 --offset 0

# JSON output
python -m stock_analyzer.cli history AAPL --json
```

**Daily Analysis Job (Personal Stock List):**
```bash
# Run daily analysis job (analyzes stocks from STOCK_ANALYZER_STOCK_LIST)
python -m stock_analyzer.cli run-daily-job

# Dry run (show what would be analyzed)
python -m stock_analyzer.cli run-daily-job --dry-run
```

**Note:** The daily job reads your stock list from `STOCK_ANALYZER_STOCK_LIST` environment variable and posts insights to your Telegram channel specified in `STOCK_ANALYZER_TELEGRAM_CHANNEL`.

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=stock_analyzer --cov-report=html

# Run specific test types
uv run pytest tests/unit/          # Unit tests
uv run pytest tests/integration/   # Integration tests
uv run pytest tests/contract/      # Contract tests

# Run specific user story tests
uv run pytest -k US1  # Personal stock list configuration
uv run pytest -k US2  # Telegram channel delivery
uv run pytest -k US3  # Historical access
```

**Test Results:** 229 tests passing
- User Story 1 (Personal Stock List): 141 tests ✅
- User Story 2 (Channel Delivery): 44 tests ✅
- User Story 3 (Historical Queries): 44 tests ✅

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│           GitHub Actions                     │
│  • Daily Analysis (Mon-Fri 10 PM UTC)      │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│        Stock Analyzer System                │
│                                             │
│  ┌──────────┐  ┌─────────┐                │
│  │ Analyzer │  │   CLI   │                │
│  │  (LLM)   │  │(Local)  │                │
│  └────┬─────┘  └────┬────┘                │
│       │             │                       │
│       └─────────────┼───────────────────┐  │
│                     │                    │  │
│       ┌─────────────▼──────────────┐    │  │
│       │    Storage (SQLite)        │    │  │
│       │  • Stock Analyses          │    │  │
│       │  • Insights                │    │  │
│       │  • Delivery Logs & Jobs    │    │  │
│       └────────────────────────────┘    │  │
│                                          │  │
│       ┌──────────────────────────────┐  │  │
│       │   Deliverer (Telegram)       │◄─┘  │
│       │  • Channel Posting           │     │
│       └──────────────────────────────┘     │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         External Services                    │
│  • LLM APIs (Claude/GPT/Gemini)            │
│  • Stock Data (yfinance/Alpha Vantage)     │
│  • Telegram Bot API (Channel Posts)        │
└─────────────────────────────────────────────┘
```

### Project Structure

```
AlphaAgent/
├── src/
│   └── stock_analyzer/
│       ├── __init__.py
│       ├── cli.py              # CLI interface with all commands
│       ├── models.py           # Data models (StockAnalysis, Insight, etc.)
│       ├── config.py           # Configuration management
│       ├── exceptions.py       # Custom exceptions
│       ├── fetcher.py          # Stock data fetching (yfinance + Alpha Vantage)
│       ├── analyzer.py         # LLM-based stock analysis
│       ├── deliverer.py        # Insight delivery (Telegram channel)
│       ├── storage.py          # SQLite database operations
│       └── llm_client.py       # LLM provider abstraction
├── src/scripts/
│   └── daily_analysis.py       # Automated daily job
├── tests/
│   ├── contract/               # Contract tests (API behavior)
│   ├── integration/            # Integration tests (end-to-end)
│   └── unit/                   # Unit tests (component-level)
├── data/
│   └── stock_analyzer.db       # SQLite database (Git-tracked)
├── specs/
│   ├── 001-llm-stock-analyzer/ # Original feature documentation
│   └── 002-personal-telegram-stocks/ # Personal use refactoring
├── .github/
│   └── workflows/
│       └── daily-analysis.yml  # Scheduled analysis job
├── pyproject.toml              # Project dependencies
├── pytest.ini                  # Test configuration
└── README.md                   # This file
```

### Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: uv (fast, modern)
- **LLM Providers**: Anthropic Claude, OpenAI, Google Gemini
- **Stock Data**: yfinance (primary), Alpha Vantage (fallback)
- **Telegram**: python-telegram-bot v20.x (async)
- **Storage**: SQLite with Git commits
- **Testing**: pytest with pytest-asyncio
- **CI/CD**: GitHub Actions

## LLM Provider Comparison

| Provider | Model | Context | Monthly Cost* | Best For |
|----------|-------|---------|--------------|----------|
| **Anthropic Claude** | claude-sonnet-4-5 | 200K | $18-27 | Best reasoning, prompt caching (90% cost reduction) |
| **OpenAI** | gpt-4o | 128K | $30-50 | Mature ecosystem, widespread adoption |
| **Google Gemini** | gemini-2.5-pro | 2M | $6-15 | Budget option, large context, fast |

*Estimated for 100 stock analyses/day, 20 trading days/month

**Recommendation:** Anthropic Claude with prompt caching for best cost/performance.

## Configuration

### Environment Variables

**Required:**
- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` or `GEMINI_API_KEY`)
- `STOCK_ANALYZER_TELEGRAM_TOKEN` - Bot token from @BotFather
- `STOCK_ANALYZER_STOCK_LIST` - Comma-separated stock symbols
- `STOCK_ANALYZER_TELEGRAM_CHANNEL` - Channel username or ID

**Optional:**
- `STOCK_ANALYZER_LLM_PROVIDER` (default: `anthropic`)
- `STOCK_ANALYZER_LLM_MODEL` (uses provider default if not set)
- `STOCK_ANALYZER_STOCK_API_KEY` (Alpha Vantage for fallback)
- `STOCK_ANALYZER_DB_PATH` (default: `./data/stock_analyzer.db`)
- `STOCK_ANALYZER_LOG_LEVEL` (default: `INFO`)

### Personal Use Configuration

- **Stock List**: Configured via environment variable (comma-separated)
- **Delivery**: Daily at 10 PM UTC (Mon-Fri) to your personal Telegram channel
- **On-demand**: Unlimited analysis via CLI commands
- **Storage**: All historical data persisted in SQLite database

## Deployment

### Local Development

1. Install dependencies: `uv pip install -e .`
2. Configure `.env` file with your settings
3. Initialize database: `python -m stock_analyzer.cli init-db`
4. Test analysis: `python -m stock_analyzer.cli run-daily-job --dry-run`

### GitHub Actions (Production)

**Setup:**

1. **Add repository secrets** (Settings → Secrets and variables → Actions):
   - `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` or `GEMINI_API_KEY`)
   - `TELEGRAM_TOKEN` - Your Telegram bot token
   - `STOCK_LIST` - Comma-separated stock symbols (e.g., `AAPL,MSFT,GOOGL`)
   - `TELEGRAM_CHANNEL` - Your channel username (e.g., `@mystockinsights`)
   - `ALPHA_VANTAGE_KEY` - (Optional) For stock data fallback

2. **Enable workflow:**
   - `.github/workflows/daily-analysis.yml` - Automated daily analysis

3. **Verify database:**
   - `data/stock_analyzer.db` is committed to repository
   - GitHub Actions will read/write this file
   - Changes are auto-committed after each run

**Daily Analysis Workflow:**
- **Schedule**: Monday-Friday at 10 PM UTC (after market close)
- **Actions**: Reads stock list → Analyzes stocks → Delivers to channel → Commits database
- **Manual Trigger**: Available via "Run workflow" button

## Troubleshooting

### Database Issues

**Problem:** Database not initialized
```bash
# Solution: Run init-db command
python -m stock_analyzer.cli init-db
```

**Problem:** Database locked
```bash
# Solution: Close other connections or delete .db-wal and .db-shm files
rm data/stock_analyzer.db-wal data/stock_analyzer.db-shm
```

### API Issues

**Problem:** LLM API rate limits
```bash
# Solution: Use prompt caching (Claude) or reduce parallel analysis
# Edit config or use --parallel 1 flag
```

**Problem:** Stock data fetch fails
```bash
# Solution: Add Alpha Vantage key for fallback
export STOCK_ANALYZER_STOCK_API_KEY=your-key
```

### Telegram Delivery Issues

**Problem:** Messages not posting to channel
```bash
# Solution: Verify bot is added as channel admin with "Post Messages" permission
# Check STOCK_ANALYZER_TELEGRAM_CHANNEL is correct (e.g., @mystockinsights)
```

**Problem:** Channel not found error
```bash
# Solution: Ensure channel username starts with @ or use numeric channel ID
# Verify bot token is valid: check STOCK_ANALYZER_TELEGRAM_TOKEN
```

### Testing Issues

**Problem:** Tests failing
```bash
# Solution: Install dev dependencies
uv pip install -e ".[dev]"

# Run tests with verbose output
uv run pytest -v
```

## Development

### Code Quality

```bash
# Format code (if installed)
black src/ tests/
isort src/ tests/

# Type check (if installed)
mypy src/
```

### Adding New Features

1. Write tests first (TDD - Red phase)
2. Implement feature (Green phase)
3. Refactor code (Refactor phase)
4. Update documentation
5. Run full test suite

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Testing guidelines
- Code style
- Pull request process

## Documentation

Detailed documentation available:
- [Feature Specification](specs/001-llm-stock-analyzer/spec.md)
- [Implementation Plan](specs/001-llm-stock-analyzer/plan.md)
- [Task List](specs/001-llm-stock-analyzer/tasks.md)
- Test Reports:
  - [MVP Test Report](/tmp/MVP_TEST_REPORT.md)
  - [User Story 2 Report](/tmp/US2_IMPLEMENTATION_REPORT.md)
  - [User Story 3 Report](/tmp/US3_IMPLEMENTATION_REPORT.md)
  - [Final MVP Report](/tmp/MVP_COMPLETE_FINAL_REPORT.md)

## Project Status

**Current Version:** 2.0.0 (Personal Use Edition)

**Features:**
- ✅ Personal stock list configuration (US1)
- ✅ Telegram channel delivery (US2)
- ✅ Historical access (US3)
- ✅ On-demand CLI analysis
- ✅ Automated daily workflow
- ✅ 229 passing tests

**Recent Changes (v2.0):**
- ✅ Removed multi-user support for simplicity
- ✅ Environment-based stock list configuration
- ✅ Direct channel posting (no bot commands)
- ✅ Simplified database schema

**Roadmap:**
- 📝 Enhanced logging and monitoring
- 📝 Rate limiting with exponential backoff
- 📝 CI workflow for automated testing
- 📝 Future: Portfolio tracking, price alerts, web dashboard

## Constitution

This project follows the [AlphaAgent Constitution](.specify/memory/constitution.md):

1. **Test-First (NON-NEGOTIABLE)**: TDD workflow, Red-Green-Refactor
2. **Library-First**: Standalone library with CLI wrapper
3. **CLI Interface**: Text in/out protocol, JSON support
4. **Integration Testing**: Contract and integration tests required
5. **Simplicity**: No premature optimization, minimal abstractions

## License

[Add your license here]

## Support

- **Documentation**: Check `specs/` directory
- **Issues**: Create GitHub issue with error details
- **Questions**: Open GitHub discussion
- **Email**: [Add your support email]

---

**Built with ❤️ using Claude Code and TDD principles**

**Status**: ✅ Production Ready | **Tests**: 229/229 Passing (100%)
