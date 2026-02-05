# AlphaAgent - AI-Powered Stock Analysis

Automated stock analysis system that uses AI (LLM) to analyze stock market data daily and deliver insights to users via Telegram.

**Status:** ✅ Production Ready | **Tests:** 229 passing (100%)

## Features

- 🤖 **Multi-Provider LLM Support**: Claude, OpenAI, and Gemini
- 📊 **Daily Stock Analysis**: Automated analysis powered by AI
- 📱 **Telegram Bot**: Subscribe to stocks and receive insights
- ⚡ **On-Demand Analysis**: Get instant insights for any stock
- 📈 **Historical Insights**: Query past analyses with date filtering
- 🔄 **Automated Workflow**: Runs daily via GitHub Actions
- 💾 **Git-Committed Storage**: SQLite database persisted across workflow runs
- 🧪 **Comprehensive Testing**: 229 tests (contract, integration, unit)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram account for bot interaction
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

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Choose your LLM provider
   STOCK_ANALYZER_LLM_PROVIDER=anthropic  # or "openai" or "gemini"

   # Add your API key (choose one)
   ANTHROPIC_API_KEY=sk-ant-...
   # OR
   OPENAI_API_KEY=sk-...
   # OR
   GEMINI_API_KEY=...

   # Add Telegram bot token from @BotFather
   STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...

   # Optional: Alpha Vantage for fallback stock data
   STOCK_ANALYZER_STOCK_API_KEY=...

   # Optional: Custom database path
   STOCK_ANALYZER_DB_PATH=./data/stock_analyzer.db
   ```

3. Initialize the database:
   ```bash
   python -m stock_analyzer.cli init-db
   ```

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
```

**Subscription Management:**
```bash
# Subscribe user to stock
python -m stock_analyzer.cli subscribe <user_id> AAPL

# Unsubscribe user from stock
python -m stock_analyzer.cli unsubscribe <user_id> AAPL

# List all subscriptions
python -m stock_analyzer.cli list-subscriptions

# List specific user's subscriptions
python -m stock_analyzer.cli list-subscriptions <user_id>

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

**Daily Analysis Job:**
```bash
# Run daily analysis job (analyzes all subscriptions)
python -m stock_analyzer.cli run-daily-job

# Dry run (show what would be analyzed)
python -m stock_analyzer.cli run-daily-job --dry-run
```

#### Telegram Bot

**Start the bot locally:**
```bash
python src/scripts/run_bot.py
```

**Available commands:**

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start using the bot | `/start` |
| `/help` | Show help message | `/help` |
| `/subscribe <symbol>` | Subscribe to daily insights | `/subscribe AAPL` |
| `/unsubscribe <symbol>` | Unsubscribe from stock | `/unsubscribe MSFT` |
| `/list` | Show your subscriptions | `/list` |
| `/analyze <symbol>` | Get instant analysis | `/analyze TSLA` |
| `/history <symbol> [days]` | View historical insights | `/history AAPL 7` |

**Bot Features:**
- ✅ Real-time symbol validation
- ✅ Subscription limit enforcement (10 per user)
- ✅ On-demand analysis (instant insights)
- ✅ Historical queries with date filtering
- ✅ Markdown formatting
- ✅ Error handling and user-friendly messages

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
uv run pytest -k US1  # Daily analysis
uv run pytest -k US2  # Subscription management
uv run pytest -k US3  # Historical access
```

**Test Results:** 229 tests passing
- User Story 1 (Daily Analysis): 141 tests ✅
- User Story 2 (Subscriptions): 44 tests ✅
- User Story 3 (History): 44 tests ✅

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│           GitHub Actions                     │
│  • Daily Analysis (Mon-Fri 10 PM UTC)      │
│  • Telegram Bot (Continuous/Manual)        │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│        Stock Analyzer System                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Analyzer │  │   Bot    │  │   CLI   │ │
│  │  (LLM)   │  │(Telegram)│  │(Local)  │ │
│  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │             │               │      │
│       └─────────────┼───────────────┘      │
│                     │                      │
│       ┌─────────────▼──────────────┐      │
│       │    Storage (SQLite)        │      │
│       │  • Users & Subscriptions   │      │
│       │  • Analyses & Insights     │      │
│       │  • Delivery Logs & Jobs    │      │
│       └────────────────────────────┘      │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         External Services                    │
│  • LLM APIs (Claude/GPT/Gemini)            │
│  • Stock Data (yfinance/Alpha Vantage)     │
│  • Telegram Bot API                         │
└─────────────────────────────────────────────┘
```

### Project Structure

```
AlphaAgent/
├── src/
│   └── stock_analyzer/
│       ├── __init__.py
│       ├── cli.py              # CLI interface with all commands
│       ├── models.py           # Data models (User, Subscription, etc.)
│       ├── config.py           # Configuration management
│       ├── exceptions.py       # Custom exceptions
│       ├── fetcher.py          # Stock data fetching (yfinance + Alpha Vantage)
│       ├── analyzer.py         # LLM-based stock analysis
│       ├── deliverer.py        # Insight delivery (Telegram)
│       ├── storage.py          # SQLite database operations
│       ├── llm_client.py       # LLM provider abstraction
│       └── bot.py              # Telegram bot with commands
├── src/scripts/
│   ├── daily_analysis.py       # Automated daily job
│   └── run_bot.py              # Bot startup script
├── tests/
│   ├── contract/               # Contract tests (API behavior)
│   ├── integration/            # Integration tests (end-to-end)
│   └── unit/                   # Unit tests (component-level)
├── data/
│   └── stock_analyzer.db       # SQLite database (Git-tracked)
├── specs/
│   └── 001-llm-stock-analyzer/ # Feature documentation
├── .github/
│   └── workflows/
│       ├── daily-analysis.yml  # Scheduled analysis job
│       └── telegram-bot.yml    # Bot deployment
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
- `STOCK_ANALYZER_TELEGRAM_TOKEN`

