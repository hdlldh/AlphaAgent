# Migration Guide: Multi-User to Personal Use (v1.x → v2.0)

This guide helps you migrate from the multi-user version (v1.x) to the personal use edition (v2.0) of AlphaAgent.

## Overview

Version 2.0 simplifies AlphaAgent by removing multi-user support and subscription management. Instead of managing multiple users through Telegram bot commands, you now configure your personal stock list directly via environment variables and receive insights in your personal Telegram channel.

## What Changed

### Removed Features

- **User Management**: No user registration, authentication, or user accounts
- **Subscription System**: No per-user stock subscriptions or subscription limits
- **Telegram Bot Commands**: Removed `/subscribe`, `/unsubscribe`, `/list` commands
- **Bot Interface**: Removed interactive Telegram bot (bot.py, run_bot.py)
- **CLI Commands**: Removed `subscribe`, `unsubscribe`, `list-subscriptions` commands

### New Features

- **Environment-Based Configuration**: Stock list configured via `STOCK_ANALYZER_STOCK_LIST`
- **Direct Channel Delivery**: Insights posted directly to your Telegram channel
- **Simplified Storage**: Removed users and subscriptions tables from database

### Database Changes

**Tables Removed:**
- `users` - User registration and authentication
- `subscriptions` - Per-user stock subscriptions

**Tables Modified:**
- `insights` - Removed `analysis_id` foreign key (simplified schema)
- `delivery_logs` - Changed `user_id` to `channel_id` (channel-based delivery)

**Tables Unchanged:**
- `stock_analyses` - No changes
- `analysis_jobs` - No changes

## Breaking Changes

⚠️ **Important**: This is a breaking change that requires reconfiguration.

1. **Configuration Change**: Environment variables required:
   - New: `STOCK_ANALYZER_STOCK_LIST` (comma-separated stock symbols)
   - New: `STOCK_ANALYZER_TELEGRAM_CHANNEL` (channel username or ID)
   - Removed: `STOCK_ANALYZER_USER_LIMIT`
   - Removed: `STOCK_ANALYZER_SYSTEM_LIMIT`

2. **Database Schema**: Automatic migration drops `users` and `subscriptions` tables
   - **All user accounts will be lost**
   - **All subscription data will be lost**
   - Historical analyses and insights are preserved

3. **Telegram Bot**: Bot no longer accepts commands
   - Bot only posts to your channel
   - No interactive chat functionality

4. **CLI Interface**: Subscription commands removed
   - Removed: `python -m stock_analyzer.cli subscribe`
   - Removed: `python -m stock_analyzer.cli unsubscribe`
   - Removed: `python -m stock_analyzer.cli list-subscriptions`

## Migration Steps

### 1. Backup Your Data

```bash
# Backup existing database (IMPORTANT!)
cp data/stock_analyzer.db data/stock_analyzer.db.backup

# Backup .env file
cp .env .env.backup
```

### 2. Export Your Subscription Data (Optional)

If you want to preserve a record of your subscriptions:

```bash
# List all subscriptions before migration
python -m stock_analyzer.cli list-subscriptions > subscriptions_export.txt

# Or use SQLite directly
sqlite3 data/stock_analyzer.db "SELECT * FROM subscriptions" > subscriptions.csv
```

### 3. Update Code

```bash
# Pull latest code
git pull origin master

# Or checkout specific version
git checkout v2.0.0

# Reinstall dependencies
uv pip install -e .
```

### 4. Create Telegram Channel

If you don't already have a personal Telegram channel:

1. Open Telegram → Settings → New Channel
2. Choose a name (e.g., "My Stock Insights")
3. Make it private or public
4. Copy channel username (e.g., `@mystockinsights`) or numeric ID

### 5. Update Telegram Bot Permissions

Your existing bot needs admin access to post to your channel:

1. Open your Telegram channel
2. Add your bot as administrator
3. Grant "Post Messages" permission

### 6. Update Configuration

Edit your `.env` file:

```bash
# REQUIRED: Add personal stock list (comma-separated)
# Use your previous subscription list from step 2
STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL,TSLA,NVDA

# REQUIRED: Add Telegram channel ID
STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockinsights

# REMOVE: These are no longer used
# STOCK_ANALYZER_USER_LIMIT=10
# STOCK_ANALYZER_SYSTEM_LIMIT=100
```

### 7. Run Database Migration

The migration happens automatically when you initialize the database:

```bash
# This will DROP users and subscriptions tables
python -m stock_analyzer.cli init-db
```

⚠️ **Warning**: This step is destructive. Make sure you have a backup (step 1).

### 8. Verify Migration

```bash
# Test analysis for one stock
python -m stock_analyzer.cli analyze AAPL

# Test daily job in dry-run mode
python -m stock_analyzer.cli run-daily-job --dry-run

# Run actual daily job (posts to your channel)
python -m stock_analyzer.cli run-daily-job
```

Check your Telegram channel to verify insights are delivered correctly.

### 9. Update GitHub Actions (If Used)

If you're using GitHub Actions for automated analysis:

```yaml
# Update .github/workflows/daily-analysis.yml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  STOCK_ANALYZER_TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
  # ADD these new secrets:
  STOCK_ANALYZER_STOCK_LIST: ${{ secrets.STOCK_LIST }}
  STOCK_ANALYZER_TELEGRAM_CHANNEL: ${{ secrets.TELEGRAM_CHANNEL }}
```

Add new repository secrets:
- `STOCK_LIST` - Your comma-separated stock symbols
- `TELEGRAM_CHANNEL` - Your channel username

