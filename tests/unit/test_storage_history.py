"""
Unit tests for historical insight queries (User Story 3).

These tests verify the get_insights() method with various filters and scenarios.
Tests are marked with [US3] for pytest filtering.
"""

import pytest
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from stock_analyzer.models import Insight, StockAnalysis
from stock_analyzer.storage import Storage

# Mark all tests in this module with US3
pytestmark = pytest.mark.US3


@pytest.fixture
def storage():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    storage = Storage(db_path)
    storage.init_database()
    yield storage

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def storage_with_insights(storage):
    """Storage with sample historical insights."""
    today = date.today()

    # Create insights for last 10 days
    for i in range(10):
        insight_date = today - timedelta(days=i)

        # Create analysis first
        analysis = StockAnalysis(
            stock_symbol="AAPL",
            analysis_date=insight_date,
            price_snapshot=150.0 + i,
            analysis_status="completed",
            duration_seconds=1.0
        )
        analysis_id = storage.save_analysis(analysis)

        # Create insight
        insight = Insight(
            analysis_id=analysis_id,
            stock_symbol="AAPL",
            analysis_date=insight_date,
            summary=f"Summary for day {i}",
            trend_analysis=f"Trend for day {i}",
            risk_factors=[f"Risk {i}"],
            opportunities=[f"Opportunity {i}"],
            confidence_level="medium",
            metadata={"day": i}
        )
        storage.save_insight(insight)

    # Create insights for another stock (MSFT) for last 5 days
    for i in range(5):
        insight_date = today - timedelta(days=i)

        analysis = StockAnalysis(
            stock_symbol="MSFT",
            analysis_date=insight_date,
            price_snapshot=300.0 + i,
            analysis_status="completed",
            duration_seconds=1.0
        )
        analysis_id = storage.save_analysis(analysis)

        insight = Insight(
            analysis_id=analysis_id,
            stock_symbol="MSFT",
            analysis_date=insight_date,
            summary=f"MSFT Summary for day {i}",
            trend_analysis=f"MSFT Trend for day {i}",
            risk_factors=[f"MSFT Risk {i}"],
            opportunities=[f"MSFT Opportunity {i}"],
            confidence_level="high",
            metadata={"day": i, "stock": "MSFT"}
        )
        storage.save_insight(insight)

    return storage


class TestBasicQueries:
    """Tests for basic insight queries."""

    def test_get_insights_returns_list(self, storage_with_insights):
        """
        GIVEN insights in database
        WHEN get_insights is called
        THEN it returns a list
        """
        result = storage_with_insights.get_insights("AAPL")

        assert isinstance(result, list)

    def test_get_insights_returns_correct_stock(self, storage_with_insights):
        """
        GIVEN insights for multiple stocks
        WHEN get_insights is called with specific symbol
        THEN only insights for that symbol are returned
        """
        aapl_insights = storage_with_insights.get_insights("AAPL")
        msft_insights = storage_with_insights.get_insights("MSFT")

        assert all(i.stock_symbol == "AAPL" for i in aapl_insights)
        assert all(i.stock_symbol == "MSFT" for i in msft_insights)
        assert len(aapl_insights) > 0
        assert len(msft_insights) > 0

    def test_get_insights_ordered_descending(self, storage_with_insights):
        """
        GIVEN insights spanning multiple dates
        WHEN get_insights is called
        THEN results are ordered by date descending (newest first)
        """
        result = storage_with_insights.get_insights("AAPL")

        for i in range(len(result) - 1):
            assert result[i].analysis_date >= result[i + 1].analysis_date

    def test_get_insights_empty_for_nonexistent_stock(self, storage_with_insights):
        """
        GIVEN database with insights
        WHEN get_insights is called for nonexistent stock
        THEN empty list is returned
        """
        result = storage_with_insights.get_insights("INVALID")

        assert result == []

    def test_get_insights_empty_database(self, storage):
        """
        GIVEN empty database
        WHEN get_insights is called
        THEN empty list is returned
        """
        result = storage.get_insights("AAPL")

        assert result == []


