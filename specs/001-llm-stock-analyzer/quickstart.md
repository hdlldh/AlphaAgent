# Quickstart Guide: AI-Powered Stock Analysis

**Feature**: 001-llm-stock-analyzer
**Date**: 2026-01-30

## Overview

This guide helps developers get the stock analyzer system running locally for development and testing. The system analyzes stocks daily using AI and delivers insights via Telegram.

---

## Prerequisites

- **Python**: 3.11 or higher
- **uv**: Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Git**: For cloning repository
- **Telegram Account**: To create test bot
- **API Keys**: Anthropic API key for LLM (Alpha Vantage optional)

---

## Quick Setup (5 minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd AlphaAgent
```

### 2. Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 3. Get API Keys

**LLM Provider API Key** (choose one):

**Option A: Anthropic Claude** (Recommended):
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Create API key
3. Copy key for next step
4. Cost: ~$18-27/month for 100 stocks

**Option B: OpenAI**:
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Create API key
3. Copy key for next step
4. Cost: ~$10-50/month depending on model

**Option C: Google Gemini**:
1. Get API key at [aistudio.google.com](https://aistudio.google.com)
2. Copy key for next step
3. Cost: ~$6-15/month depending on model

**Telegram Bot Token** (required):
1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow prompts
3. Copy bot token

**Alpha Vantage API Key** (optional):
1. Sign up at [alphavantage.co](https://www.alphavantage.co/support/#api-key)
2. Get free API key (25 calls/day)

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your API keys
nano .env
```

```bash
# .env file contents

# LLM Provider Configuration (choose one)
# Option A: Anthropic Claude (Recommended)
STOCK_ANALYZER_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your-anthropic-key...
STOCK_ANALYZER_LLM_MODEL=claude-sonnet-4-5

# Option B: OpenAI (uncomment to use)
# STOCK_ANALYZER_LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...your-openai-key...
# STOCK_ANALYZER_LLM_MODEL=gpt-4o

# Option C: Google Gemini (uncomment to use)
# STOCK_ANALYZER_LLM_PROVIDER=gemini
# GEMINI_API_KEY=...your-gemini-key...
# STOCK_ANALYZER_LLM_MODEL=gemini-2.5-pro

# Required: Telegram Bot
STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...your-bot-token...

# Optional: Stock Data API
STOCK_ANALYZER_STOCK_API_KEY=...optional-alpha-vantage-key...

# Optional configuration
STOCK_ANALYZER_DB_PATH=./data/stock_analyzer.db
STOCK_ANALYZER_LOG_LEVEL=INFO
```

### 5. Initialize Database

```bash
# Create data directory
mkdir -p data

# Initialize database schema
stock-analyzer init-db
```

### 6. Test Installation

```bash
# Run tests
pytest

# Test CLI
stock-analyzer validate AAPL
stock-analyzer analyze AAPL --dry-run

# Test bot (in separate terminal)
python -m stock_analyzer.bot
```

---

## Development Workflow

### Running Locally

**Start Telegram Bot** (terminal 1):
```bash
python -m stock_analyzer.bot
```

**Run Analysis Job** (terminal 2):
```bash
# Dry run to test
stock-analyzer run-daily-job --dry-run

# Real run
stock-analyzer run-daily-job
```

**Use CLI for Testing**:
```bash
# Subscribe test user
stock-analyzer subscribe YOUR_TELEGRAM_ID AAPL

# Analyze stock
stock-analyzer analyze AAPL

# View insights
stock-analyzer history AAPL
```

### Project Structure

```
AlphaAgent/
├── src/
│   └── stock_analyzer/
│       ├── __init__.py
│       ├── cli.py              # CLI interface
│       ├── models.py           # Data models
│       ├── fetcher.py          # Stock data fetching
│       ├── analyzer.py         # LLM analysis
│       ├── deliverer.py        # Delivery manager
│       ├── storage.py          # Database operations
│       └── bot.py              # Telegram bot
├── tests/
│   ├── contract/               # Contract tests
│   ├── integration/            # Integration tests
│   └── unit/                   # Unit tests
├── data/
│   └── stock_analyzer.db       # SQLite database
├── specs/
│   └── 001-llm-stock-analyzer/ # Feature documentation
├── pyproject.toml              # Project configuration
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_analyzer.py

# Run with coverage
pytest --cov=stock_analyzer --cov-report=html

# Run only contract tests
pytest tests/contract/

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Common Tasks

### Add a Test User Subscription

```bash
# Get your Telegram user ID
# Message your bot with /start, check logs for user_id

# Subscribe via CLI
stock-analyzer subscribe YOUR_USER_ID AAPL
stock-analyzer subscribe YOUR_USER_ID TSLA
stock-analyzer subscribe YOUR_USER_ID MSFT

# Verify
stock-analyzer list-subscriptions YOUR_USER_ID
```

### Analyze Stocks Manually

```bash
# Single stock
stock-analyzer analyze AAPL --json

# Multiple stocks
echo -e "AAPL\nTSLA\nMSFT" | stock-analyzer analyze-batch --stdin

# From file
cat stocks.txt | stock-analyzer analyze-batch --stdin --parallel 3
```

### Query Historical Data

```bash
# Last 7 days
stock-analyzer history AAPL

# Last 30 days
stock-analyzer history AAPL --start $(date -d '30 days ago' +%Y-%m-%d)

# Specific date range
stock-analyzer history AAPL --start 2026-01-01 --end 2026-01-30 --json
```

### Trigger Delivery Manually

```bash
# Deliver today's insights
stock-analyzer deliver

