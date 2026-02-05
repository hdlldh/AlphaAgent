# Tasks: AI-Powered Stock Analysis

**Input**: Design documents from `/specs/001-llm-stock-analyzer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per AlphaAgent Constitution (Test-First principle, NON-NEGOTIABLE)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/stock_analyzer/`, `tests/` at repository root
- All Python modules under `src/stock_analyzer/`
- Tests organized: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/stock_analyzer/, tests/, data/, .github/workflows/)
- [X] T002 Initialize Python project with uv (pyproject.toml with dependencies)
- [X] T003 [P] Configure pytest with pytest-asyncio in pyproject.toml
- [X] T004 [P] Create .env.example with required environment variables
- [X] T005 [P] Create .gitignore for Python project (exclude .env, __pycache__, .pytest_cache)
- [X] T006 [P] Add data/stock_analyzer.db to Git tracking (create empty file)
- [X] T007 Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Configuration & Error Handling

- [X] T008 Create src/stock_analyzer/__init__.py with version and exports
- [X] T009 Create src/stock_analyzer/exceptions.py with custom exception classes
- [X] T010 Create src/stock_analyzer/config.py with Config class (load from env/file)

### Data Models (Shared)

- [X] T011 [P] Create src/stock_analyzer/models.py with base dataclasses (User, Subscription, StockData, AnalysisResponse)

### Storage Layer

- [X] T012 Write tests for Storage class in tests/unit/test_storage.py
- [X] T013 Verify tests FAIL (run pytest tests/unit/test_storage.py)
- [X] T014 Create src/stock_analyzer/storage.py with Storage class (SQLite operations)
- [X] T015 Implement init_database() with schema from data-model.md in src/stock_analyzer/storage.py
- [X] T016 Verify tests PASS (run pytest tests/unit/test_storage.py)

### LLM Provider Abstraction

- [X] T017 Write tests for LLMClient abstraction in tests/unit/test_llm_client.py
- [X] T018 Verify tests FAIL (run pytest tests/unit/test_llm_client.py)
- [X] T019 Create src/stock_analyzer/llm_client.py with LLMClient abstract base class
- [X] T020 [P] Implement ClaudeLLMClient in src/stock_analyzer/llm_client.py
- [X] T021 [P] Implement OpenAILLMClient in src/stock_analyzer/llm_client.py
- [X] T022 [P] Implement GeminiLLMClient in src/stock_analyzer/llm_client.py
- [X] T023 Implement LLMClientFactory.create() in src/stock_analyzer/llm_client.py
- [X] T024 Verify tests PASS (run pytest tests/unit/test_llm_client.py)

### Stock Data Fetcher

- [X] T025 Write tests for StockFetcher in tests/unit/test_fetcher.py
- [X] T026 Verify tests FAIL (run pytest tests/unit/test_fetcher.py)
- [X] T027 Create src/stock_analyzer/fetcher.py with StockFetcher class
- [X] T028 Implement fetch_stock_data() with yfinance in src/stock_analyzer/fetcher.py
- [X] T029 Implement validate_symbol() in src/stock_analyzer/fetcher.py
- [X] T030 Add Alpha Vantage fallback logic in src/stock_analyzer/fetcher.py
- [X] T031 Verify tests PASS (run pytest tests/unit/test_fetcher.py)

### Integration Tests for External APIs

- [X] T032 [P] Create tests/integration/test_stock_data_integration.py with mocked yfinance responses
- [X] T033 [P] Create tests/integration/test_llm_integration.py with mocked LLM responses
- [X] T034 Run integration tests (pytest tests/integration/)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Daily Stock Insights Delivery (Priority: P1) 🎯 MVP

**Goal**: Automated daily analysis that fetches stock data, generates AI insights, and delivers via Telegram

**Independent Test**: Configure system to analyze AAPL, run daily job, verify insight generated and delivered to test user

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T035 [P] [US1] Write contract test for Analyzer.analyze_stock() in tests/contract/test_analyzer_contract.py
- [x] T036 [P] [US1] Write contract test for CLI analyze command in tests/contract/test_cli_contract.py
- [x] T037 [P] [US1] Write integration test for end-to-end analysis workflow in tests/integration/test_end_to_end.py
- [x] T038 [US1] Verify all US1 tests FAIL (run pytest -k US1)

### Implementation for User Story 1

#### Core Analysis Logic

- [x] T039 [P] [US1] Create src/stock_analyzer/analyzer.py with Analyzer class
- [x] T040 [US1] Implement analyze_stock() method in src/stock_analyzer/analyzer.py (uses fetcher + LLM)
- [x] T041 [US1] Implement analyze_batch() method in src/stock_analyzer/analyzer.py (parallel analysis)
- [x] T042 [US1] Add prompt templates for stock analysis in src/stock_analyzer/analyzer.py