class TestLimitParameter:
    """Tests for limit parameter."""

    def test_limit_returns_correct_number(self, storage_with_insights):
        """
        GIVEN 10 insights in database
        WHEN get_insights is called with limit=5
        THEN exactly 5 insights are returned
        """
        result = storage_with_insights.get_insights("AAPL", limit=5)

        assert len(result) == 5

    def test_limit_larger_than_available(self, storage_with_insights):
        """
        GIVEN 10 insights in database
        WHEN get_insights is called with limit=100
        THEN all 10 insights are returned
        """
        result = storage_with_insights.get_insights("AAPL", limit=100)

        assert len(result) == 10

    def test_limit_zero(self, storage_with_insights):
        """
        GIVEN insights in database
        WHEN get_insights is called with limit=0
        THEN empty list is returned
        """
        result = storage_with_insights.get_insights("AAPL", limit=0)

        assert result == []

    def test_default_limit(self, storage_with_insights):
        """
        GIVEN insights in database
        WHEN get_insights is called without limit
        THEN default limit (30) is applied
        """
        result = storage_with_insights.get_insights("AAPL")

        # We have 10 insights, so should get all 10
        assert len(result) == 10


class TestDateFiltering:
    """Tests for date range filtering."""

    def test_start_date_filter(self, storage_with_insights):
        """
        GIVEN insights spanning 10 days
        WHEN get_insights is called with start_date 5 days ago
        THEN only insights from last 5 days are returned
        """
        start_date = date.today() - timedelta(days=5)
        result = storage_with_insights.get_insights("AAPL", start_date=start_date)

        assert all(i.analysis_date >= start_date for i in result)
        assert len(result) == 6  # Days 0-5 inclusive

    def test_end_date_filter(self, storage_with_insights):
        """
        GIVEN insights spanning 10 days
        WHEN get_insights is called with end_date 5 days ago
        THEN only insights older than 5 days are returned
        """
        end_date = date.today() - timedelta(days=5)
        result = storage_with_insights.get_insights("AAPL", end_date=end_date)

        assert all(i.analysis_date <= end_date for i in result)
        assert len(result) == 5  # Days 5-9 inclusive

    def test_date_range_filter(self, storage_with_insights):
        """
        GIVEN insights spanning 10 days
        WHEN get_insights is called with start and end dates
        THEN only insights within range are returned
        """
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=3)

        result = storage_with_insights.get_insights(
            "AAPL",
            start_date=start_date,
            end_date=end_date
        )

        assert all(start_date <= i.analysis_date <= end_date for i in result)
        assert len(result) == 5  # Days 3-7 inclusive

    def test_date_range_no_matches(self, storage_with_insights):
        """
        GIVEN insights in the past
        WHEN get_insights is called with future date range
        THEN empty list is returned
        """
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)

        result = storage_with_insights.get_insights(
            "AAPL",
            start_date=start_date,
            end_date=end_date
        )

        assert result == []

    def test_start_date_equals_end_date(self, storage_with_insights):
        """
        GIVEN insights for multiple dates
        WHEN get_insights is called with same start and end date
        THEN only insights for that specific date are returned
        """
        target_date = date.today() - timedelta(days=3)

        result = storage_with_insights.get_insights(
            "AAPL",
            start_date=target_date,
            end_date=target_date
        )

        assert len(result) == 1
        assert result[0].analysis_date == target_date


