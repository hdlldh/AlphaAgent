# Quickstart Guide: Personal Stock Monitor

**Feature**: 002-personal-telegram-stocks
**Date**: 2026-02-28
**Target**: Personal use (single user)

## Overview

Set up your personal stock monitoring system that analyzes stocks daily and posts insights to your Telegram channel.

**What You'll Get**:
- Automated daily analysis of your chosen stocks (Mon-Fri after market close)
- AI-powered insights posted to your Telegram channel
- Historical analysis query via CLI
- No user management overhead

---

## Prerequisites

### Required
- **Python 3.11+** installed
- **Telegram account** for creating channel
- **LLM API key**: Choose one
  - [Anthropic Claude](https://console.anthropic.com/) (recommended)
  - [OpenAI](https://platform.openai.com/)
  - [Google Gemini](https://ai.google.dev/)

### Optional
- **GitHub account** for automated workflows (optional but recommended)
- **Alpha Vantage API key** for fallback stock data (free tier available)

---

## Step 1: Create Telegram Channel

### 1.1 Create Channel

1. Open Telegram app
2. Menu (☰) → **New Channel**
3. Set channel name: e.g., "My Stock Insights"
4. Set description (optional)
5. Choose **Public** or **Private**:
   - **Public**: Anyone can find and join (URL: t.me/channelname)
   - **Private**: Only invited members can access

### 1.2 Get Channel ID

**For Public Channels**:
- Your channel ID is: `@channelname`
- Example: `@mystockinsights`

**For Private Channels**:
1. Add bot `@userinfobot` to your channel
2. Bot will send channel ID (e.g., `-1001234567890`)
3. Remove `@userinfobot` after getting ID

### 1.3 Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to set bot name and username
4. **Copy the bot token** (looks like: `123456:ABC-DEF...`)

### 1.4 Add Bot to Channel

1. Open channel settings → **Administrators**
2. **Add Administrator** → Search for your bot
3. Grant permission: **Post Messages** ✓
4. Save

---

## Step 2: Clone and Install

### 2.1 Clone Repository

```bash
git clone <repository-url>
cd AlphaAgent
```

### 2.2 Install Dependencies

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -e .
```

---

## Step 3: Configure Environment

### 3.1 Create .env File

```bash
cp .env.example .env
```

### 3.2 Edit .env

Open `.env` in your editor and configure:

```bash
# === REQUIRED CONFIGURATION ===

# Stock List (comma-separated, 5-50 stocks recommended)
STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL,TSLA,NVDA,AMZN,META

# Telegram Configuration
STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...  # From BotFather
STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockinsights  # Your channel ID

# LLM Provider (choose one: anthropic, openai, gemini)
STOCK_ANALYZER_LLM_PROVIDER=anthropic

# LLM API Key (choose one)
ANTHROPIC_API_KEY=sk-ant-...      # If using Claude
# OPENAI_API_KEY=sk-...           # If using OpenAI
# GEMINI_API_KEY=...              # If using Gemini

# === OPTIONAL CONFIGURATION ===

# Alpha Vantage (fallback stock data provider)
# STOCK_ANALYZER_STOCK_API_KEY=...

# Database Path
# STOCK_ANALYZER_DB_PATH=./data/stock_analyzer.db

# Logging Level
# STOCK_ANALYZER_LOG_LEVEL=INFO
```

### 3.3 Validate Configuration

```bash
# Test stock symbol validation
python -m stock_analyzer.cli validate AAPL
# Expected: ✓ AAPL is a valid stock symbol

# Test configuration loading
python -c "from stock_analyzer.config import Config; c = Config.from_env(); c.validate(); print('✓ Configuration valid')"
```

---

## Step 4: Initialize Database

```bash
python -m stock_analyzer.cli init-db
```

**Expected Output**:
```text
Database initialized successfully at: ./data/stock_analyzer.db
```

**What This Does**:
- Creates SQLite database file
- Creates tables: `stock_analyses`, `insights`, `delivery_logs`, `analysis_jobs`
- Drops old multi-user tables if migrating from previous version

---

## Step 5: Test Analysis

### 5.1 Analyze Single Stock

```bash
python -m stock_analyzer.cli analyze AAPL
```

**Expected Output**:
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

### 5.2 Test Telegram Channel Posting

**Manual Test** (using Python):
```python
import asyncio
from telegram import Bot

async def test_channel():
    bot = Bot(token="YOUR_TELEGRAM_TOKEN")
    await bot.send_message(
        chat_id="@yourchannelname",
        text="🧪 Test message from AlphaAgent"
    )
    print("✓ Message posted successfully")

asyncio.run(test_channel())
```

**If Successful**: Check your Telegram channel for the test message.

**If Failed**: Check error message:
- `Chat not found`: Bot not added to channel, or channel ID incorrect
- `Forbidden`: Bot lacks "Post Messages" permission

---

## Step 6: Run Daily Analysis Job

### 6.1 Dry Run (Test Configuration)

```bash
python -m stock_analyzer.cli run-daily-job --dry-run
```

**Expected Output**:
```text
DRY RUN MODE - No analysis will be performed

Configuration:
- Stock list: AAPL, MSFT, GOOGL, TSLA, NVDA, AMZN, META
- Telegram channel: @mystockinsights
- Database: ./data/stock_analyzer.db

Would analyze 7 stocks:
  1. AAPL
  2. MSFT
  3. GOOGL
  4. TSLA
  5. NVDA
  6. AMZN
  7. META
```

### 6.2 Run Full Analysis

```bash
python -m stock_analyzer.cli run-daily-job
```

**Expected Output**:
```text
Starting daily analysis job...
Stock list from STOCK_ANALYZER_STOCK_LIST: AAPL, MSFT, GOOGL, ...
Analyzing 7 stocks...

[1/7] AAPL: ✓ Success (11.2s)
[2/7] MSFT: ✓ Success (10.5s)
[3/7] GOOGL: ✓ Success (12.8s)
...

Analysis complete: 7 success, 0 failed, duration=82.3s

Delivering insights to Telegram channel: @mystockinsights
[1/7] AAPL insight delivered
[2/7] MSFT insight delivered
...

Delivery complete: 7 total, 7 success, 0 failed

Daily analysis job completed successfully
```

**Check Your Channel**: You should see 7 stock analysis posts in your Telegram channel.

---

## Step 7: Set Up Automation (GitHub Actions)

### 7.1 Push to GitHub

```bash
git add .
git commit -m "Configure personal stock monitor"
git push origin main
```

### 7.2 Configure GitHub Secrets

1. Go to your repository on GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `ANTHROPIC_API_KEY` | Your Claude API key | `sk-ant-...` |
| `TELEGRAM_TOKEN` | Bot token from BotFather | `123456:ABC-DEF...` |
| `TELEGRAM_CHANNEL` | Your channel ID | `@mystockinsights` |
| `STOCK_LIST` | Comma-separated stocks | `AAPL,MSFT,GOOGL,TSLA,NVDA` |
| `ALPHA_VANTAGE_KEY` | (Optional) Fallback API key | `YOUR_KEY` |

### 7.3 Update Workflow File

Edit `.github/workflows/daily-analysis.yml`:

```yaml
name: Daily Stock Analysis

on:
  schedule:
    # Run Monday-Friday at 10 PM UTC (after US market close)
    - cron: '0 22 * * 1-5'
  workflow_dispatch:  # Manual trigger

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv pip install -e .

      - name: Run daily analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          STOCK_ANALYZER_TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          STOCK_ANALYZER_TELEGRAM_CHANNEL: ${{ secrets.TELEGRAM_CHANNEL }}
          STOCK_ANALYZER_STOCK_LIST: ${{ secrets.STOCK_LIST }}
          STOCK_ANALYZER_STOCK_API_KEY: ${{ secrets.ALPHA_VANTAGE_KEY }}
        run: python -m stock_analyzer.cli run-daily-job

      - name: Commit database changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/stock_analyzer.db
          git commit -m "chore: update analysis database [skip ci]" || echo "No changes"
          git push
```

### 7.4 Enable Workflow

1. Go to **Actions** tab in GitHub
2. Enable workflows if prompted
3. Click **Daily Stock Analysis** workflow
4. Click **Run workflow** to test (manual trigger)

### 7.5 Verify Automation

- Check **Actions** tab for workflow execution logs
- Check your Telegram channel for posted insights
- Database should be updated in repository (see commit history)

---

## Step 8: Query Historical Data

### 8.1 View All History for a Stock

```bash
python -m stock_analyzer.cli history AAPL
```

### 8.2 Query with Date Range

```bash
python -m stock_analyzer.cli history AAPL --start 2026-02-01 --end 2026-02-28
```

### 8.3 JSON Output

```bash
python -m stock_analyzer.cli history AAPL --json
```

---

## Usage Tips

### Stock List Management

**Add/Remove Stocks**:
1. Edit `.env` file: `STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,NEW_STOCK`
2. Or update GitHub secret: `STOCK_LIST`

**How Many Stocks?**:
- **Recommended**: 5-20 stocks (2-4 minutes analysis time)
- **Maximum**: 50 stocks (~15 minutes analysis time)
- **Cost**: ~$0.50-1.50 per analysis run (50 stocks with Claude)

### Cost Optimization

**Use Claude with Prompt Caching** (90% cost reduction):
```bash
STOCK_ANALYZER_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Monthly Cost Estimates** (20 trading days/month):
- 10 stocks: $10-15/month with Claude (with caching), $30-50/month with OpenAI
- 50 stocks: $30-50/month with Claude (with caching), $100-150/month with OpenAI

### Scheduling

**GitHub Actions Schedule** (cron syntax):
```yaml
# Monday-Friday at 10 PM UTC (after US market close)
- cron: '0 22 * * 1-5'

# Daily at 5 AM UTC (before market open)
- cron: '0 5 * * *'

# Weekdays at 9:30 PM UTC (30 min after US market close)
- cron: '30 21 * * 1-5'
```

### Troubleshooting

**Problem**: Stock list is empty
```text
Error: STOCK_ANALYZER_STOCK_LIST is required. Set it to a comma-separated list...
```
**Solution**: Set `STOCK_ANALYZER_STOCK_LIST` environment variable

---

**Problem**: Channel not found
```text
Error: Chat not found
```
**Solution**:
1. Verify bot is added to channel as admin
2. Check channel ID format (`@channelname` for public, `-1001234567890` for private)
3. Test with Python script (Step 5.2)

---

**Problem**: Bot lacks permission
```text
Error: Forbidden: bot is not a member of the channel
```
**Solution**:
1. Add bot to channel: Channel settings → Administrators → Add bot
2. Grant "Post Messages" permission

---

**Problem**: Analysis fails for some stocks
```text
[3/7] INVALID: ✗ Failed: Invalid symbol
```
**Solution**:
- This is expected behavior (invalid symbols are skipped)
- Remove invalid symbols from `STOCK_ANALYZER_STOCK_LIST`
- Use `validate` command to test: `python -m stock_analyzer.cli validate SYMBOL`

---

**Problem**: Rate limited by LLM API
```text
Error: Rate limit exceeded
```
**Solution**:
- Reduce parallelism: Analysis uses `parallel=2` by default
- Spread out analysis: Run fewer stocks per day
- Upgrade API plan: Check provider's rate limits

---

**Problem**: Database locked
```text
Error: database is locked
```
**Solution**:
```bash
# Stop any running processes accessing database
# Remove lock files
rm data/stock_analyzer.db-wal data/stock_analyzer.db-shm

# Reinitialize if needed
python -m stock_analyzer.cli init-db
```

---

## Advanced Configuration

### Custom Database Path

```bash
export STOCK_ANALYZER_DB_PATH=/custom/path/stock_analyzer.db
```

### Custom LLM Model

```bash
export STOCK_ANALYZER_LLM_MODEL=claude-opus-4
# or
export STOCK_ANALYZER_LLM_MODEL=gpt-4
```

### Debug Logging

```bash
export STOCK_ANALYZER_LOG_LEVEL=DEBUG
python -m stock_analyzer.cli run-daily-job
```

---

## Next Steps

✅ **You're Done!** Your personal stock monitor is now set up and running.

**What Happens Next**:
- GitHub Actions runs daily analysis (Mon-Fri at 10 PM UTC)
- Insights posted to your Telegram channel automatically
- Historical data stored in SQLite database
- Query historical insights anytime via CLI

**Customize**:
- Change stock list: Update `STOCK_ANALYZER_STOCK_LIST`
- Change schedule: Edit `.github/workflows/daily-analysis.yml`
- Change LLM provider: Set `STOCK_ANALYZER_LLM_PROVIDER` and API key

**Get Support**:
- Check logs in GitHub Actions → Workflow runs
- Check database: `sqlite3 data/stock_analyzer.db`
- Check tests: `uv run pytest`

---

## Appendix: Migration from Multi-User Version

If upgrading from the multi-user version:

### 1. Backup Database
```bash
cp data/stock_analyzer.db data/stock_analyzer.db.backup
```

### 2. Update Code
```bash
git pull origin main
git checkout 002-personal-telegram-stocks
```

### 3. Reconfigure
```bash
# Remove old user-specific config
unset STOCK_ANALYZER_USER_LIMIT
unset STOCK_ANALYZER_SYSTEM_LIMIT

# Add new personal config
export STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL
export STOCK_ANALYZER_TELEGRAM_CHANNEL=@mychannel
```

### 4. Migrate Database
```bash
python -m stock_analyzer.cli init-db
```

This will:
- Drop `users` and `subscriptions` tables
- Keep `insights` and `analyses` tables (historical data preserved)
- Update schema to remove user foreign keys

### 5. Verify
```bash
# Check historical data
python -m stock_analyzer.cli history AAPL

# Test new workflow
python -m stock_analyzer.cli run-daily-job --dry-run
```

**Historical Data**: All existing insights and analyses are preserved and queryable without user context.

---

**Status**: ✅ Quickstart Guide Complete
