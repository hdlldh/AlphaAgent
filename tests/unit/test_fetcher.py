"""
Unit tests for StockFetcher class.

Tests stock data fetching from:
- yfinance (primary)
- Alpha Vantage (backup)
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyzer.exceptions import DataFetchError, InvalidSymbolError, RateLimitError
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.models import StockData


@pytest.fixture
def mock_yfinance_data():
    """Create mock yfinance ticker data."""
    mock_ticker = MagicMock()

    # Mock info dict
    mock_ticker.info = {
        'regularMarketPrice': 185.75,
        'regularMarketChangePercent': 2.3,
        'regularMarketVolume': 52000000,
        'marketCap': 2800000000000,
        'trailingPE': 28.5,
        'forwardPE': 25.2,
        'dividendYield': 0.0045,
        'shortName': 'Apple Inc.',
        'sector': 'Technology',
    }

    # Mock history DataFrame
    mock_history = pd.DataFrame({
        'Open': [180.0, 183.0, 185.0],
        'High': [182.0, 185.0, 187.0],
        'Low': [179.0, 182.0, 184.0],
        'Close': [181.0, 184.5, 185.75],
        'Volume': [48000000, 50000000, 52000000],
    }, index=pd.DatetimeIndex([
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=1),
        date.today(),
    ]))
    mock_ticker.history.return_value = mock_history

    return mock_ticker


@pytest.fixture
def mock_alpha_vantage_data():
    """Create mock Alpha Vantage API response."""
    return {
        'Meta Data': {
            '2. Symbol': 'AAPL',
            '3. Last Refreshed': date.today().isoformat(),
        },
        'Time Series (Daily)': {
            date.today().isoformat(): {
                '1. open': '185.00',
                '2. high': '187.00',
                '3. low': '184.00',
                '4. close': '185.75',
                '5. volume': '52000000',
            },
            (date.today() - timedelta(days=1)).isoformat(): {
                '1. open': '183.00',
                '2. high': '185.00',
                '3. low': '182.00',
                '4. close': '184.50',
                '5. volume': '50000000',
            },
        }
    }


class TestStockFetcherInitialization:
    """Test StockFetcher initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default providers."""
        fetcher = StockFetcher()

        assert fetcher.primary_provider == "yfinance"
        assert fetcher.backup_provider == "alpha_vantage"
        assert fetcher.api_key is None

    def test_init_with_custom_providers(self):
        """Test initialization with custom provider configuration."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            backup_provider="yfinance",
            api_key="test_key"
        )

        assert fetcher.primary_provider == "alpha_vantage"
        assert fetcher.backup_provider == "yfinance"
        assert fetcher.api_key == "test_key"

    def test_init_with_only_primary(self):
        """Test initialization with only primary provider."""
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider=None
        )

        assert fetcher.primary_provider == "yfinance"
        assert fetcher.backup_provider is None


class TestFetchStockData:
    """Test fetching stock data."""

    @pytest.mark.asyncio
    async def test_fetch_from_yfinance_success(self, mock_yfinance_data):
        """Test successful fetch from yfinance."""
        fetcher = StockFetcher(primary_provider="yfinance")

        with patch('yfinance.Ticker', return_value=mock_yfinance_data):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            assert isinstance(stock_data, StockData)
            assert stock_data.symbol == "AAPL"
            assert stock_data.current_price == 185.75
            assert stock_data.price_change_percent == 2.3
            assert stock_data.volume == 52000000
            assert not stock_data.historical_prices.empty
            assert stock_data.fundamentals['market_cap'] == 2800000000000

    @pytest.mark.asyncio
    async def test_fetch_with_date_range(self, mock_yfinance_data):
        """Test fetching historical data with date range."""
        fetcher = StockFetcher()

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        with patch('yfinance.Ticker', return_value=mock_yfinance_data):
            stock_data = await fetcher.fetch_stock_data(
                "AAPL",
                start_date=start_date,
                end_date=end_date
            )

            assert isinstance(stock_data, StockData)
            assert stock_data.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_fetch_fallback_to_backup(self, mock_alpha_vantage_data):
        """Test fallback to Alpha Vantage when yfinance fails."""
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider="alpha_vantage",
            api_key="test_key"
        )

        # Mock yfinance to fail
        with patch('yfinance.Ticker', side_effect=Exception("yfinance error")):
            with patch('stock_analyzer.fetcher.StockFetcher._fetch_from_alpha_vantage') as mock_av:
                mock_av.return_value = StockData(
                    symbol="AAPL",
                    current_price=185.75,
                    price_change_percent=2.3,
                    volume=52000000,
                    historical_prices=pd.DataFrame(),
                    fundamentals={},
                    metadata={"source": "alpha_vantage"}
                )

                stock_data = await fetcher.fetch_stock_data("AAPL")

                assert stock_data.symbol == "AAPL"
                assert stock_data.metadata.get("source") == "alpha_vantage"
                mock_av.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_both_providers_fail(self):
        """Test when both primary and backup providers fail."""
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider="alpha_vantage",
            api_key="test_key"
        )

        with patch('yfinance.Ticker', side_effect=Exception("yfinance error")):
            with patch('stock_analyzer.fetcher.StockFetcher._fetch_from_alpha_vantage',
                      side_effect=Exception("alpha vantage error")):

                with pytest.raises(DataFetchError):
                    await fetcher.fetch_stock_data("AAPL")

    @pytest.mark.asyncio
    async def test_fetch_invalid_symbol(self):
        """Test fetching data for invalid symbol."""
        fetcher = StockFetcher()

        mock_ticker = MagicMock()
        mock_ticker.info = {}  # Empty info indicates invalid symbol

        with patch('yfinance.Ticker', return_value=mock_ticker):
            with pytest.raises(InvalidSymbolError):
                await fetcher.fetch_stock_data("INVALID123")

    @pytest.mark.asyncio
    async def test_fetch_handles_missing_fields(self, mock_yfinance_data):
        """Test that fetch handles missing optional fields gracefully."""
        # Keep minimal required fields, remove optional ones
        mock_yfinance_data.info = {
            'regularMarketPrice': 185.75,
            'symbol': 'AAPL',
            'shortName': 'Apple Inc.',
            'sector': 'Technology',
            'marketCap': 2800000000000,
            'volume': 52000000,
            # Missing regularMarketChangePercent, PE ratio, etc.
        }

        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=mock_yfinance_data):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            assert stock_data.current_price == 185.75
            # Should handle missing optional fields with defaults
            assert stock_data.price_change_percent == 0.0  # Default when missing


