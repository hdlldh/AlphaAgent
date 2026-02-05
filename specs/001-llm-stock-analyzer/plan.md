# Implementation Plan: AI-Powered Stock Analysis

**Branch**: `001-llm-stock-analyzer` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-llm-stock-analyzer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an automated stock analysis system that uses AI (LLM) to analyze stock market data daily and deliver insights to users via Telegram. The system runs on a scheduled basis (GitHub Actions), fetches stock data from market APIs, generates AI-powered insights (trends, risks, opportunities), and delivers them through a Telegram bot. Users manage subscriptions via Telegram bot commands. The system stores historical insights for later retrieval and enforces limits of 10 stocks per user, 100 total.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- `uv` (Python package manager - as specified by user)
- LLM client libraries: `anthropic` (v2.7+), `openai` (v1.0+), `google-generativeai` (v0.3+)
- Stock data API client: `yfinance` (v1.1.0) with `alpha-vantage` (v3.0+) backup
- `python-telegram-bot` (v22.x) for Telegram bot
- SQLite (stdlib) for storage

**Storage**: SQLite with Git-committed database file
**Testing**: pytest with pytest-asyncio (for async operations)
**Target Platform**: GitHub Actions (scheduled workflows), Linux container environment
**Project Type**: Single project (CLI library + scheduled job + Telegram bot)
**Performance Goals**:
- Complete analysis for 100 stocks within 1 hour
- Respond to Telegram commands within 3 seconds
- Query historical insights within 3 seconds

**Constraints**:
- Must run in GitHub Actions free tier constraints (6 hours max runtime, usage limits)
- Must handle API rate limits gracefully (stock data API, LLM API, Telegram API)
- Must store secrets securely (Telegram bot token, LLM API key, stock data API key)
- Must be cost-effective (minimize LLM API calls, use free/low-cost stock data sources if possible)

**Scale/Scope**:
- 10 stocks per user maximum
- 100 stocks total across all users
- Estimated 10-20 users initially
- Historical data retention: 1 year minimum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on the AlphaAgent Constitution (v1.0.0), verify compliance with these principles:

### I. Library-First
- [x] Feature designed as standalone library
- [x] Library is self-contained and independently testable
- [x] Library has clear, singular purpose
- [x] Library has complete documentation plan

**Violations**: None
**Justification**: The stock analyzer will be built as a standalone library (`stock_analyzer`) with clear interfaces for analysis, data fetching, and delivery. The CLI and Telegram bot will be thin wrappers around the library.

### II. CLI Interface
- [x] Library exposes functionality via CLI
- [x] Text in/out protocol: stdin/args → stdout, errors → stderr
- [x] Supports both JSON and human-readable output

**Violations**: None
**Justification**: The library will expose CLI commands:
- `stock-analyzer analyze <symbol>` - Analyze a single stock, output to stdout
- `stock-analyzer analyze-batch <file>` - Analyze multiple stocks from file
- `stock-analyzer subscribe <user_id> <symbol>` - Manage subscriptions
- `stock-analyzer history <symbol>` - Query historical insights
All commands will support `--json` flag for JSON output, default to human-readable format.

### III. Test-First (NON-NEGOTIABLE)
- [x] Tests will be written before implementation
- [x] Tests will be approved by user before implementation
- [x] Tests will fail before implementation begins
- [x] Red-Green-Refactor cycle documented in tasks

**Violations**: None
**Justification**: All tasks in tasks.md will follow TDD workflow. Tests written first for each component (data fetching, analysis, delivery, storage). User approval required before implementation begins. Tests will be committed first and verified to fail.

### IV. Integration Testing
- [x] Contract tests planned for public interfaces
- [x] Integration tests planned for external dependencies
- [x] Contract changes have backward compatibility tests
- [x] Shared schemas have validation tests

**Violations**: None
**Justification**: Integration tests planned for:
- Stock data API integration (with mocked/recorded responses)
- LLM API integration (with mocked responses)
- Telegram API integration (with test bot)
- Storage layer contract tests
- End-to-end workflow tests (subscribe → analyze → deliver → query history)

### V. Simplicity
- [x] Solution uses simplest approach that meets requirements
- [x] No premature optimization
- [x] No unnecessary abstraction layers
- [x] Complexity is justified in Complexity Tracking table

**Violations**: None
**Justification**:
- Simple file-based or SQLite storage (no need for PostgreSQL initially)
- Direct API calls (no complex queueing system)
- Straightforward scheduled job (GitHub Actions cron)
- Minimal abstractions (data fetcher, analyzer, deliverer, storage)

**Overall Status**: PASS - All constitution principles satisfied. Ready for Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-stock-analyzer/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (already complete)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli.md          # CLI interface contract
│   ├── library.md      # Library API contract
│   └── telegram.md     # Telegram bot commands contract
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── stock_analyzer/
│   ├── __init__.py
│   ├── cli.py              # CLI entry points
│   ├── models.py           # Data models (Subscription, Analysis, Insight)
│   ├── fetcher.py          # Stock data fetching
│   ├── analyzer.py         # LLM-based analysis logic
│   ├── deliverer.py        # Delivery abstraction (Telegram, extensible)
│   ├── storage.py          # Storage abstraction (file/SQLite)
│   └── bot.py              # Telegram bot implementation
└── scripts/
    └── daily_analysis.py   # Scheduled job entry point

