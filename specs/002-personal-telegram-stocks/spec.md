# Feature Specification: Personal Stock Monitor with Telegram Channel

**Feature Branch**: `002-personal-telegram-stocks`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "refactor this repo: 1. remove multi user support. This app is for personal use. 2. allow to specify the stock list in the env variables and check the stocks in the stock list and send results to telegram channel."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure and Analyze Personal Stock List (Priority: P1)

The personal user configures their stock watchlist via environment variables and runs automated daily analysis without any user management overhead.

**Why this priority**: This is the core functionality - enabling personal stock monitoring without multi-user complexity. It's the minimum viable feature that delivers value.

**Independent Test**: Can be fully tested by setting environment variables with stock symbols, running the analysis job, and verifying insights are generated for all configured stocks.

**Acceptance Scenarios**:

1. **Given** the environment variable `STOCK_ANALYZER_STOCK_LIST` is set to "AAPL,MSFT,GOOGL", **When** the daily analysis job runs, **Then** insights are generated for AAPL, MSFT, and GOOGL.
2. **Given** the stock list contains an invalid symbol like "INVALID", **When** the analysis job runs, **Then** the system logs a warning for the invalid symbol and continues processing valid symbols.
3. **Given** no stock list is configured, **When** the analysis job runs, **Then** the system exits gracefully with a clear error message indicating the stock list must be configured.
4. **Given** the stock list is empty (blank string), **When** the analysis job runs, **Then** the system exits gracefully with a clear error message.

---

### User Story 2 - Receive Insights via Telegram Channel (Priority: P2)

The personal user receives all stock analysis insights posted to a single Telegram channel instead of individual user messages.

**Why this priority**: Delivers the automated notification mechanism for personal use. Depends on P1 (analysis must run first) but is independently testable.

**Independent Test**: Can be fully tested by running analysis with a configured Telegram channel ID and verifying messages are posted to the channel with proper formatting.

**Acceptance Scenarios**:

1. **Given** analysis insights exist for AAPL, **When** the delivery process runs, **Then** the insight is posted to the configured Telegram channel.
2. **Given** multiple stocks have been analyzed, **When** the delivery process runs, **Then** each stock's insight is posted as a separate message to the channel in sequential order.
3. **Given** the Telegram channel ID is invalid or bot lacks permission, **When** delivery is attempted, **Then** the system logs an error with details and continues processing remaining insights.
4. **Given** a message exceeds Telegram's length limit, **When** delivery is attempted, **Then** the message is truncated with an indicator (e.g., "...") or split into multiple messages.

---

### User Story 3 - View Historical Analysis Data (Priority: P3)

The personal user can query and view historical stock analysis insights via the CLI without needing user-specific filtering.

**Why this priority**: Provides value for tracking trends over time but is not essential for daily monitoring. Can be implemented independently after P1 and P2.

**Independent Test**: Can be fully tested by storing multiple days of analysis data and using CLI commands to retrieve historical insights by stock symbol and date range.

**Acceptance Scenarios**:

1. **Given** historical insights exist for AAPL, **When** the user runs `cli history AAPL`, **Then** all historical insights for AAPL are displayed in chronological order.
2. **Given** insights exist for multiple stocks, **When** the user runs `cli history MSFT --start 2026-02-01 --end 2026-02-28`, **Then** only MSFT insights within the date range are displayed.
3. **Given** no insights exist for a stock, **When** the user queries history for that stock, **Then** a user-friendly message indicates no data is available.

---

### Edge Cases

- What happens when the stock list contains duplicate symbols (e.g., "AAPL,AAPL,MSFT")? System should deduplicate before processing.
- How does the system handle network failures during Telegram channel posting? System should retry with exponential backoff and log persistent failures.
- What happens if the environment variable contains invalid formatting (e.g., "AAPL, MSFT,,GOOGL" with extra commas or spaces)? System should sanitize input by trimming whitespace and removing empty entries.
- How does the system behave when the Telegram channel is deleted or bot is removed? System should fail gracefully with a clear error message and not crash.
- What happens if the LLM API fails during analysis? System should retry and log the failure, but not block analysis of other stocks.

## Requirements *(mandatory)*

### Functional Requirements

**Data Model Simplification:**
- **FR-001**: System MUST remove all user-related database tables (users, subscriptions)
- **FR-002**: System MUST remove user ID foreign key constraints from analyses and delivery logs
- **FR-003**: System MUST retain the analyses table for storing historical stock insights
- **FR-004**: System MUST retain the delivery_logs table for tracking Telegram channel deliveries

**Configuration:**
- **FR-005**: System MUST read stock list from environment variable `STOCK_ANALYZER_STOCK_LIST` (comma-separated symbols)
- **FR-006**: System MUST read Telegram channel ID from environment variable `STOCK_ANALYZER_TELEGRAM_CHANNEL` (format: @channelname or numeric ID)
- **FR-007**: System MUST validate and sanitize the stock list by trimming whitespace, removing duplicates, and filtering empty values
- **FR-008**: System MUST validate each stock symbol before analysis using existing validation logic

**Analysis Workflow:**
- **FR-009**: Daily analysis job MUST iterate over the configured stock list and analyze each symbol
- **FR-010**: System MUST skip invalid stock symbols with a warning log but continue processing remaining stocks
- **FR-011**: System MUST store analysis insights in the database without associating them with a user ID
- **FR-012**: Analysis results MUST include stock symbol, analysis text, timestamp, and LLM provider used

