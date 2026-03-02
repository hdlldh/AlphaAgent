# Implementation Plan: Personal Stock Monitor with Telegram Channel

**Branch**: `002-personal-telegram-stocks` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-personal-telegram-stocks/spec.md`

## Summary

Refactor the AlphaAgent stock analyzer from a multi-user subscription system to a personal stock monitoring tool. The application will read a fixed stock list from environment variables, run automated daily analysis, and post insights to a single Telegram channel instead of individual user messages. This simplification removes user management, subscription tracking, and interactive bot commands while retaining analysis and historical query capabilities.

**Key Technical Changes**:
- Remove `users` and `subscriptions` tables from database schema
- Add environment variables: `STOCK_ANALYZER_STOCK_LIST` and `STOCK_ANALYZER_TELEGRAM_CHANNEL`
- Refactor daily analysis workflow to read stock list from config instead of subscriptions
- Update Telegram deliverer to post to channel (broadcast) instead of individual user messages
- Remove CLI commands: `subscribe`, `unsubscribe`, `list-subscriptions`
- Remove or disable interactive Telegram bot (`/start`, `/subscribe`, etc.)
- Retain CLI commands: `init-db`, `analyze`, `history`, `run-daily-job`
- Retain analysis and insight storage without user associations

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `python-telegram-bot` v20.x (async, for Telegram channel posting)
- `anthropic`, `openai`, `google-generativeai` (LLM providers)
- `yfinance`, `alpha-vantage` (stock data)
- `pandas` (data manipulation)
- `pytest`, `pytest-asyncio` (testing)

**Storage**: SQLite database (`./data/stock_analyzer.db`)
- Remove tables: `users`, `subscriptions`
- Keep tables: `stock_analyses`, `insights`, `delivery_logs`, `analysis_jobs`
- Update schema: Remove `user_id` foreign keys from `insights` and `delivery_logs`

**Testing**: pytest with TDD workflow
- Contract tests: Verify CLI interface, storage interface, deliverer interface
- Integration tests: End-to-end daily job workflow, Telegram channel posting
- Unit tests: Configuration parsing, stock list validation

**Target Platform**: Linux server (GitHub Actions, VPS)
**Project Type**: Single Python project with CLI interface
**Performance Goals**:
- Analyze 50 stocks in <15 minutes
- Post to Telegram channel with <5 second latency per message
- CLI history queries in <2 seconds

**Constraints**:
- Backward compatible with existing historical analysis data
- No breaking changes to existing `analyze` and `history` CLI commands (only removals)
- Telegram Bot API rate limit: 30 messages/second per bot

**Scale/Scope**:
- 5-50 stocks (personal use)
- 1000+ historical analysis records
- Single Telegram channel
- GitHub Actions daily workflow (Mon-Fri)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the AlphaAgent Constitution (v1.0.0), verify compliance with these principles:

### I. Library-First
- [x] Feature designed as standalone library
- [x] Library is self-contained and independently testable
- [x] Library has clear, singular purpose
- [x] Library has complete documentation plan

**Violations**: None
**Justification**: N/A - Existing codebase already follows library-first design. The refactoring maintains the `stock_analyzer` library structure with CLI wrapper.

### II. CLI Interface
- [x] Library exposes functionality via CLI
- [x] Text in/out protocol: stdin/args → stdout, errors → stderr
- [x] Supports both JSON and human-readable output

**Violations**: None
**Justification**: N/A - Existing CLI commands (`analyze`, `history`) already support both JSON and human-readable output. Refactoring removes some commands but maintains the protocol.

### III. Test-First (NON-NEGOTIABLE)
- [x] Tests will be written before implementation
- [x] Tests will be approved by user before implementation
- [x] Tests will fail before implementation begins
- [x] Red-Green-Refactor cycle documented in tasks

**Violations**: None
**Justification**: N/A - TDD workflow will be strictly followed. Tests for new functionality (environment-based stock list, channel posting) will be written first per constitution requirements.

### IV. Integration Testing
- [x] Contract tests planned for public interfaces
- [x] Integration tests planned for external dependencies
- [x] Contract changes have backward compatibility tests
- [x] Shared schemas have validation tests

**Violations**: None
**Justification**: N/A - Contract tests will verify CLI and storage interface changes. Integration tests will cover Telegram channel posting and end-to-end daily job workflow.

### V. Simplicity
- [x] Solution uses simplest approach that meets requirements
- [x] No premature optimization
- [x] No unnecessary abstraction layers
- [x] Complexity is justified in Complexity Tracking table

**Violations**: None
**Justification**: N/A - This refactoring **reduces** complexity by removing multi-user abstractions. The simplest approach is to read a comma-separated environment variable and post to a single channel.

**Overall Status**: PASS ✅

## Project Structure

### Documentation (this feature)

```text
specs/002-personal-telegram-stocks/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (design decisions)
├── data-model.md        # Phase 1 output (simplified schema)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (CLI contracts)
│   ├── cli.md           # CLI interface contracts
│   ├── storage.md       # Storage interface contracts
│   └── deliverer.md     # Deliverer interface contracts
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT YET CREATED)
```

### Source Code (repository root)

```text
src/
├── stock_analyzer/
│   ├── __init__.py
│   ├── models.py           # MODIFY: Remove User, Subscription; Update DeliveryLog
│   ├── config.py           # MODIFY: Add stock_list, telegram_channel config
│   ├── storage.py          # MODIFY: Remove user/subscription methods; Update schema
│   ├── analyzer.py         # NO CHANGE: Analysis logic unchanged
│   ├── fetcher.py          # NO CHANGE: Stock data fetching unchanged
│   ├── llm_client.py       # NO CHANGE: LLM provider abstraction unchanged
│   ├── deliverer.py        # MODIFY: Add channel posting; Remove user-specific delivery
│   ├── cli.py              # MODIFY: Remove subscribe/unsubscribe; Update run-daily-job
│   ├── bot.py              # REMOVE or DISABLE: Interactive bot commands
│   ├── exceptions.py       # NO CHANGE: Custom exceptions unchanged
│   ├── logging.py          # NO CHANGE: Logging setup unchanged
│   └── retry.py            # NO CHANGE: Retry logic unchanged
│
└── scripts/
    ├── daily_analysis.py   # MODIFY: Read stock list from config instead of subscriptions
    └── run_bot.py          # REMOVE or DISABLE: No longer needed for personal use