### 10. Remove Bot Deployment (If Used)

If you were running the bot on a server or via GitHub Actions:

```bash
# Stop bot service
sudo systemctl stop stock-analyzer-bot

# Disable bot service
sudo systemctl disable stock-analyzer-bot

# Remove systemd service file
sudo rm /etc/systemd/system/stock-analyzer-bot.service
sudo systemctl daemon-reload
```

## Configuration Mapping

### Old Configuration (v1.x)

```bash
# Multi-user bot configuration
STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...
STOCK_ANALYZER_USER_LIMIT=10
STOCK_ANALYZER_SYSTEM_LIMIT=100
```

Users subscribed via bot commands:
```
/subscribe AAPL
/subscribe MSFT
/subscribe GOOGL
```

### New Configuration (v2.0)

```bash
# Personal use configuration
STOCK_ANALYZER_TELEGRAM_TOKEN=123456:ABC-DEF...  # Same bot token
STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL       # Your subscriptions as env var
STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockinsights # Your channel
```

## Data Preservation

### What's Preserved

✅ **Historical Analyses**: All stock analyses in `stock_analyses` table
✅ **Historical Insights**: All AI-generated insights in `insights` table
✅ **Job History**: All analysis job records in `analysis_jobs` table

You can still query historical data:
```bash
python -m stock_analyzer.cli history AAPL
python -m stock_analyzer.cli history MSFT --start 2026-01-01
```

### What's Lost

❌ **User Accounts**: All user registration data
❌ **Subscriptions**: All per-user stock subscriptions
❌ **Delivery History**: Old delivery logs with user_id references

## Testing After Migration

Run these tests to verify everything works:

```bash
# 1. Test CLI analysis
python -m stock_analyzer.cli analyze AAPL

# 2. Test historical queries
python -m stock_analyzer.cli history AAPL --limit 5

# 3. Test daily job (dry run)
python -m stock_analyzer.cli run-daily-job --dry-run

# 4. Test actual delivery to channel
python -m stock_analyzer.cli run-daily-job

# 5. Run full test suite
uv run pytest

# 6. Check Telegram channel for new insights
```

## Rollback Instructions

If you need to rollback to v1.x:

```bash
# 1. Stop any running processes
# 2. Restore database backup
cp data/stock_analyzer.db.backup data/stock_analyzer.db

# 3. Checkout previous version
git checkout v1.0.0

# 4. Restore .env file
cp .env.backup .env

# 5. Reinstall dependencies
uv pip install -e .

# 6. Restart bot
python src/scripts/run_bot.py
```

## Troubleshooting

### Problem: Database migration fails

```bash
# Solution: Check database is not locked
rm data/stock_analyzer.db-wal data/stock_analyzer.db-shm

# Re-run migration
python -m stock_analyzer.cli init-db
```

### Problem: Bot can't post to channel

```bash
# Solution 1: Verify bot is channel admin
# Check in Telegram: Channel → Administrators → Your bot should be listed

# Solution 2: Verify channel ID is correct
# Channel username must start with @ or use numeric ID
STOCK_ANALYZER_TELEGRAM_CHANNEL=@mystockinsights  # Correct
STOCK_ANALYZER_TELEGRAM_CHANNEL=mystockinsights   # Wrong (missing @)
```

### Problem: Stock list not recognized

```bash
# Solution: Check environment variable format
# Correct: Comma-separated, no spaces
STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL

# Also correct: With spaces (will be trimmed)
STOCK_ANALYZER_STOCK_LIST=AAPL, MSFT, GOOGL

# Wrong: Missing symbols
STOCK_ANALYZER_STOCK_LIST=
```

### Problem: Historical data missing after migration

```bash
# Solution: Restore from backup
cp data/stock_analyzer.db.backup data/stock_analyzer.db

# Historical data (analyses, insights) should NOT be lost during migration
# Only users and subscriptions tables are dropped
```

## Frequently Asked Questions

### Q: Can I keep using the multi-user version?

A: Yes, you can stay on v1.x. However, v2.0 is simpler and designed for personal use, which is the primary use case for most users.

### Q: Can I migrate back from v2.0 to v1.x?

A: Yes, but you'll need to:
1. Restore database backup (user/subscription data will be lost)
2. Checkout v1.x code
3. Reconfigure .env for multi-user mode

### Q: Will my historical insights be preserved?

A: Yes! All historical analyses and insights are preserved during migration.

### Q: Can I still use multiple stock symbols?

A: Yes! Add them to `STOCK_ANALYZER_STOCK_LIST` as comma-separated values:
```bash
STOCK_ANALYZER_STOCK_LIST=AAPL,MSFT,GOOGL,TSLA,NVDA,AMZN,META
```

### Q: What happens to my old delivery logs?

A: Old delivery logs remain in the database but may have `user_id` references that no longer exist. New deliveries use `channel_id` instead.

## Support

If you encounter issues during migration:

1. Check the [Troubleshooting section](#troubleshooting) above
2. Review the [README.md](../README.md) for configuration help
3. Create a GitHub issue with:
   - Migration step where you encountered the issue
   - Error messages
   - Your configuration (remove sensitive tokens)
   - Database backup status

## Summary

✅ **Simpler**: No user management, no subscription complexity
✅ **Faster**: Direct channel posting, no bot command processing
✅ **Focused**: Personal use case optimized
✅ **Maintained**: Historical data preserved

Version 2.0 makes AlphaAgent easier to use for its primary use case: personal stock monitoring. If you were the only user of your v1.x instance, this migration will simplify your setup significantly.
