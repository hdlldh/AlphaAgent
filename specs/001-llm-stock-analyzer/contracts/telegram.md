# Telegram Bot Interface Contract

**Feature**: AI-Powered Stock Analysis
**Date**: 2026-01-30
**Version**: 1.0.0

## Overview

The Telegram bot provides conversational access to stock analysis functionality. Users interact via commands and inline buttons to subscribe to stocks, view insights, and query historical data.

---

## Bot Information

- **Bot Username**: `@stock_analyzer_bot` (placeholder - actual username TBD)
- **Bot Description**: "Daily AI-powered stock analysis delivered to your Telegram"
- **Framework**: python-telegram-bot v22.x
- **Commands**: 8 user commands + 2 admin commands

---

## User Commands

### /start

Initialize conversation with the bot.

**Usage**: `/start`

**Response**:
```
Welcome to Stock Analyzer! 📈

I provide daily AI-powered analysis for stocks you subscribe to.

Get started:
• /subscribe AAPL - Subscribe to a stock
• /list - View your subscriptions
• /help - See all commands

Limits: 10 stocks per user
```

**Features**:
- Creates User record if first interaction
- Updates last_active timestamp
- Shows welcome message with quick start

---

### /help

Show all available commands and usage instructions.

**Usage**: `/help`

**Response**:
```
Stock Analyzer Commands 📚

Subscriptions:
/subscribe <SYMBOL> - Subscribe to stock analysis
/unsubscribe <SYMBOL> - Unsubscribe from stock
/list - View your active subscriptions

Analysis:
/analyze <SYMBOL> - Get immediate analysis
/history <SYMBOL> - View past insights

Information:
/help - Show this message
/stats - View your statistics
/about - About this bot

Examples:
/subscribe AAPL
/analyze TSLA
/history MSFT 7d

Questions? Contact @admin_username
```

---

### /subscribe

Subscribe to daily analysis for a stock.

**Usage**: `/subscribe <SYMBOL>`

**Examples**:
- `/subscribe AAPL`
- `/subscribe TSLA`

**Response (Success)**:
```
✅ Subscribed to AAPL

You'll receive daily analysis after market close (10 PM UTC).

Your subscriptions: 3/10
Manage: /list
```

**Response (At Limit)**:
```
❌ Subscription limit reached (10/10)

Unsubscribe from a stock to add a new one:
/unsubscribe <SYMBOL>

View subscriptions: /list
```

**Response (Already Subscribed)**:
```
ℹ️ Already subscribed to AAPL

Subscribed on: Jan 28, 2026
View insights: /history AAPL

Manage subscriptions: /list
```

**Response (Invalid Symbol)**:
```
❌ Invalid stock symbol: INVALID

The symbol was not found or is not supported.

Try a valid symbol like:
• AAPL (Apple)
• TSLA (Tesla)
• MSFT (Microsoft)

Validate first: /validate INVALID
```

**Response (System at Capacity)**:
```
❌ System capacity reached

The system is currently at maximum capacity (100 stocks).
Please try again later or contact support.

Your subscriptions are not affected: /list
```

**Inline Keyboard**: After successful subscription:
```
[View Latest Analysis] [History] [Unsubscribe]
```

---

### /unsubscribe

Unsubscribe from daily analysis for a stock.

**Usage**: `/unsubscribe <SYMBOL>`

**Response (Success)**:
```
✅ Unsubscribed from AAPL

You will no longer receive daily analysis for this stock.

Your subscriptions: 2/10
Resubscribe: /subscribe AAPL
View all: /list
```

**Response (Not Subscribed)**:
```
ℹ️ Not subscribed to AAPL

Subscribe now: /subscribe AAPL
View your subscriptions: /list
```

---

### /list

View all active subscriptions.

**Usage**: `/list`

