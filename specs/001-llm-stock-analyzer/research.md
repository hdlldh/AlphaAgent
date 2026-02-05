# Research Findings: AI-Powered Stock Analysis

**Date**: 2026-01-30
**Feature**: 001-llm-stock-analyzer

## Overview

This document consolidates research findings for technical decisions required to implement the AI-powered stock analysis system. All NEEDS CLARIFICATION items from the Technical Context have been resolved through systematic evaluation of alternatives.

---

## Research Area 1: LLM API Selection

### Decision

**Multi-Provider Support with Configurable Models**

The system supports three LLM providers:
- **Anthropic Claude** (Recommended): Sonnet 4.5 (primary), Haiku 4.5 (cost-optimization), Opus 4.5 (premium)
- **OpenAI**: GPT-4o, GPT-4 Turbo, GPT-4o-mini
- **Google Gemini**: 2.5 Pro, 2.5 Flash

**Default Recommendation**: Claude Sonnet 4.5

### Rationale for Multi-Provider Approach

1. **Flexibility**: Users can choose based on budget, performance, or existing API subscriptions
2. **Redundancy**: Fallback to alternative providers if primary is unavailable
3. **Cost Optimization**: Switch to cheaper models for high-volume scenarios
4. **Future-Proof**: Easy to add new providers as they emerge
5. **Provider-Specific Features**: Leverage unique capabilities of each provider

### Provider Comparison

#### Anthropic Claude (Recommended)

**Strengths**:
- Superior analytical reasoning validated by finance domain experts
- Cost-effective with prompt caching (90% discount on cached tokens)
- Excellent async Python SDK with full type hints
- Transparent rate limits and clear pricing

**Pricing** (per 1M tokens):
- Sonnet 4.5: $3 input / $15 output (with caching: $0.30/$0.60 cached)
- Haiku 4.5: $1 input / $5 output
- Opus 4.5: $5 input / $25 output

**Monthly Cost** (100 stocks, 20 days): $18-27 with caching

#### OpenAI

**Strengths**:
- Most mature ecosystem and widespread adoption
- Strong general-purpose reasoning
- Excellent documentation and community support
- Function calling for structured outputs

**Pricing** (per 1M tokens, estimated):
- GPT-4o: $5 input / $15 output
- GPT-4 Turbo: $10 input / $30 output
- GPT-4o-mini: $0.15 input / $0.60 output

**Monthly Cost** (100 stocks, 20 days): $10-50 depending on model

#### Google Gemini

**Strengths**:
- Competitive pricing (Flash model very cheap)
- Long context windows
- Fast inference speed
- Good for high-volume scenarios

**Pricing** (per 1M tokens):
- Gemini 2.5 Pro: $1.25 input / $5 output
- Gemini 2.5 Flash: $0.30 input / $2.50 output

**Monthly Cost** (100 stocks, 20 days): $6-15 depending on model

### Cost Analysis

**Monthly Cost Estimates (100 stocks, 20 trading days/month)**:
- **Claude Sonnet 4.5 with caching**: ~$18.36/month
- **Claude Haiku 4.5 with caching**: ~$6.12/month (cost-optimization option)
- **Without caching**: ~$27/month (Sonnet)

**Rate Limits**:
- Tier 1 (free entry): 50 RPM, 30K input TPM - adequate for sequential processing
- Tier 2 ($40 deposit): 1,000 RPM - enables parallel processing

### Alternatives Considered

- **OpenAI GPT-4o**: Similar cost but less specialized for sustained analytical reasoning
- **Google Gemini 2.5 Flash**: Cheaper ($0.30/$2.50 per MTok) but lower rate limits and less proven for financial reasoning
- **Together AI (Open Source)**: Significantly lower costs but reduced reasoning quality
- **Claude Opus 4.5**: Highest quality but 3x cost - reserve for quarterly deep-dives

### Implementation Plan

1. **Phase 1 (MVP)**: Implement provider abstraction with Claude Sonnet 4.5 as default
2. **Phase 2 (Multi-Provider)**: Add OpenAI and Gemini support via adapter pattern
3. **Phase 3 (Optimization)**: Implement provider-specific optimizations (caching, batching)
4. **Phase 4 (Advanced)**: Implement fallback logic and provider health monitoring

### Provider Configuration

```python
# Configuration options
[api]
llm_provider = "anthropic"  # or "openai", "gemini"
llm_model = "claude-sonnet-4-5"  # or "gpt-4o", "gemini-2-5-pro"
llm_api_key = "${LLM_API_KEY}"

# Fallback configuration
llm_fallback_provider = "openai"
llm_fallback_model = "gpt-4o-mini"
llm_fallback_api_key = "${OPENAI_API_KEY}"

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
```

---

## Research Area 2: Stock Market Data API

### Decision

**yfinance (Primary) + Alpha Vantage (Backup/Validation)**

### Rationale

