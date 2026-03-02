"""
Contract tests for Config interface.

Tests the public API contract for configuration management,
ensuring get_stock_symbols() parses and validates stock lists correctly.
"""

import pytest

from stock_analyzer.config import Config


class TestStockListParsing:
    """Test Config.get_stock_symbols() contract."""

    def test_get_stock_symbols_basic_parsing(self):
        """Test parsing comma-separated stock list."""
        config = Config(
            stock_list="AAPL,MSFT,GOOGL",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        symbols = config.get_stock_symbols()

        assert symbols == ["AAPL", "MSFT", "GOOGL"]
        assert len(symbols) == 3
        assert all(isinstance(sym, str) for sym in symbols)

    def test_get_stock_symbols_with_whitespace(self):
        """Test parsing stock list with extra whitespace."""
        config = Config(
            stock_list="AAPL, MSFT , GOOGL,  TSLA  ",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        symbols = config.get_stock_symbols()

        # Should strip whitespace from each symbol
        assert symbols == ["AAPL", "MSFT", "GOOGL", "TSLA"]

    def test_get_stock_symbols_uppercase_normalization(self):
        """Test parsing stock list with mixed case (should uppercase)."""
        config = Config(
            stock_list="aapl,Msft,GOOGL,tSLa",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        symbols = config.get_stock_symbols()

        # All symbols should be uppercased
        assert symbols == ["AAPL", "MSFT", "GOOGL", "TSLA"]
        assert all(sym.isupper() for sym in symbols)

    def test_get_stock_symbols_deduplication(self):
        """Test parsing stock list with duplicate symbols."""
        config = Config(
            stock_list="AAPL,MSFT,AAPL,GOOGL,MSFT",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        symbols = config.get_stock_symbols()

        # Should remove duplicates while preserving order
        assert symbols == ["AAPL", "MSFT", "GOOGL"]
        assert len(symbols) == 3

    def test_get_stock_symbols_single_symbol(self):
        """Test parsing stock list with single symbol."""
        config = Config(
            stock_list="AAPL",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        symbols = config.get_stock_symbols()

        assert symbols == ["AAPL"]


class TestStockListValidation:
    """Test Config validation for empty stock list."""

    def test_validate_empty_stock_list_raises_error(self):
        """Test validation fails with empty stock list."""
        config = Config(
            stock_list="",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        with pytest.raises(ValueError, match="stock list.*empty|required"):
            config.validate()

    def test_validate_none_stock_list_raises_error(self):
        """Test validation fails with None stock list."""
        config = Config(
            stock_list=None,
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        with pytest.raises(ValueError, match="stock list.*empty|required"):
            config.validate()

    def test_validate_whitespace_only_stock_list_raises_error(self):
        """Test validation fails with whitespace-only stock list."""
        config = Config(
            stock_list="   , ,  ",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@testchannel"
        )

        with pytest.raises(ValueError, match="stock list.*empty|required"):
            config.validate()

    def test_validate_missing_telegram_channel_raises_error(self):
        """Test validation fails with missing telegram channel."""
        config = Config(
            stock_list="AAPL,MSFT",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel=None
        )

        with pytest.raises(ValueError, match="telegram.*channel.*required"):
            config.validate()

    def test_validate_valid_stock_list_and_channel(self):
        """Test validation passes with valid stock list and channel."""
        config = Config(
            stock_list="AAPL,MSFT,GOOGL",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@mystocks",
            llm_provider="anthropic"
        )

        # Should not raise
        config.validate()
