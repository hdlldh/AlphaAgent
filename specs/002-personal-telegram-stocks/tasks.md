# Tasks: Personal Stock Monitor with Telegram Channel

**Input**: Design documents from `/specs/002-personal-telegram-stocks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included - This project follows TDD workflow per constitution requirement III

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single Python project structure:
- Source code: `src/stock_analyzer/`
- Tests: `tests/contract/`, `tests/integration/`, `tests/unit/`
- Scripts: `src/scripts/`
- Workflows: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment and configuration updates for personal use

- [X] T001 [P] Update .env.example to add STOCK_ANALYZER_STOCK_LIST environment variable
- [X] T002 [P] Update .env.example to add STOCK_ANALYZER_TELEGRAM_CHANNEL environment variable
- [X] T003 [P] Update .github/workflows/daily-analysis.yml to use STOCK_LIST and TELEGRAM_CHANNEL secrets
- [X] T004 Remove .github/workflows/telegram-bot.yml (no longer needed for personal use)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema migration and core infrastructure changes that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Migration

- [X] T005 Update storage.py init_database() to drop users table in src/stock_analyzer/storage.py
- [X] T006 Update storage.py init_database() to drop subscriptions table in src/stock_analyzer/storage.py
- [X] T007 Update storage.py init_database() to modify insights table schema (remove analysis_id FK, remove user_id) in src/stock_analyzer/storage.py
- [X] T008 Update storage.py init_database() to modify delivery_logs table schema (replace user_id with channel_id) in src/stock_analyzer/storage.py
- [ ] T009 [P] Test database migration with init_database() to verify users and subscriptions tables removed

### Model Updates

- [X] T010 [P] Remove User dataclass from src/stock_analyzer/models.py
- [X] T011 [P] Remove Subscription dataclass from src/stock_analyzer/models.py
- [X] T012 [P] Update Insight dataclass to remove user_id and analysis_id fields in src/stock_analyzer/models.py
- [X] T013 [P] Update DeliveryLog dataclass to replace user_id with channel_id field in src/stock_analyzer/models.py

### Storage Interface Updates

- [X] T014 [P] Remove create_user() method from src/stock_analyzer/storage.py
- [X] T015 [P] Remove get_user() method from src/stock_analyzer/storage.py
- [X] T016 [P] Remove update_user_activity() method from src/stock_analyzer/storage.py
- [X] T017 [P] Remove create_subscription() method from src/stock_analyzer/storage.py
- [X] T018 [P] Remove delete_subscription() method from src/stock_analyzer/storage.py
- [X] T019 [P] Remove get_subscriptions() method from src/stock_analyzer/storage.py
- [X] T020 [P] Remove count_user_subscriptions() method from src/stock_analyzer/storage.py
- [X] T021 [P] Remove count_system_subscriptions() method from src/stock_analyzer/storage.py
- [X] T022 Update create_insight() to remove user_id parameter in src/stock_analyzer/storage.py
- [X] T023 Update get_insights() to remove user_id parameter and filtering in src/stock_analyzer/storage.py
- [X] T024 Update create_delivery_log() to replace user_id with channel_id parameter in src/stock_analyzer/storage.py

### Bot Removal

- [X] T025 Delete src/stock_analyzer/bot.py (interactive bot no longer needed)
- [X] T026 Delete src/scripts/run_bot.py (bot startup script no longer needed)
- [X] T027 Delete tests/unit/test_subscriptions.py (subscription tests no longer relevant)

**Checkpoint**: Foundation ready - database migrated, models updated, storage interface simplified. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Configure and Analyze Personal Stock List (Priority: P1) 🎯 MVP

**Goal**: Enable personal stock monitoring via environment variables without user management overhead

**Independent Test**: Set STOCK_ANALYZER_STOCK_LIST="AAPL,MSFT,GOOGL", run daily job, verify insights generated for all three stocks

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T028 [P] [US1] Contract test for config.get_stock_symbols() parsing in tests/contract/test_config_contract.py
- [X] T029 [P] [US1] Contract test for config validation (empty stock list error) in tests/contract/test_config_contract.py
- [X] T030 [P] [US1] Unit test for stock list parsing with whitespace and duplicates in tests/unit/test_config.py
- [X] T031 [P] [US1] Unit test for stock list parsing with invalid formatting in tests/unit/test_config.py
- [X] T032 [P] [US1] Unit test for stock symbol validation in tests/unit/test_config.py
- [X] T033 [P] [US1] Integration test for daily job reading stock list from env in tests/integration/test_end_to_end.py
- [X] T034 [P] [US1] Integration test for daily job handling invalid symbols in tests/integration/test_end_to_end.py

### Implementation for User Story 1

#### Configuration Updates

- [X] T035 [P] [US1] Add stock_list field to Config dataclass in src/stock_analyzer/config.py
- [X] T036 [P] [US1] Add telegram_channel field to Config dataclass in src/stock_analyzer/config.py
- [X] T037 [US1] Implement get_stock_symbols() method to parse and validate stock list in src/stock_analyzer/config.py
- [X] T038 [US1] Update Config.from_env() to read STOCK_ANALYZER_STOCK_LIST in src/stock_analyzer/config.py
- [X] T039 [US1] Update Config.from_env() to read STOCK_ANALYZER_TELEGRAM_CHANNEL in src/stock_analyzer/config.py
- [X] T040 [US1] Update Config.validate() to require stock_list and telegram_channel in src/stock_analyzer/config.py

#### Daily Analysis Workflow Updates

- [X] T041 [US1] Update daily_analysis.py to read stock list from config.get_stock_symbols() instead of querying subscriptions in src/scripts/daily_analysis.py
- [X] T042 [US1] Update daily_analysis.py to remove subscription query logic in src/scripts/daily_analysis.py
- [X] T043 [US1] Update daily_analysis.py to handle empty stock list with clear error message in src/scripts/daily_analysis.py
- [X] T044 [US1] Update daily_analysis.py to deduplicate stock symbols before analysis in src/scripts/daily_analysis.py
- [X] T045 [US1] Add validation logging for invalid stock symbols in src/scripts/daily_analysis.py

#### CLI Updates for User Story 1

- [X] T046 [P] [US1] Remove subscribe command from CLI in src/stock_analyzer/cli.py
- [X] T047 [P] [US1] Remove unsubscribe command from CLI in src/stock_analyzer/cli.py
- [X] T048 [P] [US1] Remove list-subscriptions command from CLI in src/stock_analyzer/cli.py
- [X] T049 [US1] Update run-daily-job command to use config stock list in src/stock_analyzer/cli.py
- [X] T050 [US1] Add dry-run flag to run-daily-job for testing stock list in src/stock_analyzer/cli.py
- [X] T051 [US1] Update run-daily-job error handling for empty stock list in src/stock_analyzer/cli.py

#### Test Updates for User Story 1

- [X] T052 [P] [US1] Remove subscription command tests from tests/contract/test_cli_contract.py
- [X] T053 [P] [US1] Update run-daily-job test to use env stock list in tests/contract/test_cli_contract.py
- [X] T054 [P] [US1] Remove user/subscription tests from tests/contract/test_storage_contract.py
- [X] T055 [P] [US1] Remove user/subscription tests from tests/unit/test_storage.py

**Checkpoint**: At this point, User Story 1 should be fully functional - stock list can be configured via environment variable and daily analysis runs without subscriptions

---

## Phase 4: User Story 2 - Receive Insights via Telegram Channel (Priority: P2)

**Goal**: Post analysis insights to single Telegram channel instead of individual users

**Independent Test**: Run analysis with configured channel ID, verify messages posted to channel with proper formatting

### Tests for User Story 2

- [X] T056 [P] [US2] Contract test for deliver_to_channel() method in tests/contract/test_deliverer_contract.py
- [X] T057 [P] [US2] Contract test for channel posting with invalid channel ID in tests/contract/test_deliverer_contract.py
- [X] T058 [P] [US2] Unit test for format_insight() with channel formatting in tests/unit/test_deliverer.py
- [X] T059 [P] [US2] Unit test for channel posting with rate limit retry in tests/unit/test_deliverer.py
- [X] T060 [P] [US2] Integration test for end-to-end channel delivery in tests/integration/test_telegram_integration.py
- [X] T061 [P] [US2] Integration test for delivery error handling in tests/integration/test_telegram_integration.py

### Implementation for User Story 2

#### Deliverer Updates

- [X] T062 [US2] Add deliver_to_channel() method to InsightDeliverer in src/stock_analyzer/deliverer.py
- [X] T063 [US2] Remove deliver_to_subscribers() method from InsightDeliverer in src/stock_analyzer/deliverer.py
- [X] T064 [US2] Update DeliveryResult dataclass to use channel_id instead of user_id in src/stock_analyzer/deliverer.py
- [X] T065 [US2] Remove BatchDeliveryResult dataclass (no longer needed for single channel) in src/stock_analyzer/deliverer.py
- [X] T066 [US2] Update TelegramChannel.send() documentation to clarify channel ID support in src/stock_analyzer/deliverer.py
- [X] T067 [US2] Add channel permission error handling in deliver_to_channel() in src/stock_analyzer/deliverer.py
- [X] T068 [US2] Add message length truncation for Telegram 4096 char limit in format_insight() in src/stock_analyzer/deliverer.py

#### Daily Analysis Integration

- [X] T069 [US2] Update daily_analysis.py to use deliver_to_channel() instead of deliver_to_subscribers() in src/scripts/daily_analysis.py
- [X] T070 [US2] Update daily_analysis.py to pass config.telegram_channel to deliverer in src/scripts/daily_analysis.py
- [X] T071 [US2] Update daily_analysis.py delivery logging for single channel in src/scripts/daily_analysis.py
- [X] T072 [US2] Update daily_analysis.py to handle channel delivery failures gracefully in src/scripts/daily_analysis.py

#### Test Updates for User Story 2

- [X] T073 [P] [US2] Add channel posting tests to tests/contract/test_deliverer_contract.py
- [X] T074 [P] [US2] Add channel error handling tests to tests/unit/test_deliverer.py
- [X] T075 [P] [US2] Update telegram integration tests for channel delivery in tests/integration/test_telegram_integration.py
- [X] T076 [P] [US2] Remove multi-user delivery tests from tests/integration/test_telegram_integration.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - analysis runs from stock list and posts to channel

---

## Phase 5: User Story 3 - View Historical Analysis Data (Priority: P3)

**Goal**: Query historical insights via CLI without user filtering

**Independent Test**: Store multiple days of analysis data, run `cli history AAPL`, verify all historical insights displayed

### Tests for User Story 3

- [X] T077 [P] [US3] Contract test for history command without user_id in tests/contract/test_cli_contract.py
- [X] T078 [P] [US3] Contract test for history command with date range filtering in tests/contract/test_cli_contract.py
- [X] T079 [P] [US3] Unit test for get_insights() without user filtering in tests/unit/test_storage.py
- [X] T080 [P] [US3] Unit test for history command pagination in tests/unit/test_storage.py
- [X] T081 [P] [US3] Integration test for historical query workflow in tests/integration/test_end_to_end.py

### Implementation for User Story 3

#### CLI History Command Updates

- [X] T082 [US3] Update history command to remove user_id filtering in src/stock_analyzer/cli.py
- [X] T083 [US3] Update history command to query all insights by stock symbol in src/stock_analyzer/cli.py
- [X] T084 [US3] Update history command output format for personal use in src/stock_analyzer/cli.py
- [X] T085 [US3] Verify history command date range filtering still works in src/stock_analyzer/cli.py
- [X] T086 [US3] Verify history command pagination (limit/offset) still works in src/stock_analyzer/cli.py

#### Test Updates for User Story 3

- [X] T087 [P] [US3] Update history contract tests to verify no user filtering in tests/contract/test_cli_contract.py
- [X] T088 [P] [US3] Add test for empty history results in tests/contract/test_cli_contract.py
- [X] T089 [P] [US3] Update storage tests for get_insights() without user_id in tests/unit/test_storage.py

**Checkpoint**: All user stories should now be independently functional - configure stock list, analyze and post to channel, query historical data

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, cleanup, and documentation

### Documentation

- [X] T090 [P] Update README.md to reflect personal use (remove multi-user instructions)
- [X] T091 [P] Update README.md to add stock list and channel ID configuration
- [X] T092 [P] Update README.md to remove subscription management commands
- [X] T093 [P] Update README.md to add quickstart section for personal setup
- [X] T094 [P] Create migration guide in docs/ for upgrading from multi-user version

### Code Cleanup

- [X] T095 [P] Remove any remaining references to User or Subscription models in codebase
- [X] T096 [P] Remove subscription-related imports from all files
- [X] T097 [P] Update docstrings to reflect personal use (no user_id parameters)
- [X] T098 [P] Run linting checks with ruff check . and fix any issues
- [X] T099 [P] Verify all tests pass with pytest

### Final Validation

- [ ] T100 Run full test suite to verify all user stories work independently
- [ ] T101 Manual test: Set up stock list and channel, run daily job end-to-end
- [ ] T102 Manual test: Verify historical queries work for multiple stocks
- [ ] T103 Manual test: Test error handling with invalid stock symbols
- [ ] T104 Manual test: Test error handling with invalid channel ID
- [X] T105 Update CLAUDE.md with any new technologies or patterns (if needed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Configuration changes before workflow updates
- Storage/model changes before service/CLI changes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: All 4 tasks can run in parallel (different files)

**Phase 2 (Foundational)**:
- Database migration tasks (T005-T009) are sequential
- Model updates (T010-T013) can run in parallel after schema migration
- Storage method removals (T014-T024) can run in parallel after model updates
- Bot removal (T025-T027) can run in parallel with other Phase 2 tasks

**Phase 3 (User Story 1)**:
- All test tasks (T028-T034) can run in parallel
- Config field additions (T035-T036) can run in parallel
- CLI command removals (T046-T048) can run in parallel
- Test update tasks (T052-T055) can run in parallel

**Phase 4 (User Story 2)**:
- All test tasks (T056-T061) can run in parallel
- Test update tasks (T073-T076) can run in parallel

**Phase 5 (User Story 3)**:
- All test tasks (T077-T081) can run in parallel
- Test update tasks (T087-T089) can run in parallel

**Phase 6 (Polish)**:
- All documentation tasks (T090-T094) can run in parallel
- All code cleanup tasks (T095-T099) can run in parallel

Once Foundational phase completes, all user stories (Phase 3-5) can start in parallel if team capacity allows.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for config.get_stock_symbols() parsing in tests/contract/test_config_contract.py"
Task: "Contract test for config validation (empty stock list error) in tests/contract/test_config_contract.py"
Task: "Unit test for stock list parsing with whitespace and duplicates in tests/unit/test_config.py"
Task: "Unit test for stock list parsing with invalid formatting in tests/unit/test_config.py"
Task: "Unit test for stock symbol validation in tests/unit/test_config.py"
Task: "Integration test for daily job reading stock list from env in tests/integration/test_end_to_end.py"
Task: "Integration test for daily job handling invalid symbols in tests/integration/test_end_to_end.py"

# Launch config field additions together:
Task: "Add stock_list field to Config dataclass in src/stock_analyzer/config.py"
Task: "Add telegram_channel field to Config dataclass in src/stock_analyzer/config.py"

# Launch CLI command removals together:
Task: "Remove subscribe command from CLI in src/stock_analyzer/cli.py"
Task: "Remove unsubscribe command from CLI in src/stock_analyzer/cli.py"
Task: "Remove list-subscriptions command from CLI in src/stock_analyzer/cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (23 tasks) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (28 tasks)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Set STOCK_ANALYZER_STOCK_LIST="AAPL,MSFT,GOOGL"
   - Run daily job
   - Verify insights generated
5. Deploy/demo if ready

**MVP Milestone**: Personal stock monitoring via environment variables without multi-user complexity (Stock list configuration working)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (27 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! - 28 tasks)
3. Add User Story 2 → Test independently → Deploy/Demo (21 tasks)
4. Add User Story 3 → Test independently → Deploy/Demo (13 tasks)
5. Add Polish → Final release (16 tasks)

**Total**: 105 tasks

Each story adds value without breaking previous stories:
- After US1: Stock list configuration works
- After US2: Telegram channel delivery works
- After US3: Historical queries work
- After Polish: Production-ready personal stock monitor

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together - 4 tasks
2. Team completes Foundational (Phase 2) together - 23 tasks (many can be parallel)
3. Once Foundational is done:
   - Developer A: User Story 1 (28 tasks)
   - Developer B: User Story 2 (21 tasks)
   - Developer C: User Story 3 (13 tasks)
4. Stories complete and integrate independently
5. Team completes Polish together - 16 tasks

**Time Estimate** (single developer, TDD):
- Phase 1: 1 hour
- Phase 2: 1 day (database migration critical)
- Phase 3 (US1): 1 day (core functionality)
- Phase 4 (US2): 0.5 day (delivery mechanism)
- Phase 5 (US3): 0.5 day (historical queries)
- Phase 6: 0.5 day (polish)
- **Total**: 3-4 days for complete refactoring

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD Required**: Tests MUST fail before implementing (constitution principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Database migration (Phase 2) is the critical blocking phase - prioritize carefully
- User Story 1 is the MVP - can deploy after US1 completion
- User Story 2 adds delivery - can deploy after US2 completion
- User Story 3 adds historical queries - optional enhancement
- Total tasks: 105 (27 foundation, 28 US1, 21 US2, 13 US3, 16 polish)
- Parallel opportunities: ~40% of tasks marked [P] (42 tasks can run in parallel within their phase)
