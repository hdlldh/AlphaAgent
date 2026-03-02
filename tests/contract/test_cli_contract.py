"""
Contract tests for CLI interface.

Tests the command-line interface commands and their output formats.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from stock_analyzer.cli import CLI
from stock_analyzer.models import Insight


@pytest.fixture
def mock_analyzer():
    """Create a mock analyzer."""
    analyzer = MagicMock()

    # Mock analyze_stock
    async def mock_analyze(symbol, date=None, force=False):
        from datetime import date as dt
        return Insight(
            stock_symbol=symbol,
            analysis_date=date or dt.today(),
            summary="Strong upward momentum",
            trend_analysis="Positive trend observed",
            risk_factors=["Overvaluation", "Market volatility"],
            opportunities=["Product launches", "Services growth"],
            confidence_level="high",
            metadata={"llm_model": "claude-sonnet-4-5", "tokens_used": 1500}
        )

    analyzer.analyze_stock = mock_analyze

    # Mock analyze_batch
    async def mock_batch(symbols, parallel=1, continue_on_error=False):
        result = MagicMock()
        result.total = len(symbols)
        result.success_count = len(symbols)
        result.failure_count = 0
        result.duration_seconds = 10.5
        result.results = [
            MagicMock(stock_symbol=sym, status="success") for sym in symbols
        ]
        return result

    analyzer.analyze_batch = mock_batch

    return analyzer


@pytest.fixture
def cli(mock_analyzer, tmp_path):
    """Create CLI instance with mocked dependencies."""
    db_path = tmp_path / "test.db"
    return CLI(config=None, db_path=str(db_path), analyzer=mock_analyzer)


class TestAnalyzeCommand:
    """Test the analyze command contract."""

    @pytest.mark.asyncio
    async def test_analyze_human_readable_output(self, cli, capsys):
        """Test analyze command with human-readable output."""
        exit_code = await cli.analyze("AAPL", json_output=False)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify human-readable format
        assert "AAPL" in output
        assert "Strong upward momentum" in output
        assert "Risk Factors" in output or "risk" in output.lower()
        assert "Opportunities" in output or "opportunity" in output.lower()

    @pytest.mark.asyncio
    async def test_analyze_json_output(self, cli, capsys):
        """Test analyze command with JSON output."""
        exit_code = await cli.analyze("AAPL", json_output=True)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify JSON format
        data = json.loads(output)
        assert data['status'] == 'success'
        assert data['stock_symbol'] == 'AAPL'
        assert 'summary' in data
        assert 'risk_factors' in data
        assert 'opportunities' in data
        assert 'confidence_level' in data

    @pytest.mark.asyncio
    async def test_analyze_with_date(self, cli):
        """Test analyze command with specific date."""
        from datetime import date
        exit_code = await cli.analyze(
            "AAPL",
            date=date(2026, 1, 30),
            json_output=False
        )

        assert exit_code == 0

    @pytest.mark.asyncio
    async def test_analyze_force_flag(self, cli):
        """Test analyze command with force flag."""
        exit_code = await cli.analyze("AAPL", force=True, json_output=False)

        assert exit_code == 0

    @pytest.mark.asyncio
    async def test_analyze_invalid_symbol_returns_error(self, cli, mock_analyzer):
        """Test analyze command error handling."""
        from stock_analyzer.exceptions import InvalidSymbolError

        async def mock_error(symbol, date=None, force=False):
            raise InvalidSymbolError(symbol, "Not found")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("INVALID", json_output=False)

        assert exit_code == 1  # Error exit code


class TestAnalyzeBatchCommand:
    """Test the analyze-batch command contract."""

    @pytest.mark.asyncio
    async def test_analyze_batch_from_list(self, cli, capsys):
        """Test batch analysis with list of symbols."""
        symbols = ["AAPL", "TSLA", "MSFT"]
        exit_code = await cli.analyze_batch(symbols, json_output=False)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify summary output
        assert "3" in output or "Success: 3" in output

    @pytest.mark.asyncio
    async def test_analyze_batch_json_output(self, cli, capsys):
        """Test batch analysis with JSON output."""
        symbols = ["AAPL", "TSLA"]
        exit_code = await cli.analyze_batch(symbols, json_output=True)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify JSON structure
        data = json.loads(output)
        assert data['status'] == 'success'
        assert data['total'] == 2
        assert data['success_count'] == 2
        assert 'results' in data

    @pytest.mark.asyncio
    async def test_analyze_batch_parallel(self, cli):
        """Test batch analysis with parallel execution."""
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL"]
        exit_code = await cli.analyze_batch(
            symbols,
            parallel=2,
            json_output=False
        )

        assert exit_code == 0

    @pytest.mark.asyncio
    async def test_analyze_batch_continue_on_error(self, cli):
        """Test batch analysis with continue_on_error flag."""
        symbols = ["AAPL", "TSLA"]
        exit_code = await cli.analyze_batch(
            symbols,
            continue_on_error=True,
            json_output=False
        )

        assert exit_code == 0


class TestRunDailyJobCommand:
    """Test the run-daily-job command contract (personal use)."""

    @pytest.mark.asyncio
    async def test_run_daily_job_output(self, cli, capsys, monkeypatch):
        """Test daily job command output using stock list from config."""
        # Set stock list in config
        monkeypatch.setattr(cli.config, 'stock_list', 'AAPL,TSLA')

        exit_code = await cli.run_daily_job(dry_run=False, json_output=False)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify job output structure for personal use
        assert "job" in output.lower() or "analysis" in output.lower()
        assert "personal" in output.lower()

    @pytest.mark.asyncio
    async def test_run_daily_job_dry_run(self, cli, capsys, monkeypatch):
        """Test daily job in dry-run mode with config stock list."""
        # Set stock list in config
        monkeypatch.setattr(cli.config, 'stock_list', 'AAPL')

        exit_code = await cli.run_daily_job(dry_run=True, json_output=False)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify dry-run indication and stock list source
        assert "dry" in output.lower()
        assert "aapl" in output.lower()

    @pytest.mark.asyncio
    async def test_run_daily_job_json_output(self, cli, capsys, monkeypatch):
        """Test daily job with JSON output using config stock list."""
        # Set stock list in config
        monkeypatch.setattr(cli.config, 'stock_list', 'AAPL')

        exit_code = await cli.run_daily_job(dry_run=False, json_output=True)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify JSON structure
        data = json.loads(output)
        assert 'job_id' in data or 'status' in data
        assert 'stocks_scheduled' in data or 'total' in data

    @pytest.mark.asyncio
    async def test_run_daily_job_empty_stock_list(self, cli, capsys, monkeypatch):
        """Test daily job with empty stock list returns error."""
        # Set empty stock list
        monkeypatch.setattr(cli.config, 'stock_list', '')

        exit_code = await cli.run_daily_job(dry_run=False, json_output=False)

        assert exit_code == 1  # Error exit code

        captured = capsys.readouterr()
        output = captured.err

        # Verify error message mentions stock list
        assert "stock" in output.lower() and ("empty" in output.lower() or "list" in output.lower())


class TestCLIErrorHandling:
    """Test CLI error handling contract."""

    @pytest.mark.asyncio
    async def test_error_output_format(self, cli, mock_analyzer, capsys):
        """Test that errors are output to stderr."""
        from stock_analyzer.exceptions import AnalysisError

        async def mock_error(symbol, date=None, force=False):
            raise AnalysisError(symbol, "Analysis failed", "test-model")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("AAPL", json_output=False)

        assert exit_code != 0

        captured = capsys.readouterr()
        # Error should be in output (either stdout or stderr)
        assert captured.err or "error" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_json_error_format(self, cli, mock_analyzer, capsys):
        """Test JSON error format."""
        from stock_analyzer.exceptions import DataFetchError

        async def mock_error(symbol, date=None, force=False):
            raise DataFetchError(symbol, "Failed to fetch", "yfinance")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("AAPL", json_output=True)

        assert exit_code != 0

        captured = capsys.readouterr()
        output = captured.out or captured.err

        # Verify JSON error structure
        if output and output.strip():
            data = json.loads(output)
            assert data['status'] == 'error'
            assert 'error_message' in data or 'message' in data


class TestCLIExitCodes:
    """Test CLI exit code contract."""

    @pytest.mark.asyncio
    async def test_success_returns_zero(self, cli):
        """Test that successful commands return exit code 0."""
        exit_code = await cli.analyze("AAPL", json_output=False)
        assert exit_code == 0

    @pytest.mark.asyncio
    async def test_invalid_symbol_returns_one(self, cli, mock_analyzer):
        """Test that invalid symbol returns exit code 1."""
        from stock_analyzer.exceptions import InvalidSymbolError

        async def mock_error(symbol, date=None, force=False):
            raise InvalidSymbolError(symbol, "Not found")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("INVALID", json_output=False)
        assert exit_code == 1

    @pytest.mark.asyncio
    async def test_data_fetch_error_returns_two(self, cli, mock_analyzer):
        """Test that data fetch error returns exit code 2."""
        from stock_analyzer.exceptions import DataFetchError

        async def mock_error(symbol, date=None, force=False):
            raise DataFetchError(symbol, "Fetch failed", "test")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("AAPL", json_output=False)
        assert exit_code == 2

    @pytest.mark.asyncio
    async def test_analysis_error_returns_three(self, cli, mock_analyzer):
        """Test that analysis error returns exit code 3."""
        from stock_analyzer.exceptions import AnalysisError

        async def mock_error(symbol, date=None, force=False):
            raise AnalysisError(symbol, "Analysis failed", "test-model")

        mock_analyzer.analyze_stock = mock_error

        exit_code = await cli.analyze("AAPL", json_output=False)
        assert exit_code == 3


class TestHistoryCommand:
    """Test the history command contract (personal use - no user filtering)."""

    def test_history_without_user_filtering(self, cli, capsys):
        """Test history command queries all insights without user_id filtering."""
        from datetime import date, datetime
        from stock_analyzer.models import Insight

        # Store multiple insights for same stock
        insights_data = [
            Insight(
                stock_symbol="AAPL",
                analysis_date=date(2026, 1, 28),
                summary="Day 1 summary",
                trend_analysis="Positive",
                risk_factors=["Risk 1"],
                opportunities=["Opp 1"],
                confidence_level="high",
                metadata={},
                created_at=datetime(2026, 1, 28, 10, 0)
            ),
            Insight(
                stock_symbol="AAPL",
                analysis_date=date(2026, 1, 29),
                summary="Day 2 summary",
                trend_analysis="Neutral",
                risk_factors=["Risk 2"],
                opportunities=["Opp 2"],
                confidence_level="medium",
                metadata={},
                created_at=datetime(2026, 1, 29, 10, 0)
            ),
            Insight(
                stock_symbol="AAPL",
                analysis_date=date(2026, 1, 30),
                summary="Day 3 summary",
                trend_analysis="Negative",
                risk_factors=["Risk 3"],
                opportunities=["Opp 3"],
                confidence_level="low",
                metadata={},
                created_at=datetime(2026, 1, 30, 10, 0)
            )
        ]

        # Save all insights
        for insight in insights_data:
            cli.storage.save_insight(insight)

        # Query history (no user_id needed - personal use)
        exit_code = cli.history("AAPL", limit=10)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify all insights shown (no user filtering)
        assert "Day 1 summary" in output
        assert "Day 2 summary" in output
        assert "Day 3 summary" in output
        assert "AAPL" in output

    def test_history_with_date_range_filtering(self, cli, capsys):
        """Test history command with date range filtering."""
        from datetime import date, datetime
        from stock_analyzer.models import Insight

        # Store insights across multiple days
        for day in [27, 28, 29, 30, 31]:
            insight = Insight(
                stock_symbol="MSFT",
                analysis_date=date(2026, 1, day),
                summary=f"Day {day} analysis",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium",
                metadata={},
                created_at=datetime(2026, 1, day, 10, 0)
            )
            cli.storage.save_insight(insight)

        # Query with date range
        start = date(2026, 1, 28)
        end = date(2026, 1, 30)
        exit_code = cli.history("MSFT", start_date=start, end_date=end)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Should include days 28, 29, 30
        assert "Day 28" in output
        assert "Day 29" in output
        assert "Day 30" in output

        # Should NOT include days 27, 31
        assert "Day 27" not in output
        assert "Day 31" not in output

    def test_history_json_output(self, cli, capsys):
        """Test history command with JSON output."""
        from datetime import date, datetime
        from stock_analyzer.models import Insight

        insight = Insight(
            stock_symbol="GOOGL",
            analysis_date=date(2026, 1, 30),
            summary="Test summary",
            trend_analysis="Test trend",
            risk_factors=["Risk A"],
            opportunities=["Opp B"],
            confidence_level="high",
            metadata={},
            created_at=datetime(2026, 1, 30, 10, 0)
        )
        cli.storage.save_insight(insight)

        # Get JSON output
        exit_code = cli.history("GOOGL", json_output=True)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Parse JSON
        data = json.loads(output)

        assert data['status'] == 'success'
        assert data['symbol'] == 'GOOGL'
        assert data['total'] == 1
        assert len(data['insights']) == 1
        assert data['insights'][0]['summary'] == "Test summary"

    def test_history_pagination(self, cli, capsys):
        """Test history command pagination (limit/offset)."""
        from datetime import date, datetime, timedelta
        from stock_analyzer.models import Insight

        # Store 10 insights
        base_date = date(2026, 1, 20)
        for i in range(10):
            insight = Insight(
                stock_symbol="TSLA",
                analysis_date=base_date + timedelta(days=i),
                summary=f"Analysis {i+1}",
                trend_analysis="Test",
                risk_factors=[],
                opportunities=[],
                confidence_level="medium",
                metadata={},
                created_at=datetime(2026, 1, 20 + i, 10, 0)
            )
            cli.storage.save_insight(insight)

        # Test limit
        exit_code = cli.history("TSLA", limit=5, json_output=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['total'] == 5
        assert len(data['insights']) == 5

        # Test offset
        exit_code = cli.history("TSLA", limit=3, offset=2, json_output=True)
        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['total'] == 3
        assert data['offset'] == 2

    def test_history_empty_results(self, cli, capsys):
        """Test history command with no results."""
        # Query non-existent symbol
        exit_code = cli.history("NONEXIST", json_output=False)

        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        assert "No insights found" in output
        assert "NONEXIST" in output

    def test_history_empty_results_json(self, cli, capsys):
        """Test history command with no results (JSON output)."""
        exit_code = cli.history("EMPTY", json_output=True)

        assert exit_code == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data['status'] == 'success'
        assert data['total'] == 0
        assert data['insights'] == []