tests/
├── contract/
│   ├── test_cli_contract.py          # MODIFY: Remove subscription command tests
│   ├── test_storage_contract.py      # MODIFY: Remove user/subscription tests
│   └── test_deliverer_contract.py    # MODIFY: Add channel posting tests
│
├── integration/
│   ├── test_end_to_end.py            # MODIFY: Update daily job workflow tests
│   └── test_telegram_integration.py  # MODIFY: Test channel posting
│
└── unit/
    ├── test_config.py                # MODIFY: Add stock list parsing tests
    ├── test_storage.py               # MODIFY: Remove user/subscription tests
    ├── test_deliverer.py             # MODIFY: Add channel posting tests
    └── test_subscriptions.py         # REMOVE: No longer relevant

data/
└── stock_analyzer.db       # MODIFY: Schema migration to remove users/subscriptions

.github/
└── workflows/
    ├── daily-analysis.yml  # MODIFY: Update env vars (add stock list, channel ID)
    └── telegram-bot.yml    # REMOVE or DISABLE: No longer needed

.env.example                # MODIFY: Add STOCK_ANALYZER_STOCK_LIST, TELEGRAM_CHANNEL
```

**Structure Decision**: Single project structure is maintained as this is a refactoring of the existing AlphaAgent codebase. The library (`stock_analyzer/`) and CLI wrapper (`cli.py`) remain unchanged in structure. Changes are primarily removals (users, subscriptions, bot) and modifications (config, storage, deliverer).

## Complexity Tracking

**No violations** - This refactoring reduces complexity:

| Before (Multi-User) | After (Personal) | Simplification |
|---------------------|------------------|----------------|
| Users table with foreign keys | No users table | Remove user management complexity |
| Subscriptions with limits (10/user, 100/system) | Environment variable list (5-50 stocks) | Remove subscription tracking |
| Per-user Telegram message delivery | Single channel broadcast | Simplify delivery logic |
| Interactive bot with 7 commands | No interactive bot (channel-only) | Remove bot state management |
| User-specific history queries | Global history queries | Simplify query logic |

**Result**: Estimated **30-40% reduction** in codebase complexity (lines of code, test cases, configuration options).