1. **Cost**: yfinance is completely free with unlimited access; Alpha Vantage free tier provides 25 calls/day for validation
2. **Python Integration**: yfinance has excellent pandas integration, 21.2K GitHub stars, actively maintained (v1.1.0)
3. **Data Coverage**: Historical data going back decades, comprehensive fundamentals, suitable for 100 stocks daily
4. **Community**: Large user base (85,800+ projects), extensive examples and documentation
5. **Backup Strategy**: Alpha Vantage provides official API for critical data validation within free tier limits

### Free Tier Limits

**yfinance**:
- Cost: Free, no API key required
- Rate Limits: No documented hard limits
- Coverage: Global markets, decades of historical data
- Data Types: OHLCV, dividends, splits, fundamentals

**Alpha Vantage**:
- Cost: Free tier available
- Rate Limits: 25 API calls/day
- Coverage: Global markets, 20+ years historical
- Data Types: Time series, 50+ technical indicators, fundamentals

### Trade-offs Acknowledged

**yfinance Limitations**:
- Not officially supported by Yahoo (uses public API)
- No SLA guarantees
- Occasional data accuracy concerns

**Mitigation**:
- Use Alpha Vantage's 25 daily calls for critical validation
- Implement error handling and retry logic
- Cache data locally
- Monitor for stale data

### Alternatives Considered

- **Twelve Data**: 8 credits/min free (insufficient for 100 stocks)
- **Financial Modeling Prep**: 250 calls/day (barely sufficient, no official Python library)
- **Polygon.io**: High quality but primarily paid ($49-99/month)
- **IEX Cloud**: Outdated Python library (v0.5.0 from 2020)
- **Finnhub**: Unclear free tier limits

---

## Research Area 3: Telegram Bot Framework

### Decision

**python-telegram-bot (PTB) v22.x**

### Rationale

1. **Async Support**: Fully asynchronous since v20.0, built on asyncio - ideal for GitHub Actions
2. **Documentation**: Exceptional with 200+ types documented, comprehensive wiki, 19 examples
3. **Community**: 28.7K stars, 237 contributors, 154K projects - largest ecosystem
4. **Testing**: Excellent support with dedicated wiki pages, manual update enqueueing, no external connection needed
5. **Maintenance**: Very active (7 releases/year), only 15 open issues

### Key Features

- Clean async/await syntax with context manager support
- Comprehensive handler system with filters
- Built-in job queue for task scheduling
- Convenient shortcut methods (`Message.reply_text`)
- Minimal dependencies (only `httpx` required)
- LGPLv3 license

### Testing Support

- Manual update processing without network calls
- Mock Bot class for unit tests
- Custom BaseRequest subclasses for integration tests
- Dedicated testing documentation

### Alternatives Considered

- **aiogram**: Good async support but smaller community (5.6K stars), weaker documentation, limited testing guidance
- **pyTelegramBotAPI**: Simpler but not async-first, less comprehensive testing support

---

## Research Area 4: Storage Solution

### Decision

**SQLite with Git-Committed Database File**

### Rationale

1. **Persistence**: Database file committed to Git ensures state persists across GitHub Actions runs
2. **Query Performance**: Handles 36,500+ records easily, indexed queries complete in <10ms
3. **Simplicity**: Single file, no infrastructure, `sqlite3` in Python stdlib
4. **Zero Cost**: No external services, API keys, or subscription fees
5. **Reliability**: ACID transactions, version-controlled backups, no network dependency

### Database Schema

```sql
-- User subscriptions (user_id, stock_symbol, preferences)
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    stock_symbol TEXT NOT NULL,
    subscription_date TEXT NOT NULL,
    active_status INTEGER DEFAULT 1,
    preferences TEXT,  -- JSON
    UNIQUE(user_id, stock_symbol)
);

-- Historical insights (stock_symbol, date, analysis)
CREATE TABLE insights (
    id INTEGER PRIMARY KEY,
    stock_symbol TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    price_snapshot REAL,
    analysis_text TEXT NOT NULL,
    metadata TEXT,  -- JSON: trends, risks, opportunities
    created_at TEXT NOT NULL,
    UNIQUE(stock_symbol, analysis_date)
);

-- Job execution logs
CREATE TABLE job_logs (
    id INTEGER PRIMARY KEY,
    execution_time TEXT NOT NULL,
    stocks_processed INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    errors TEXT,  -- JSON
    duration_seconds REAL
);
```

### Persistence Strategy

1. **Database Location**: `data/stock_analyzer.db` in repository root
2. **Git Tracking**: Database file committed to version control
3. **Workflow Integration**: GitHub Actions commits database after each run
4. **Conflict Handling**: Serialized workflow execution prevents concurrent writes
5. **Size Management**: Expected 5-10 MB/year, well within GitHub's 100 GB limit

### Performance Expectations

- Simple SELECT with index: <10ms for 36K rows
- Date range queries: <50ms
- Historical aggregations: <100ms
- Storage growth: ~300 KB/day, ~10 MB/year