class TestOffsetParameter:
    """Tests for offset parameter (pagination)."""

    def test_offset_skips_records(self, storage_with_insights):
        """
        GIVEN 10 insights
        WHEN get_insights is called with offset=3
        THEN first 3 insights are skipped
        """
        all_results = storage_with_insights.get_insights("AAPL", limit=100)
        offset_results = storage_with_insights.get_insights("AAPL", limit=100, offset=3)

        # Should have 7 results (10 - 3)
        assert len(offset_results) == 7

        # First result with offset should match 4th result without offset
        assert offset_results[0].id == all_results[3].id

    def test_offset_with_limit(self, storage_with_insights):
        """
        GIVEN 10 insights
        WHEN get_insights is called with offset=3 and limit=2
        THEN insights 4 and 5 are returned
        """
        all_results = storage_with_insights.get_insights("AAPL", limit=100)
        page_results = storage_with_insights.get_insights("AAPL", limit=2, offset=3)

        assert len(page_results) == 2
        assert page_results[0].id == all_results[3].id
        assert page_results[1].id == all_results[4].id

    def test_offset_beyond_available(self, storage_with_insights):
        """
        GIVEN 10 insights
        WHEN get_insights is called with offset=100
        THEN empty list is returned
        """
        result = storage_with_insights.get_insights("AAPL", offset=100)

        assert result == []

    def test_offset_zero_same_as_no_offset(self, storage_with_insights):
        """
        GIVEN insights in database
        WHEN get_insights is called with offset=0
        THEN same results as no offset
        """
        no_offset = storage_with_insights.get_insights("AAPL", limit=5)
        with_offset = storage_with_insights.get_insights("AAPL", limit=5, offset=0)

        assert len(no_offset) == len(with_offset)
        assert [i.id for i in no_offset] == [i.id for i in with_offset]


class TestPaginationScenarios:
    """Tests for pagination use cases."""

    def test_paginate_through_all_results(self, storage_with_insights):
        """
        GIVEN 10 insights
        WHEN paginating with page_size=3
        THEN all insights can be retrieved across pages
        """
        page_size = 3
        all_ids = set()

        for page in range(4):  # 4 pages needed for 10 items
            offset = page * page_size
            results = storage_with_insights.get_insights("AAPL", limit=page_size, offset=offset)

            for insight in results:
                all_ids.add(insight.id)

        # Should have collected all 10 unique IDs
        assert len(all_ids) == 10

    def test_last_page_partial(self, storage_with_insights):
        """
        GIVEN 10 insights
        WHEN requesting last page with page_size=3
        THEN last page has only 1 insight
        """
        page_size = 3
        offset = 9  # 4th page

        result = storage_with_insights.get_insights("AAPL", limit=page_size, offset=offset)

        assert len(result) == 1


class TestInsightDataIntegrity:
    """Tests for insight data structure and integrity."""

    def test_insight_has_all_fields(self, storage_with_insights):
        """
        GIVEN insights in database
        WHEN get_insights is called
        THEN each insight has all required fields populated
        """
        result = storage_with_insights.get_insights("AAPL", limit=1)

        assert len(result) == 1
        insight = result[0]

        assert insight.id is not None
        assert insight.analysis_id is not None
        assert insight.stock_symbol == "AAPL"
        assert isinstance(insight.analysis_date, date)
        assert isinstance(insight.summary, str)
        assert isinstance(insight.trend_analysis, str)
        assert isinstance(insight.risk_factors, list)
        assert isinstance(insight.opportunities, list)
        assert insight.confidence_level in ["low", "medium", "high"]
        assert isinstance(insight.metadata, dict)
        assert isinstance(insight.created_at, datetime)

    def test_insight_metadata_deserialization(self, storage_with_insights):
        """
        GIVEN insights with metadata
        WHEN get_insights is called
        THEN metadata is properly deserialized as dict
        """
        result = storage_with_insights.get_insights("AAPL", limit=1)

        insight = result[0]
        assert isinstance(insight.metadata, dict)
        assert "day" in insight.metadata


class TestCombinedFilters:
    """Tests for combining multiple filters."""

    def test_date_range_with_limit(self, storage_with_insights):
        """
        GIVEN insights spanning multiple dates
        WHEN get_insights is called with date range and limit
        THEN results match both date range and limit
        """
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=2)

        result = storage_with_insights.get_insights(
            "AAPL",
            start_date=start_date,
            end_date=end_date,
            limit=3
        )

        assert len(result) == 3
        assert all(start_date <= i.analysis_date <= end_date for i in result)

    def test_date_range_with_offset_and_limit(self, storage_with_insights):
        """
        GIVEN insights spanning multiple dates
        WHEN get_insights is called with date range, offset, and limit
        THEN results match all filters
        """
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        result = storage_with_insights.get_insights(
            "AAPL",
            start_date=start_date,
            end_date=end_date,
            limit=2,
            offset=2
        )

        assert len(result) == 2
        assert all(start_date <= i.analysis_date <= end_date for i in result)