#### Insight Storage

- [x] T043 [US1] Add save_analysis() and save_insight() methods to src/stock_analyzer/storage.py
- [x] T044 [US1] Add get_analysis() method to src/stock_analyzer/storage.py

#### Delivery System

- [x] T045 [US1] Create src/stock_analyzer/deliverer.py with InsightDeliverer class
- [x] T046 [US1] Implement TelegramChannel class in src/stock_analyzer/deliverer.py
- [x] T047 [US1] Implement deliver_insight() method in src/stock_analyzer/deliverer.py
- [x] T048 [US1] Implement deliver_batch() method in src/stock_analyzer/deliverer.py
- [x] T049 [US1] Add delivery logging to Storage (save to delivery_logs table)

#### Daily Job Script

- [x] T050 [US1] Create src/scripts/daily_analysis.py with main() function
- [x] T051 [US1] Implement job workflow in src/scripts/daily_analysis.py (get subscriptions → analyze → deliver)
- [x] T052 [US1] Add job logging to Storage (create_job, update_job) in src/stock_analyzer/storage.py
- [x] T053 [US1] Add error handling and retry logic in src/scripts/daily_analysis.py

#### GitHub Actions Workflow

- [x] T054 [US1] Create .github/workflows/daily-analysis.yml with scheduled job (cron: 0 22 * * 1-5)
- [x] T055 [US1] Add secrets configuration to workflow (TELEGRAM_TOKEN, LLM API keys)
- [x] T056 [US1] Add database commit step to workflow

#### CLI Commands for US1

- [x] T057 [P] [US1] Create src/stock_analyzer/cli.py with CLI entry point (using argparse or click)
- [x] T058 [P] [US1] Implement analyze command in src/stock_analyzer/cli.py
- [x] T059 [P] [US1] Implement analyze-batch command in src/stock_analyzer/cli.py
- [x] T060 [P] [US1] Implement run-daily-job command in src/stock_analyzer/cli.py
- [x] T061 [US1] Add --json flag support for all commands in src/stock_analyzer/cli.py

### Verification for User Story 1

- [x] T062 [US1] Run all US1 tests and verify they PASS (pytest -k US1)
- [x] T063 [US1] Manual test: Run daily job script locally with test data
- [x] T064 [US1] Manual test: Verify Telegram delivery to test user

**Checkpoint**: At this point, User Story 1 is fully functional - automated daily analysis and delivery works end-to-end

---

## Phase 4: User Story 2 - Stock Subscription Management (Priority: P2)

**Goal**: Allow users to subscribe/unsubscribe to stocks via Telegram bot commands

**Independent Test**: User sends /subscribe AAPL to bot, verify subscription added and appears in next analysis run

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T065 [P] [US2] Write contract test for Telegram bot commands in tests/contract/test_telegram_contract.py
- [x] T066 [P] [US2] Write unit tests for subscription management in tests/unit/test_subscriptions.py
- [x] T067 [P] [US2] Write integration test for Telegram bot workflow in tests/integration/test_telegram_integration.py
- [x] T068 [US2] Verify all US2 tests FAIL (run pytest -k US2)

### Implementation for User Story 2

#### Subscription Management

- [x] T069 [P] [US2] Add add_subscription() method to src/stock_analyzer/storage.py
- [x] T070 [P] [US2] Add remove_subscription() method to src/stock_analyzer/storage.py
- [x] T071 [P] [US2] Add get_subscriptions() method to src/stock_analyzer/storage.py (with filters)
- [x] T072 [US2] Add subscription limit validation (10 per user, 100 total) in src/stock_analyzer/storage.py

#### Telegram Bot

- [x] T073 [US2] Create src/stock_analyzer/bot.py with bot initialization (python-telegram-bot Application)
- [x] T074 [P] [US2] Implement /start command handler in src/stock_analyzer/bot.py
- [x] T075 [P] [US2] Implement /help command handler in src/stock_analyzer/bot.py
- [x] T076 [US2] Implement /subscribe <symbol> command handler in src/stock_analyzer/bot.py
- [x] T077 [US2] Implement /unsubscribe <symbol> command handler in src/stock_analyzer/bot.py
- [x] T078 [US2] Implement /list command handler in src/stock_analyzer/bot.py
- [x] T079 [US2] Add symbol validation before subscription in src/stock_analyzer/bot.py
- [x] T080 [US2] Add error messages for limits and invalid symbols in src/stock_analyzer/bot.py