**Response (With Subscriptions)**:
```
Your Subscriptions 📋

1. AAPL - Apple Inc.
   Subscribed: Jan 28, 2026
   Last analysis: Today, 10:05 PM
   [View] [History] [Unsubscribe]

2. TSLA - Tesla, Inc.
   Subscribed: Jan 29, 2026
   Last analysis: Today, 10:12 PM
   [View] [History] [Unsubscribe]

3. MSFT - Microsoft Corp.
   Subscribed: Jan 30, 2026
   Last analysis: Today, 10:18 PM
   [View] [History] [Unsubscribe]

Total: 3/10

[Add Stock] [View All History]
```

**Response (No Subscriptions)**:
```
No Active Subscriptions 📭

You're not subscribed to any stocks yet.

Get started:
/subscribe AAPL - Subscribe to Apple
/subscribe TSLA - Subscribe to Tesla
/help - See all commands

You can subscribe to up to 10 stocks.
```

---

### /analyze

Get immediate AI analysis for a stock (doesn't require subscription).

**Usage**: `/analyze <SYMBOL>`

**Response**:
```
Analyzing AAPL... ⏳

Stock Analysis: Apple Inc. (AAPL)
Date: Jan 30, 2026
Price: $185.75 (+2.3%)

💡 Summary:
Apple shows strong upward momentum with increased volume, indicating positive investor sentiment.

📈 Trend Analysis:
The stock has gained 2.3% with volume 15% above average, suggesting sustained buying interest. Technical indicators show bullish divergence.

⚠️ Risk Factors:
• Overvaluation concerns at current P/E ratio
• Dependence on iPhone revenue
• Supply chain vulnerabilities

✨ Opportunities:
• Upcoming product launches in Q2
• Growing services revenue segment
• Market expansion in emerging economies

Confidence: High
Analysis time: 4.2s

[Subscribe] [View History] [Share]
```

**Notes**:
- Available for any valid symbol (not just subscribed)
- Generated on-demand (not cached)
- Counts toward API usage limits

---

### /history

View historical insights for a subscribed stock.

**Usage**:
- `/history <SYMBOL>` - Last 7 days
- `/history <SYMBOL> 30d` - Last 30 days
- `/history <SYMBOL> 2026-01-01` - Since specific date

**Response**:
```
History: AAPL 📊
Last 7 days

📅 Jan 30, 2026 - $185.75 (+2.3%)
Summary: Strong upward momentum...
[View Full Analysis]

📅 Jan 29, 2026 - $181.60 (-0.5%)
Summary: Consolidation phase...
[View Full Analysis]

📅 Jan 28, 2026 - $182.50 (+1.2%)
Summary: Positive earnings reaction...
[View Full Analysis]

Showing 3 of 250 insights
[Load More] [Export CSV]
```

**Response (Not Subscribed)**:
```
ℹ️ Not subscribed to AAPL

Subscribe to view full history:
/subscribe AAPL

Or get immediate analysis:
/analyze AAPL
```

---

### /stats

View personal usage statistics.

**Usage**: `/stats`

**Response**:
```
Your Statistics 📊

Account:
• Member since: Jan 28, 2026
• Active subscriptions: 3/10
• Total insights received: 45

This Month:
• Analyses delivered: 15
• Average per day: 3.0
• Most tracked: AAPL (10 analyses)

[View Detailed History] [Export Data]
```

---

### /about

Information about the bot.

**Usage**: `/about`

**Response**:
```
Stock Analyzer Bot 🤖

Version: 1.0.0
Daily AI-powered stock analysis

Features:
• Subscribe to up to 10 stocks
• Daily analysis after market close
• Historical insights (1 year)
• Immediate on-demand analysis

Technology:
• AI Model: Claude Sonnet 4.5
• Data: Yahoo Finance + Alpha Vantage
• Powered by Python + Telegram Bot API

Disclaimer:
This bot provides analysis for informational purposes only. Not financial advice. Consult a professional before making investment decisions.

Privacy: We store only your Telegram ID and stock subscriptions.

Contact: @admin_username
GitHub: github.com/user/stock-analyzer
```

---

## Admin Commands

### /admin_stats

System-wide statistics (admin only).

**Usage**: `/admin_stats`

**Response**:
```
System Statistics (Admin) 🔐

Users:
• Total: 15
• Active (7d): 12
• Avg subscriptions: 2.8

Subscriptions:
• Total: 42/100 (42%)
• Top stocks: AAPL(8), TSLA(6), MSFT(5)

Today's Job:
• Status: Completed
• Stocks analyzed: 42
• Success rate: 95.2%
• Duration: 9m 15s
• Deliveries: 120 (98.5% success)

[View Details] [Export Logs]
```

---

### /admin_broadcast

Send message to all users (admin only).

**Usage**: `/admin_broadcast <message>`

**Response**:
```
Broadcast sent to 15 users
Delivered: 14
Failed: 1

[View Report]
```

---

## Callback Queries (Inline Buttons)

### view_insight_{insight_id}

View full insight details.

**Action**: Display full analysis in new message

---

### history_{symbol}_{days}

View historical insights.

**Action**: Display paginated history

---

### subscribe_{symbol}

Subscribe to stock via button.

**Action**: Execute subscription, update message

---

### unsubscribe_{symbol}

Unsubscribe via button.

**Action**: Execute unsubscription with confirmation

**Confirmation**:
```
Unsubscribe from AAPL?

You'll stop receiving daily analysis.

[Confirm Unsubscribe] [Cancel]
```

---

## Scheduled Messages

### Daily Insight Delivery

Sent automatically after daily analysis job completes (~10 PM UTC).

**Format**:
```
📈 Daily Stock Insights - Jan 30, 2026

You have 3 new analyses:

1. AAPL - $185.75 (+2.3%) ✅
   Strong upward momentum...
   [View Full Analysis]

2. TSLA - $245.80 (-1.5%) ⚠️
   Consolidation after rally...
   [View Full Analysis]

3. MSFT - $395.20 (+0.8%) ✅
   Steady growth continues...
   [View Full Analysis]

[View All History] [Manage Subscriptions]
```

**Batching**: All insights for a user sent in single message to avoid spam

---

## Error Messages

### Invalid Command Format

```
❌ Invalid command format

Usage: /subscribe <SYMBOL>
Example: /subscribe AAPL

Need help? /help
```

### API Error

```
⚠️ Temporary service issue

We're experiencing technical difficulties.
Please try again in a few moments.

If the problem persists, contact @admin_username
```

### Rate Limit

```
⏳ Rate limit exceeded

Please wait a moment before trying again.

Tip: Use /subscribe instead of /analyze for daily automated insights.
```

---

## Message Formatting

- **Markdown**: Enabled for bold, italic, code
- **Emojis**: Used sparingly for visual hierarchy
- **Line Breaks**: Used for readability
- **Inline Buttons**: Maximum 3 per row
- **Message Length**: Truncated with "Load More" if >4096 characters

---

## Privacy & Security

- **Data Stored**: Telegram user ID, username, subscriptions only
- **No PII**: No names, emails, or contact info
- **Data Retention**: 1 year for insights, indefinite for subscriptions
- **Admin Access**: Only authorized users can execute admin commands
- **Rate Limiting**: Per-user limits to prevent abuse

---

## Testing

Test bot with BotFather test environment:

```
/start - Initialize
/subscribe AAPL - Test subscription
/analyze AAPL - Test analysis
/list - View subscriptions
/history AAPL - Test history query
/unsubscribe AAPL - Test unsubscribe
```

---

## Deployment

```yaml
# GitHub Actions workflow
- name: Start Telegram Bot
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  run: python -m stock_analyzer.bot
```

---

## Version History

- **1.0.0** (2026-01-30): Initial Telegram bot interface