tests/
├── contract/
│   ├── test_cli_contract.py
│   ├── test_library_contract.py
│   └── test_telegram_contract.py
├── integration/
│   ├── test_stock_data_integration.py
│   ├── test_llm_integration.py
│   ├── test_telegram_integration.py
│   └── test_end_to_end.py
└── unit/
    ├── test_models.py
    ├── test_fetcher.py
    ├── test_analyzer.py
    ├── test_deliverer.py
    └── test_storage.py

.github/
└── workflows/
    ├── daily-analysis.yml   # Scheduled job (cron)
    └── test.yml             # CI tests

pyproject.toml               # uv project configuration
README.md                    # User guide
```

**Structure Decision**: Single project structure chosen because:
- All components are tightly related (analysis pipeline)
- No separate frontend/backend (Telegram is the interface)
- Library + CLI + scheduled job fits naturally in one repository
- Simplifies testing and deployment
- Aligns with Library-First principle

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - table intentionally left empty.

---

## Phase 0: Research - ✅ COMPLETE

All NEEDS CLARIFICATION items resolved. See `research.md` for detailed findings.

**Decisions Made**:
1. **LLM API**: Multi-provider support (Claude, OpenAI, Gemini) - Claude Sonnet 4.5 recommended (~$18-27/month with caching)
2. **Stock Data**: yfinance (primary, free) + Alpha Vantage (backup, 25 calls/day free)
3. **Telegram Bot**: python-telegram-bot v22.x
4. **Storage**: SQLite with Git-committed database file

---

## Phase 1: Design & Contracts - ✅ COMPLETE

All design artifacts generated and agent context updated.

**Artifacts Created**:
- ✅ `research.md`: Technology decisions with rationale
- ✅ `data-model.md`: Entity definitions, relationships, database schema
- ✅ `contracts/cli.md`: Command-line interface contract
- ✅ `contracts/library.md`: Python library API contract
- ✅ `contracts/telegram.md`: Telegram bot interface contract
- ✅ `quickstart.md`: Developer onboarding guide
- ✅ `CLAUDE.md`: Agent context file updated

---

## Constitution Check (Post-Design)

Re-evaluating compliance after Phase 1 design completion:

### I. Library-First ✅
- [x] Feature designed as standalone `stock_analyzer` library
- [x] Library is self-contained with clear module boundaries
- [x] Independently testable with comprehensive test structure
- [x] Complete documentation: contracts, data model, quickstart

**Status**: PASS - Library structure clearly defined with CLI and bot as thin wrappers

### II. CLI Interface ✅
- [x] Full CLI contract defined in `contracts/cli.md`
- [x] Text in/out protocol: 10 commands with stdin/stdout/stderr separation
- [x] Both JSON and human-readable output formats specified
- [x] Exit codes defined for error handling

**Status**: PASS - Comprehensive CLI interface contract complete

### III. Test-First (NON-NEGOTIABLE) ✅
- [x] Test structure defined: contract/, integration/, unit/
- [x] Testing strategy documented in contracts
- [x] Mock classes specified for unit testing
- [x] TDD workflow will be enforced in tasks.md (next phase)

**Status**: PASS - Testing infrastructure designed, ready for implementation

### IV. Integration Testing ✅
- [x] Contract tests planned for CLI, library, Telegram interfaces
- [x] Integration tests planned for stock API, LLM API, Telegram API
- [x] End-to-end workflow tests defined
- [x] Storage layer contract tests specified

**Status**: PASS - Comprehensive integration testing strategy defined

### V. Simplicity ✅
- [x] Simple SQLite storage (no complex database)
- [x] Direct API calls (no queueing complexity)
- [x] Straightforward GitHub Actions scheduling
- [x] Minimal abstractions: fetcher, analyzer, deliverer, storage

**Status**: PASS - Design remains simple and focused

**Overall Status**: ✅ PASS - All constitution principles satisfied post-design

---

## Next Steps

Planning phase complete. Ready for Phase 2: Task Generation

Run the following command to generate actionable tasks:

```bash
/speckit.tasks
```

This will create `tasks.md` with:
- Setup tasks (project initialization)
- Foundational tasks (core infrastructure)
- User Story 1 tasks (Daily Stock Insights Delivery - P1 MVP)
- User Story 2 tasks (Stock Subscription Management - P2)
- User Story 3 tasks (Historical Insight Access - P3)
- Polish & cross-cutting concerns

Each task will include:
- Exact file paths
- Test-first workflow steps
- Parallel execution opportunities
- Clear dependencies

---

## Summary

The AI-Powered Stock Analysis system is architected as a simple, maintainable solution that:

1. **Follows Constitution**: All principles satisfied, no violations
2. **Uses Proven Technologies**: Python, SQLite, established APIs
3. **Keeps Costs Low**: ~$18-27/month (LLM API only)
4. **Scales Appropriately**: 100 stocks, 10 users initially, room to grow
5. **Maintains Simplicity**: No premature optimization or unnecessary complexity

**Technology Stack**:
- Python 3.11+ with uv package manager
- Multi-provider LLM support: Anthropic Claude (recommended), OpenAI, Google Gemini
- yfinance + Alpha Vantage for stock data
- python-telegram-bot v22.x for delivery
- SQLite with Git-committed storage
- GitHub Actions for scheduled execution
- pytest for comprehensive testing

**Estimated Implementation Time**: 2-3 weeks for MVP (User Story 1), 4-6 weeks for full feature set

**Ready for Implementation**: All design complete, proceed to task generation and TDD implementation.