#### CLI Commands for US2

- [x] T081 [P] [US2] Implement subscribe command in src/stock_analyzer/cli.py
- [x] T082 [P] [US2] Implement unsubscribe command in src/stock_analyzer/cli.py
- [x] T083 [P] [US2] Implement list-subscriptions command in src/stock_analyzer/cli.py
- [x] T084 [P] [US2] Implement validate command in src/stock_analyzer/cli.py

#### Bot Deployment

- [x] T085 [US2] Create .github/workflows/telegram-bot.yml for bot deployment (optional: runs continuously or webhook)
- [x] T086 [US2] Add bot startup script for local development in src/scripts/run_bot.py

### Verification for User Story 2

- [x] T087 [US2] Run all US2 tests and verify they PASS (pytest -k US2)
- [x] T088 [US2] Manual test: Subscribe to AAPL via Telegram, verify in database
- [x] T089 [US2] Manual test: Unsubscribe from AAPL via Telegram, verify removed
- [x] T090 [US2] Manual test: Try subscribing to 11th stock, verify error

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently - users can manage subscriptions and receive daily insights

---

## Phase 5: User Story 3 - Historical Insight Access (Priority: P3)

**Goal**: Query and view historical insights for tracked stocks

**Independent Test**: Run analyses for multiple days, query history via CLI or bot, verify correct data returned

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T091 [P] [US3] Write contract test for history query API in tests/contract/test_history_contract.py
- [x] T092 [P] [US3] Write unit tests for historical queries in tests/unit/test_storage_history.py
- [x] T093 [US3] Verify all US3 tests FAIL (run pytest -k US3)

### Implementation for User Story 3

#### Historical Query Logic

- [x] T094 [P] [US3] Add get_insights() method to src/stock_analyzer/storage.py (with date range filters)
- [x] T095 [P] [US3] Add query optimization (indexes already defined in init_database) in src/stock_analyzer/storage.py
- [x] T096 [US3] Add pagination support to get_insights() in src/stock_analyzer/storage.py

#### CLI Commands for US3

- [x] T097 [P] [US3] Implement history command in src/stock_analyzer/cli.py
- [x] T098 [US3] Add --start, --end, --limit flags to history command in src/stock_analyzer/cli.py
- [x] T099 [US3] Add table output formatting for history command in src/stock_analyzer/cli.py

#### Telegram Bot Commands for US3

- [x] T100 [P] [US3] Implement /history <symbol> command handler in src/stock_analyzer/bot.py
- [x] T101 [US3] Implement /history <symbol> <days> command handler in src/stock_analyzer/bot.py
- [x] T102 [US3] Add inline buttons for "Load More" in bot history responses in src/stock_analyzer/bot.py
- [x] T103 [US3] Format historical insights for Telegram display in src/stock_analyzer/bot.py

### Verification for User Story 3

- [x] T104 [US3] Run all US3 tests and verify they PASS (pytest -k US3)
- [x] T105 [US3] Manual test: Query AAPL history for last 7 days via CLI
- [x] T106 [US3] Manual test: Query AAPL history via Telegram bot
- [x] T107 [US3] Manual test: Verify date filtering works correctly

**Checkpoint**: All user stories now complete and independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, documentation, and quality

### Additional CLI Commands

- [x] T108 [P] Implement stats command in src/stock_analyzer/cli.py (system statistics)
- [x] T109 [P] Implement deliver command in src/stock_analyzer/cli.py (manual delivery trigger)
- [x] T110 [P] Implement init-db command in src/stock_analyzer/cli.py (initialize database)

### Telegram Bot Enhancements

- [x] T111 [P] Implement /analyze <symbol> command in src/stock_analyzer/bot.py (on-demand analysis)
- [x] T112 [P] Implement /stats command in src/stock_analyzer/bot.py
- [x] T113 [P] Implement /about command in src/stock_analyzer/bot.py

### Error Handling & Logging

- [ ] T114 Add comprehensive error handling to all API calls in src/stock_analyzer/fetcher.py
- [x] T115 Add structured logging throughout application (using Python logging module)
- [x] T116 Add rate limit handling with exponential backoff in src/stock_analyzer/fetcher.py and src/stock_analyzer/llm_client.py

### Testing & Quality

- [ ] T117 [P] Add unit tests for all uncovered utility functions in tests/unit/
- [ ] T118 [P] Add mock classes for testing in src/stock_analyzer/testing.py
- [x] T119 Run full test suite and achieve >80% coverage (pytest --cov=stock_analyzer)
- [x] T120 Add CI workflow for running tests in .github/workflows/test.yml

