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
    """Test the run-daily-job command contract."""

    @pytest.mark.asyncio
    async def test_run_daily_job_output(self, cli, capsys):
        """Test daily job command output."""
        # Mock get_subscriptions and other dependencies
        with patch.object(cli, '_get_active_subscriptions', return_value=["AAPL", "TSLA"]):
            exit_code = await cli.run_daily_job(dry_run=False, json_output=False)

            assert exit_code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Verify job output structure
            assert "job" in output.lower() or "analysis" in output.lower()

    @pytest.mark.asyncio
    async def test_run_daily_job_dry_run(self, cli, capsys):
        """Test daily job in dry-run mode."""
        with patch.object(cli, '_get_active_subscriptions', return_value=["AAPL"]):
            exit_code = await cli.run_daily_job(dry_run=True, json_output=False)

            assert exit_code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Verify dry-run indication
            assert "dry" in output.lower() or "simulate" in output.lower()

    @pytest.mark.asyncio
    async def test_run_daily_job_json_output(self, cli, capsys):
        """Test daily job with JSON output."""
        with patch.object(cli, '_get_active_subscriptions', return_value=["AAPL"]):
            exit_code = await cli.run_daily_job(dry_run=False, json_output=True)

            assert exit_code == 0

            captured = capsys.readouterr()
            output = captured.out

            # Verify JSON structure
            data = json.loads(output)
            assert 'job_id' in data or 'status' in data
            assert 'stocks_scheduled' in data or 'total' in data


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