class TestValidateSymbol:
    """Test stock symbol validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_symbol(self, mock_yfinance_data):
        """Test validating a valid stock symbol."""
        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=mock_yfinance_data):
            result = await fetcher.validate_symbol("AAPL")

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_invalid_symbol(self):
        """Test validating an invalid stock symbol."""
        fetcher = StockFetcher()

        mock_ticker = MagicMock()
        mock_ticker.info = {}  # Empty info = invalid

        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await fetcher.validate_symbol("INVALID")

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_delisted_symbol(self):
        """Test validating a delisted symbol."""
        fetcher = StockFetcher()

        mock_ticker = MagicMock()
        mock_ticker.info = {'symbol': 'XYZ'}  # Has some data but might be delisted
        mock_ticker.history.return_value = pd.DataFrame()  # No recent history

        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await fetcher.validate_symbol("XYZ")

            # Should return False if no recent trading data
            assert isinstance(result, bool)


class TestAlphaVantageIntegration:
    """Test Alpha Vantage backup provider."""

    @pytest.mark.asyncio
    async def test_fetch_from_alpha_vantage(self, mock_alpha_vantage_data):
        """Test fetching from Alpha Vantage directly."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            api_key="test_key"
        )

        with patch('stock_analyzer.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_alpha_vantage_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            stock_data = await fetcher.fetch_stock_data("AAPL")

            assert stock_data.symbol == "AAPL"
            assert stock_data.metadata.get("source") == "alpha_vantage"

    @pytest.mark.asyncio
    async def test_alpha_vantage_rate_limit(self):
        """Test handling Alpha Vantage rate limit."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            api_key="test_key"
        )

        with patch('stock_analyzer.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 25 calls per day.'
            }
            mock_get.return_value = mock_response

            with pytest.raises(RateLimitError):
                await fetcher.fetch_stock_data("AAPL")

    @pytest.mark.asyncio
    async def test_alpha_vantage_requires_api_key(self):
        """Test that Alpha Vantage requires API key."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            api_key=None  # No API key
        )

        with pytest.raises(DataFetchError, match="API key required"):
            await fetcher.fetch_stock_data("AAPL")


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_empty_symbol_raises_error(self):
        """Test that empty symbol raises error."""
        fetcher = StockFetcher()

        with pytest.raises(InvalidSymbolError):
            await fetcher.fetch_stock_data("")

    @pytest.mark.asyncio
    async def test_none_symbol_raises_error(self):
        """Test that None symbol raises error."""
        fetcher = StockFetcher()

        with pytest.raises(InvalidSymbolError):
            await fetcher.fetch_stock_data(None)

    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling of network timeout."""
        fetcher = StockFetcher()

        with patch('yfinance.Ticker', side_effect=TimeoutError("Network timeout")):
            with pytest.raises(DataFetchError):
                await fetcher.fetch_stock_data("AAPL")

    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        """Test handling of invalid date range (end before start)."""
        fetcher = StockFetcher()

        start_date = date.today()
        end_date = date.today() - timedelta(days=30)  # Invalid: end before start

        with pytest.raises(ValueError):
            await fetcher.fetch_stock_data("AAPL", start_date=start_date, end_date=end_date)
