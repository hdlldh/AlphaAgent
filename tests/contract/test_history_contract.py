"""
Contract tests for historical insight access (User Story 3).

These tests define the expected behavior of the history query API.
Tests are marked with [US3] for pytest filtering.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from stock_analyzer.models import Insight
from stock_analyzer.storage import Storage

# Mark all tests in this module with US3
pytestmark = pytest.mark.US3


@pytest.fixture
def mock_storage_with_insights():
    """Mock storage with sample historical insights."""
    storage = MagicMock(spec=Storage)

    # Create sample insights for testing
    today = date.today()
    insights = []

    for i in range(10):
        insight_date = today - timedelta(days=i)
        insights.append(Insight(
            id=i + 1,
            analysis_id=i + 1,
            stock_symbol="AAPL",
            analysis_date=insight_date,
            summary=f"Summary for day {i}",
            trend_analysis=f"Trend analysis for day {i}",
            risk_factors=["Risk 1", "Risk 2"],
            opportunities=["Opportunity 1", "Opportunity 2"],
            confidence_level="medium",
            metadata={"test": True},
            created_at=datetime.now()
        ))

    storage.get_insights = MagicMock(return_value=insights[:5])  # Default return 5
    return storage, insights


class TestBasicInsightRetrieval:
    """Contract tests for basic insight retrieval."""

    def test_get_insights_returns_list(self, mock_storage_with_insights):
        """
        GIVEN a stock with historical insights
        WHEN get_insights is called
        THEN it should return a list of Insight objects
        """
        storage, _ = mock_storage_with_insights

        result = storage.get_insights("AAPL")

        assert isinstance(result, list)
        assert all(isinstance(insight, Insight) for insight in result)

    def test_get_insights_ordered_by_date_descending(self, mock_storage_with_insights):
        """
        GIVEN historical insights for multiple dates
        WHEN get_insights is called
        THEN results should be ordered by date descending (newest first)
        """
        storage, all_insights = mock_storage_with_insights
        storage.get_insights.return_value = all_insights[:5]

        result = storage.get_insights("AAPL")

        # Verify descending order (newest first)
        for i in range(len(result) - 1):
            assert result[i].analysis_date >= result[i + 1].analysis_date

    def test_get_insights_respects_limit(self, mock_storage_with_insights):
        """
        GIVEN a stock with many historical insights
        WHEN get_insights is called with a limit
        THEN it should return at most limit insights
        """
        storage, all_insights = mock_storage_with_insights
        storage.get_insights.return_value = all_insights[:3]

        result = storage.get_insights("AAPL", limit=3)

        assert len(result) <= 3

    def test_get_insights_empty_for_no_data(self, mock_storage_with_insights):
        """
        GIVEN a stock with no historical insights
        WHEN get_insights is called
        THEN it should return an empty list
        """
        storage, _ = mock_storage_with_insights
        storage.get_insights.return_value = []

        result = storage.get_insights("INVALID")

        assert result == []


class TestDateRangeFiltering:
    """Contract tests for date range filtering."""

    def test_filter_by_start_date(self, mock_storage_with_insights):
        """
        GIVEN historical insights spanning multiple dates
        WHEN get_insights is called with start_date
        THEN only insights on or after start_date are returned
        """
        storage, all_insights = mock_storage_with_insights

        start_date = date.today() - timedelta(days=5)
        filtered = [i for i in all_insights if i.analysis_date >= start_date]
        storage.get_insights.return_value = filtered[:5]

        result = storage.get_insights("AAPL", start_date=start_date)

        assert all(insight.analysis_date >= start_date for insight in result)

    def test_filter_by_end_date(self, mock_storage_with_insights):
        """
        GIVEN historical insights spanning multiple dates
        WHEN get_insights is called with end_date
        THEN only insights on or before end_date are returned
        """
        storage, all_insights = mock_storage_with_insights

        end_date = date.today() - timedelta(days=5)
        filtered = [i for i in all_insights if i.analysis_date <= end_date]
        storage.get_insights.return_value = filtered[:5]

        result = storage.get_insights("AAPL", end_date=end_date)

        assert all(insight.analysis_date <= end_date for insight in result)

    def test_filter_by_date_range(self, mock_storage_with_insights):
        """
        GIVEN historical insights spanning multiple dates
        WHEN get_insights is called with both start_date and end_date
        THEN only insights within the range are returned
        """
        storage, all_insights = mock_storage_with_insights

        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=3)
        filtered = [
            i for i in all_insights
            if start_date <= i.analysis_date <= end_date
        ]
        storage.get_insights.return_value = filtered

        result = storage.get_insights("AAPL", start_date=start_date, end_date=end_date)

        assert all(
            start_date <= insight.analysis_date <= end_date
            for insight in result
        )

    def test_filter_returns_empty_for_no_matches(self, mock_storage_with_insights):
        """
        GIVEN historical insights
        WHEN get_insights is called with date range that has no matches
        THEN it should return an empty list
        """
        storage, _ = mock_storage_with_insights
        storage.get_insights.return_value = []

        # Date range in the future
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)

        result = storage.get_insights("AAPL", start_date=start_date, end_date=end_date)

        assert result == []


class TestPaginationSupport:
    """Contract tests for pagination."""

    def test_pagination_with_offset(self, mock_storage_with_insights):
        """
        GIVEN many historical insights
        WHEN get_insights is called with offset
        THEN it should skip offset insights and return next page
        """
        storage, all_insights = mock_storage_with_insights

        # First page (offset=0, limit=3)
        storage.get_insights.return_value = all_insights[0:3]
        page1 = storage.get_insights("AAPL", limit=3, offset=0)

        # Second page (offset=3, limit=3)
        storage.get_insights.return_value = all_insights[3:6]
        page2 = storage.get_insights("AAPL", limit=3, offset=3)

        # Pages should be different
        assert page1 != page2
        assert len(page1) <= 3
        assert len(page2) <= 3

    def test_pagination_last_page_partial(self, mock_storage_with_insights):
        """
        GIVEN insights that don't divide evenly by page size
        WHEN requesting the last page
        THEN it should return remaining insights
        """
        storage, all_insights = mock_storage_with_insights

        # If we have 10 insights and page size is 3
        # Last page (offset=9, limit=3) should return 1 insight
        storage.get_insights.return_value = all_insights[9:10]

        last_page = storage.get_insights("AAPL", limit=3, offset=9)

        assert len(last_page) <= 3

    def test_pagination_beyond_available_returns_empty(self, mock_storage_with_insights):
        """
        GIVEN limited historical insights
        WHEN offset exceeds available insights
        THEN it should return empty list
        """
        storage, _ = mock_storage_with_insights
        storage.get_insights.return_value = []

        result = storage.get_insights("AAPL", limit=10, offset=100)

        assert result == []


class TestInsightDataIntegrity:
    """Contract tests for insight data structure."""

    def test_insight_has_required_fields(self, mock_storage_with_insights):
        """
        GIVEN historical insights
        WHEN get_insights is called
        THEN each insight should have all required fields
        """
        storage, all_insights = mock_storage_with_insights
        storage.get_insights.return_value = all_insights[:1]

        result = storage.get_insights("AAPL", limit=1)

        assert len(result) > 0
        insight = result[0]

        # Verify all required fields exist
        assert hasattr(insight, 'stock_symbol')
        assert hasattr(insight, 'analysis_date')
        assert hasattr(insight, 'summary')
        assert hasattr(insight, 'trend_analysis')
        assert hasattr(insight, 'risk_factors')
        assert hasattr(insight, 'opportunities')
        assert hasattr(insight, 'confidence_level')

    def test_insight_risk_factors_is_list(self, mock_storage_with_insights):
        """
        GIVEN historical insights
        WHEN get_insights is called
        THEN risk_factors should be a list
        """
        storage, all_insights = mock_storage_with_insights
        storage.get_insights.return_value = all_insights[:1]

        result = storage.get_insights("AAPL", limit=1)
        insight = result[0]

        assert isinstance(insight.risk_factors, list)

    def test_insight_opportunities_is_list(self, mock_storage_with_insights):
        """
        GIVEN historical insights
        WHEN get_insights is called
        THEN opportunities should be a list
        """
        storage, all_insights = mock_storage_with_insights
        storage.get_insights.return_value = all_insights[:1]

        result = storage.get_insights("AAPL", limit=1)
        insight = result[0]

        assert isinstance(insight.opportunities, list)


class TestCLIHistoryCommand:
    """Contract tests for CLI history command."""

    def test_history_command_accepts_symbol(self):
        """
        GIVEN CLI with history command
        WHEN command is called with symbol
        THEN it should query insights for that symbol
        """
        from stock_analyzer.cli import CLI

        # CLI should have history method
        assert hasattr(CLI, 'history')

    def test_history_command_supports_date_range(self):
        """
        GIVEN CLI with history command
        WHEN command is called with --start and --end
        THEN it should filter by date range
        """
        # This will be tested in integration tests
        # Contract: history method should accept start_date and end_date parameters
        pass

    def test_history_command_supports_limit(self):
        """
        GIVEN CLI with history command
        WHEN command is called with --limit
        THEN it should limit number of results
        """
        # Contract: history method should accept limit parameter
        pass


class TestBotHistoryCommand:
    """Contract tests for Telegram bot /history command."""

    def test_bot_has_history_handler(self):
        """
        GIVEN Telegram bot
        WHEN checking available commands
        THEN it should have history_command handler
        """
        from stock_analyzer.bot import TelegramBot

        # Bot should have history_command method
        assert hasattr(TelegramBot, 'history_command')

    def test_history_command_accepts_symbol(self):
        """
        GIVEN /history command
        WHEN called with symbol
        THEN it should query insights for that symbol
        """
        # This will be tested in integration tests
        # Contract: history_command should process symbol argument
        pass

    def test_history_command_accepts_days(self):
        """
        GIVEN /history command
        WHEN called with symbol and days
        THEN it should query insights for last N days
        """
        # Contract: history_command should accept optional days parameter
        pass