**Telegram Delivery:**
- **FR-013**: System MUST post analysis insights to the configured Telegram channel instead of sending to individual users
- **FR-014**: System MUST format messages with Markdown including stock symbol, date, and analysis text
- **FR-015**: System MUST handle Telegram API rate limits with retry logic and exponential backoff
- **FR-016**: System MUST log successful and failed deliveries in the delivery_logs table without user ID references

**CLI Simplification:**
- **FR-017**: System MUST remove user management commands (subscribe, unsubscribe, list-subscriptions)
- **FR-018**: System MUST retain analyze, history, and init-db commands
- **FR-019**: System MUST update the `run-daily-job` command to use the environment-configured stock list
- **FR-020**: History command MUST query analyses without requiring a user ID filter

**Bot Removal:**
- **FR-021**: System MUST remove or disable the Telegram bot interactive commands (/start, /subscribe, /analyze, etc.)
- **FR-022**: System MUST remove bot-related workflows and scripts if no longer needed for channel posting

### Key Entities

- **Stock List**: Environment-configured list of stock symbols (tickers) to monitor daily. Comma-separated string, validated and deduplicated at runtime.
- **Analysis**: Historical record of stock analysis including symbol, insight text, timestamp, and LLM provider. No longer associated with specific users.
- **Delivery Log**: Record of Telegram channel posts including timestamp, stock symbol, success/failure status, and error details if applicable.
- **Telegram Channel**: Single target destination for all stock insights. Identified by channel ID or username (e.g., @mystockchannel).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Personal user can configure up to 50 stocks via a single environment variable and run analysis without managing subscriptions
- **SC-002**: Daily analysis job completes for all configured stocks within 15 minutes (assuming 50 stocks max, 18 seconds per stock average)
- **SC-003**: 100% of successfully analyzed stocks result in a Telegram channel post within 5 minutes of analysis completion
- **SC-004**: System startup time is reduced by at least 30% compared to multi-user version due to simplified schema and removed authentication checks
- **SC-005**: Historical queries return results for any stock in under 2 seconds regardless of data volume (tested with 1000+ analysis records)
- **SC-006**: Zero crashes or unhandled exceptions when invalid stock symbols are included in the configured list
- **SC-007**: System successfully recovers from Telegram API failures and retries delivery at least 3 times before logging permanent failure

## Assumptions *(mandatory)*

1. **Single User Context**: The application will only be used by one person (the repository owner) and does not need any user authentication or authorization.
2. **Telegram Channel Setup**: The user has already created a Telegram channel and added the bot as an administrator with posting permissions.
3. **Environment Management**: The user is comfortable managing environment variables via `.env` files or GitHub Actions secrets.
4. **Backward Compatibility**: Historical data from the multi-user version (existing analyses) can be retained and queried without user context. No data migration script is needed.
5. **Stock List Size**: The personal user will monitor between 5-50 stocks typically, which is within reasonable LLM API cost limits (~$30-50/month for 50 stocks with Claude).
6. **Delivery Frequency**: Daily delivery frequency (once per day after market close) is sufficient; real-time or intraday updates are not required.
7. **Channel vs Group**: The user wants a Telegram **channel** (one-way broadcast) rather than a group (two-way discussion). Bot cannot read messages in channels by design.
8. **Error Notifications**: Failed deliveries will be logged to console/file logs only; no separate alerting mechanism (email, SMS) is needed for this personal use case.

## Out of Scope

The following are explicitly **NOT** included in this refactoring:

1. **User Authentication**: No login, registration, or user management features (being removed).
2. **Subscription Management**: No per-user stock subscriptions or limits (being removed).
3. **Interactive Bot Commands**: No two-way Telegram bot interaction like /subscribe, /analyze, /history via chat (being removed or disabled).
4. **Multi-Channel Support**: Only one Telegram channel is supported; no ability to configure multiple channels or groups.
5. **Web Dashboard**: No web interface for viewing stock insights; CLI and Telegram channel are the only interfaces.
6. **Portfolio Tracking**: No profit/loss calculations, cost basis tracking, or portfolio performance metrics.
7. **Price Alerts**: No real-time price monitoring or threshold-based notifications.
8. **Stock Filtering**: No ability to conditionally analyze stocks based on criteria (e.g., only analyze if price changed >5%); all configured stocks are analyzed daily.
9. **Custom Analysis Prompts**: LLM analysis prompt remains standardized; no per-stock customization.
10. **Multi-Tenancy**: No support for multiple users or personal instances; strictly single-user personal deployment.

## Dependencies

- **Existing Codebase**: Refactors the current multi-user AlphaAgent system (version 1.0.0 MVP).
- **Telegram Bot API**: Requires bot to have admin privileges in the target Telegram channel.
- **Environment Variables**: Relies on proper configuration of `STOCK_ANALYZER_STOCK_LIST` and `STOCK_ANALYZER_TELEGRAM_CHANNEL`.
- **Database Schema**: Requires database migration to drop user-related tables and remove foreign key constraints.
- **GitHub Actions**: Depends on updated workflow configuration to pass new environment variables (channel ID instead of bot token for interactive use).