**Optional:**
- `STOCK_ANALYZER_LLM_PROVIDER` (default: `anthropic`)
- `STOCK_ANALYZER_LLM_MODEL` (uses provider default if not set)
- `STOCK_ANALYZER_STOCK_API_KEY` (Alpha Vantage for fallback)
- `STOCK_ANALYZER_DB_PATH` (default: `./data/stock_analyzer.db`)
- `STOCK_ANALYZER_LOG_LEVEL` (default: `INFO`)
- `STOCK_ANALYZER_USER_LIMIT` (default: `10`)
- `STOCK_ANALYZER_SYSTEM_LIMIT` (default: `100`)

### Subscription Limits

- **Per User**: 10 stocks maximum
- **System-wide**: 100 stocks total
- **Delivery**: Daily at 10 PM UTC (Mon-Fri)
- **On-demand**: Unlimited `/analyze` commands

## Deployment

### Local Development

1. Install dependencies
2. Configure `.env` file
3. Initialize database: `python -m stock_analyzer.cli init-db`
4. Run bot: `python src/scripts/run_bot.py`

### GitHub Actions (Production)

**Setup:**

1. **Add repository secrets** (Settings → Secrets and variables → Actions):
   - `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` or `GEMINI_API_KEY`)
   - `TELEGRAM_TOKEN` - Your Telegram bot token
   - `ALPHA_VANTAGE_KEY` - (Optional) For stock data fallback

2. **Enable workflows:**
   - `.github/workflows/daily-analysis.yml` - Automated daily analysis
   - `.github/workflows/telegram-bot.yml` - Bot deployment (optional)

3. **Verify database:**
   - `data/stock_analyzer.db` is committed to repository
   - GitHub Actions will read/write this file
   - Changes are auto-committed after each run

**Daily Analysis Workflow:**
- **Schedule**: Monday-Friday at 10 PM UTC (after market close)
- **Actions**: Fetches subscriptions → Analyzes stocks → Delivers insights → Commits database
- **Manual Trigger**: Available via "Run workflow" button

**Telegram Bot Workflow:**
- **Mode**: Polling (development) or Webhook (production)
- **Deployment**: VPS recommended for 24/7 operation
- **GitHub Actions**: 1-hour timeout (use for testing only)

### Production Deployment (VPS/Cloud)

**Recommended setup for 24/7 bot operation:**

```bash
# On your server
git clone <repository-url>
cd AlphaAgent

# Setup
uv pip install -e .
cp .env.example .env
# Edit .env with production keys

# Initialize database
python -m stock_analyzer.cli init-db

# Run bot with systemd or supervisor
# Example systemd service:
[Unit]
Description=Stock Analyzer Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/AlphaAgent
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/python src/scripts/run_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

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

### Bot Issues

**Problem:** Bot not responding
```bash
# Solution: Check bot token and restart
python src/scripts/run_bot.py
```

**Problem:** "/analyze not available"
```bash
# Solution: Ensure LLM provider is configured
# Check .env has ANTHROPIC_API_KEY (or OpenAI/Gemini key)
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

**Current Version:** 1.0.0 (MVP Complete)

**Features:**
- ✅ Automated daily analysis (US1)
- ✅ Subscription management (US2)
- ✅ Historical access (US3)
- ✅ On-demand analysis
- ✅ 229 passing tests

**Roadmap:**
- 🔄 Enhanced logging and monitoring
- 🔄 Rate limiting with exponential backoff
- 🔄 CI workflow for automated testing
- 🔄 Additional bot commands (/stats, /about)
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