### Documentation

- [x] T121 [P] Update README.md with complete usage examples
- [x] T122 [P] Add docstrings to all public methods (following Google style)
- [x] T123 [P] Create CONTRIBUTING.md with development guidelines
- [ ] T124 Verify quickstart.md is accurate and up-to-date

### Configuration & Deployment

- [x] T125 Create pyproject.toml console_scripts entry point for CLI
- [x] T126 Test installation with uv pip install -e .
- [ ] T127 Create example config file at config.example.toml
- [x] T128 Document all environment variables in .env.example

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - User Story 1 (MVP): Can start after Foundational - No dependencies on other stories
  - User Story 2: Can start after Foundational - Integrates with US1 but independently testable
  - User Story 3: Can start after Foundational - Depends on US1 data but independently testable
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories (can be MVP)
- **User Story 2 (P2)**: No blocking dependencies, but naturally extends US1 (users need subscriptions to receive insights)
- **User Story 3 (P3)**: Requires US1 to have generated some insights for testing, but implementation is independent

### Within Each User Story

**Test-First Workflow (NON-NEGOTIABLE)**:
1. Write tests FIRST
2. Verify tests FAIL
3. Implement functionality
4. Verify tests PASS
5. Refactor if needed (Red-Green-Refactor)

**Implementation Order**:
- Tests → Models → Storage → Services → CLI/Bot → Integration → Verification

### Parallel Opportunities

**Setup Phase**:
- T003, T004, T005, T006, T007 (all marked [P]) can run in parallel

**Foundational Phase**:
- T011 (models) can run in parallel with T008-T010 (config/exceptions)
- T020, T021, T022 (LLM client implementations) can run in parallel after T019
- Integration tests T032, T033 can run in parallel after their respective units complete

**User Story 1**:
- T035, T036, T037 (all test files) can run in parallel
- T039, T045, T050, T057 (different modules) can start in parallel after foundation
- T058, T059, T060 (different CLI commands) can run in parallel

**User Story 2**:
- T065, T066, T067 (test files) can run in parallel
- T069, T070, T071 (storage methods) can run in parallel
- T074, T075 (bot command handlers) can run in parallel
- T081, T082, T083, T084 (CLI commands) can run in parallel

**User Story 3**:
- T091, T092 (test files) can run in parallel
- T094, T095 (storage query methods) can run in parallel
- T097, T100, T101 (CLI/bot commands) can run in parallel

**Polish Phase**:
- T108, T109, T110 (CLI commands) can run in parallel
- T111, T112, T113 (bot commands) can run in parallel
- T117, T118, T121, T122, T123 (independent documentation/test tasks) can run in parallel

---

## Parallel Example: User Story 1

After Foundational phase completes, launch these tasks together:

```bash
# Test writing (all parallel)
Task T035: Contract test for Analyzer
Task T036: Contract test for CLI
Task T037: Integration test end-to-end

# After tests fail, core modules (parallel)
Task T039: analyzer.py module
Task T045: deliverer.py module
Task T050: daily_analysis.py script
Task T057: cli.py entry point
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T034) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T035-T064)
4. **STOP and VALIDATE**: Run daily analysis job, verify insight delivery
5. Deploy MVP (GitHub Actions workflow active)

**Timeline**: ~2-3 weeks for fully functional MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~1 week)
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!** ~1 week)
3. Add User Story 2 → Test independently → Deploy/Demo (~3-5 days)
4. Add User Story 3 → Test independently → Deploy/Demo (~2-3 days)
5. Polish phase → Final release (~2-3 days)

Each story adds value without breaking previous stories.

**Total Timeline**: 4-6 weeks for full feature set

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~1 week)
2. Once Foundational is done:
   - Developer A: User Story 1 (T035-T064)
   - Developer B: User Story 2 (T065-T090)
   - Developer C: User Story 3 (T091-T107)
3. Stories complete and integrate independently
4. Team converges on Polish phase

**Timeline**: 2-3 weeks total with 3 developers

---

## Notes

- **[P]** tasks = different files, no dependencies on incomplete work
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **Test-First is NON-NEGOTIABLE**: Always write tests, verify they fail, then implement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are exact - ready for implementation
- Database schema defined in data-model.md, implemented in T015

**Total Tasks**: 128 tasks
- Setup: 7 tasks
- Foundational: 27 tasks
- User Story 1: 30 tasks
- User Story 2: 26 tasks
- User Story 3: 17 tasks
- Polish: 21 tasks

**Parallel Opportunities**: 47 tasks marked [P]
**Test Tasks**: 22 explicit test-writing tasks (per TDD workflow)