# Deliver specific stock
stock-analyzer deliver AAPL --user YOUR_USER_ID

# Dry run
stock-analyzer deliver --dry-run
```

---

## Testing Telegram Bot

### Local Testing

1. **Start bot**:
   ```bash
   python -m stock_analyzer.bot
   ```

2. **Open Telegram** and find your bot by username

3. **Test commands**:
   ```
   /start
   /subscribe AAPL
   /analyze TSLA
   /list
   /history AAPL
   /unsubscribe AAPL
   ```

4. **Check logs** in terminal for debugging

### Test with Mock Data

```python
# tests/test_bot_integration.py
from stock_analyzer.testing import MockBot, MockStorage

async def test_subscribe_command():
    bot = MockBot()
    storage = MockStorage()

    # Simulate /subscribe AAPL
    update = bot.create_message("/subscribe AAPL", user_id="123")
    await bot.process_update(update)

    # Verify response
    assert "✅ Subscribed to AAPL" in bot.last_message

    # Verify storage
    subs = storage.get_subscriptions("123")
    assert len(subs) == 1
    assert subs[0].stock_symbol == "AAPL"
```

---

## Configuration

### Config File

Create `~/.stock-analyzer/config.toml`:

```toml
[api]
# Primary LLM provider (choose: "anthropic", "openai", or "gemini")
llm_provider = "anthropic"
llm_model = "claude-sonnet-4-5"

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

[storage]
db_path = "./data/stock_analyzer.db"
retention_days = 365

[telegram]
parse_mode = "Markdown"
disable_notification = false

[logging]
level = "INFO"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Provider-Specific Setup Examples

**Using Claude** (Recommended):
```bash
export STOCK_ANALYZER_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export STOCK_ANALYZER_LLM_MODEL=claude-sonnet-4-5
```

**Using OpenAI**:
```bash
export STOCK_ANALYZER_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export STOCK_ANALYZER_LLM_MODEL=gpt-4o
```

**Using Gemini** (Budget Option):
```bash
export STOCK_ANALYZER_LLM_PROVIDER=gemini
export GEMINI_API_KEY=...
export STOCK_ANALYZER_LLM_MODEL=gemini-2.5-flash
```

### Environment Variables

```bash
# Required
STOCK_ANALYZER_LLM_API_KEY
STOCK_ANALYZER_TELEGRAM_TOKEN

# Optional
STOCK_ANALYZER_STOCK_API_KEY
STOCK_ANALYZER_DB_PATH
STOCK_ANALYZER_LOG_LEVEL
STOCK_ANALYZER_CONFIG_FILE
STOCK_ANALYZER_USER_LIMIT
STOCK_ANALYZER_SYSTEM_LIMIT
```

---

## Troubleshooting

### Database Issues

**Error**: `sqlite3.OperationalError: no such table`
```bash
# Reinitialize database
rm data/stock_analyzer.db
stock-analyzer init-db
```

**Error**: `database is locked`
```bash
# Close all connections, check for processes
lsof data/stock_analyzer.db
kill <PID>
```

### API Issues

**Error**: `Invalid API key`
```bash
# Check environment variables
echo $STOCK_ANALYZER_LLM_API_KEY
echo $STOCK_ANALYZER_TELEGRAM_TOKEN

# Reload .env
source .env
```

**Error**: `Rate limit exceeded`
```bash
# Wait or use different API key
# Check usage: console.anthropic.com
# Reduce parallel analysis tasks
```

### Telegram Bot Issues

**Bot not responding**:
1. Check bot is running: `ps aux | grep bot.py`
2. Check logs for errors
3. Verify bot token: `curl https://api.telegram.org/bot<TOKEN>/getMe`
4. Check network connectivity

**Commands not working**:
1. Restart bot
2. Clear Telegram cache
3. Check bot has privacy mode disabled (BotFather → /setprivacy)

---

## Development Tips

### Enable Debug Logging

```bash
export STOCK_ANALYZER_LOG_LEVEL=DEBUG
python -m stock_analyzer.bot
```

### Use Mock Mode

```python
# In your code
from stock_analyzer import Config

config = Config.from_env()
config.mock_mode = True  # Use mock APIs

analyzer = Analyzer.from_config(config)
```

### Reset Database

```bash
# Backup first
cp data/stock_analyzer.db data/stock_analyzer.db.backup

# Reset
rm data/stock_analyzer.db
stock-analyzer init-db

# Restore if needed
cp data/stock_analyzer.db.backup data/stock_analyzer.db
```

### Profile Performance

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
await analyzer.analyze_stock("AAPL")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)
```

---

## Next Steps

1. **Read Contracts**: Review `contracts/` directory for API details
2. **Check Tests**: Look at `tests/` for examples
3. **Review Data Model**: See `data-model.md` for database schema
4. **Read Research**: Check `research.md` for technology decisions
5. **Implement Features**: Follow TDD workflow in `tasks.md` (when generated)

---

## Getting Help

- **Documentation**: Check `specs/001-llm-stock-analyzer/` directory
- **Issues**: Create GitHub issue with error details
- **Questions**: Open GitHub discussion
- **Logs**: Check `~/.stock-analyzer/logs/` directory

---

## Production Deployment

See GitHub Actions workflow in `.github/workflows/daily-analysis.yml` for production deployment configuration.

**Key Steps**:
1. Set up secrets in GitHub repository settings
2. Configure schedule (default: 10 PM UTC, Mon-Fri)
3. Enable workflow
4. Monitor workflow runs in Actions tab

---

## License

[Add your license here]

## Contributors

[Add contributors here]