### Alternatives Considered

- **JSON Files**: Poor query performance, no indexing, 36K+ files unwieldy
- **CSV Files**: O(n) search, no relationships, inadequate for 36K+ records
- **GitHub Actions Cache/Artifacts**: 7-90 day retention (insufficient), not queryable
- **Cloud Databases**: Unnecessary infrastructure, $5-50/month cost, violates simplicity principle
- **Hybrid (SQLite + Releases)**: Premature optimization, adds complexity

---

## Technology Stack Summary

### Final Decisions

| Component | Choice | Version | License | Cost |
|-----------|--------|---------|---------|------|
| Language | Python | 3.11+ | PSF | Free |
| Package Manager | uv | Latest | MIT/Apache-2.0 | Free |
| LLM API (Primary) | Anthropic Claude | Sonnet 4.5 | Commercial | $18-27/month |
| LLM API (Optional) | OpenAI | GPT-4o / GPT-4o-mini | Commercial | $10-50/month |
| LLM API (Optional) | Google Gemini | 2.5 Pro / Flash | Commercial | $6-15/month |
| Stock Data | yfinance | 1.1.0 | Apache-2.0 | Free |
| Stock Data Backup | Alpha Vantage | Latest | Commercial | Free (25/day) |
| Telegram Bot | python-telegram-bot | 22.x | LGPLv3 | Free |
| Storage | SQLite | 3.x (stdlib) | Public Domain | Free |
| Testing | pytest + pytest-asyncio | Latest | MIT | Free |
| Async Library | asyncio | stdlib | PSF | Free |

### Dependencies to Add

```toml
[project]
dependencies = [
    "anthropic>=2.7.0",
    "openai>=1.0.0",
    "google-generativeai>=0.3.0",
    "yfinance>=1.1.0",
    "alpha-vantage>=3.0.0",
    "python-telegram-bot>=22.0.0",
    "httpx>=0.27.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

### LLM Provider Options

**Anthropic Claude** (Recommended):
- Models: claude-sonnet-4-5, claude-haiku-4-5, claude-opus-4-5
- Cost: $18-27/month (Sonnet with caching)
- Strengths: Best analytical reasoning, prompt caching, transparent pricing

**OpenAI** (Alternative):
- Models: gpt-4o, gpt-4-turbo, gpt-4o-mini
- Cost: $10-50/month depending on model
- Strengths: Mature ecosystem, function calling, widespread adoption

**Google Gemini** (Budget Option):
- Models: gemini-2.5-pro, gemini-2.5-flash
- Cost: $6-15/month depending on model
- Strengths: Cheapest option, fast inference, long context

### Total Estimated Cost

**With Recommended Configuration** (Claude Sonnet 4.5):
- **LLM API**: $18-27/month
- **Stock Data**: $0/month (yfinance + Alpha Vantage free tiers)
- **Telegram Bot**: $0/month (free API)
- **Storage**: $0/month (Git-committed SQLite)
- **Hosting**: $0/month (GitHub Actions free tier)

**Total Monthly Cost**: $18-27 (LLM API only)

**With Budget Configuration** (Gemini Flash):
- **Total Monthly Cost**: $6-10 (LLM API only)

**With Alternative Configuration** (OpenAI GPT-4o-mini):
- **Total Monthly Cost**: $10-15 (LLM API only)

---

## Risk Assessment

### Technical Risks

1. **yfinance Reliability**: Unofficial API may break
   - **Mitigation**: Alpha Vantage backup, error handling, local caching

2. **GitHub Actions Limits**: 6-hour max runtime, usage quotas
   - **Mitigation**: 100 stocks completes in <1 hour, well within limits

3. **SQLite Database Size**: Large binary in Git
   - **Mitigation**: Expected 10 MB/year acceptable, archive strategy available

4. **LLM API Costs**: Usage may exceed estimates
   - **Mitigation**: Implement cost monitoring, fallback to Haiku, usage caps

### Operational Risks

1. **API Rate Limits**: Stock API, LLM API, Telegram API
   - **Mitigation**: Retry logic, exponential backoff, sequential processing

2. **Data Accuracy**: Stock data or LLM hallucinations
   - **Mitigation**: Cross-validation with Alpha Vantage, disclaimer that insights are not financial advice

3. **Workflow Failures**: GitHub Actions down or failing
   - **Mitigation**: Manual trigger option, alerting, robust error handling

---

## Next Steps

All NEEDS CLARIFICATION items resolved. Proceeding to Phase 1:

1. ✅ LLM API: Anthropic Claude Sonnet 4.5
2. ✅ Stock Data: yfinance + Alpha Vantage
3. ✅ Telegram Bot: python-telegram-bot v22.x
4. ✅ Storage: SQLite with Git-committed DB

Ready to generate:
- `data-model.md`: Entity definitions and relationships
- `contracts/`: CLI, library, and Telegram bot interfaces
- `quickstart.md`: Developer onboarding guide
