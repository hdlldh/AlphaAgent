"""
Integration tests for stock data fetching.

Tests integration with external stock data APIs using mocked responses.
These tests verify that the fetcher correctly handles real-world API response formats.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.models import StockData


@pytest.fixture
def realistic_yfinance_response():
    """
    Create a realistic yfinance response based on actual API structure.
    """
    mock_ticker = MagicMock()

    # Realistic info dict structure from yfinance
    mock_ticker.info = {
        'symbol': 'AAPL',
        'shortName': 'Apple Inc.',
        'longName': 'Apple Inc.',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'quoteType': 'EQUITY',
        'regularMarketPrice': 185.75,
        'regularMarketDayHigh': 187.50,
        'regularMarketDayLow': 184.00,
        'regularMarketVolume': 52000000,
        'regularMarketPreviousClose': 181.60,
        'regularMarketChangePercent': 2.28,
        'marketCap': 2850000000000,
        'trailingPE': 28.45,
        'forwardPE': 25.18,
        'dividendYield': 0.0045,
        'beta': 1.25,
        'fiftyTwoWeekHigh': 198.23,
        'fiftyTwoWeekLow': 164.08,
        'fiftyDayAverage': 182.34,
        'twoHundredDayAverage': 175.89,
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'fullTimeEmployees': 164000,
        'website': 'https://www.apple.com',
    }

    # Realistic historical data
    dates = pd.date_range(end=date.today(), periods=30, freq='D')
    mock_history = pd.DataFrame({
        'Open': [180 + i * 0.5 for i in range(30)],
        'High': [182 + i * 0.5 for i in range(30)],
        'Low': [179 + i * 0.5 for i in range(30)],
        'Close': [181 + i * 0.5 for i in range(30)],
        'Volume': [48000000 + i * 100000 for i in range(30)],
    }, index=dates)

    mock_ticker.history.return_value = mock_history

    return mock_ticker


@pytest.fixture
def realistic_alpha_vantage_response():
    """
    Create a realistic Alpha Vantage API response.
    """
    dates = [date.today() - timedelta(days=i) for i in range(30)]

    time_series = {}
    for i, d in enumerate(dates):
        time_series[d.isoformat()] = {
            '1. open': str(180.0 + i * 0.5),
            '2. high': str(182.0 + i * 0.5),
            '3. low': str(179.0 + i * 0.5),
            '4. close': str(181.0 + i * 0.5),
            '5. volume': str(48000000 + i * 100000),
        }

    return {
        'Meta Data': {
            '1. Information': 'Daily Prices (open, high, low, close) and Volumes',
            '2. Symbol': 'AAPL',
            '3. Last Refreshed': date.today().isoformat(),
            '4. Output Size': 'Full size',
            '5. Time Zone': 'US/Eastern',
        },
        'Time Series (Daily)': time_series,
    }


class TestYFinanceIntegration:
    """Test integration with yfinance API."""

    @pytest.mark.asyncio
    async def test_fetch_complete_stock_data(self, realistic_yfinance_response):
        """Test fetching complete stock data with all fields."""
        fetcher = StockFetcher(primary_provider="yfinance")

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            # Verify basic data
            assert stock_data.symbol == "AAPL"
            assert stock_data.current_price > 0
            assert stock_data.volume > 0

            # Verify historical data structure
            assert not stock_data.historical_prices.empty
            assert 'Open' in stock_data.historical_prices.columns
            assert 'High' in stock_data.historical_prices.columns
            assert 'Low' in stock_data.historical_prices.columns
            assert 'Close' in stock_data.historical_prices.columns
            assert 'Volume' in stock_data.historical_prices.columns

            # Verify fundamentals
            assert 'market_cap' in stock_data.fundamentals
            assert 'sector' in stock_data.fundamentals
            assert stock_data.fundamentals['sector'] == 'Technology'

            # Verify metadata
            assert stock_data.metadata['source'] == 'yfinance'
            assert 'fetch_time' in stock_data.metadata

    @pytest.mark.asyncio
    async def test_historical_date_range(self, realistic_yfinance_response):
        """Test fetching specific date range."""
        fetcher = StockFetcher()

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data(
                "AAPL",
                start_date=start_date,
                end_date=end_date
            )

            assert isinstance(stock_data, StockData)
            assert stock_data.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_handles_market_closed(self, realistic_yfinance_response):
        """Test handling when market is closed (uses last close price)."""
        # Remove regularMarketPrice to simulate market closed
        realistic_yfinance_response.info.pop('regularMarketPrice', None)

        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            # Should use last close price from history
            assert stock_data.current_price > 0


class TestAlphaVantageIntegration:
    """Test integration with Alpha Vantage API."""

    @pytest.mark.asyncio
    async def test_fetch_from_alpha_vantage(self, realistic_alpha_vantage_response):
        """Test fetching data from Alpha Vantage."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            api_key="test_key"
        )

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = realistic_alpha_vantage_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            stock_data = await fetcher.fetch_stock_data("AAPL")

            # Verify data structure
            assert stock_data.symbol == "AAPL"
            assert stock_data.current_price > 0
            assert stock_data.volume > 0

            # Verify historical data
            assert not stock_data.historical_prices.empty
            assert 'Open' in stock_data.historical_prices.columns

            # Verify metadata
            assert stock_data.metadata['source'] == 'alpha_vantage'

    @pytest.mark.asyncio
    async def test_alpha_vantage_error_messages(self):
        """Test handling various Alpha Vantage error responses."""
        fetcher = StockFetcher(
            primary_provider="alpha_vantage",
            api_key="test_key"
        )

        # Test error message response
        error_response = {
            'Error Message': 'Invalid API call. Please retry or visit the documentation.'
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = error_response
            mock_get.return_value = mock_response

            with pytest.raises(Exception):  # Should raise InvalidSymbolError
                await fetcher.fetch_stock_data("INVALID")


class TestFallbackBehavior:
    """Test automatic fallback between providers."""

    @pytest.mark.asyncio
    async def test_yfinance_to_alpha_vantage_fallback(
        self, realistic_alpha_vantage_response
    ):
        """Test fallback from yfinance to Alpha Vantage."""
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider="alpha_vantage",
            api_key="test_key"
        )

        # Make yfinance fail
        with patch('yfinance.Ticker', side_effect=Exception("yfinance down")):
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = realistic_alpha_vantage_response
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                stock_data = await fetcher.fetch_stock_data("AAPL")

                # Should successfully get data from Alpha Vantage
                assert stock_data.symbol == "AAPL"
                assert stock_data.metadata['source'] == 'alpha_vantage'

    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(self):
        """Test that fallback doesn't occur when backup provider is None."""
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider=None  # No backup
        )

        with patch('yfinance.Ticker', side_effect=Exception("yfinance down")):
            with pytest.raises(Exception):  # Should raise DataFetchError
                await fetcher.fetch_stock_data("AAPL")


class TestRealWorldScenarios:
    """Test real-world edge cases and scenarios."""

    @pytest.mark.asyncio
    async def test_penny_stock_with_low_volume(self, realistic_yfinance_response):
        """Test fetching data for penny stock with low trading volume."""
        # Modify to simulate penny stock
        realistic_yfinance_response.info['regularMarketPrice'] = 0.25
        realistic_yfinance_response.info['regularMarketVolume'] = 5000

        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("PENNY")

            assert stock_data.current_price == 0.25
            assert stock_data.volume == 5000

    @pytest.mark.asyncio
    async def test_international_stock(self, realistic_yfinance_response):
        """Test fetching data for international stock."""
        # Modify for international stock
        realistic_yfinance_response.info['symbol'] = 'TSM'
        realistic_yfinance_response.info['currency'] = 'TWD'
        realistic_yfinance_response.info['exchange'] = 'Taiwan Stock Exchange'

        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("TSM")

            assert stock_data.symbol == "TSM"

    @pytest.mark.asyncio
    async def test_etf_data(self, realistic_yfinance_response):
        """Test fetching data for ETF."""
        # Modify for ETF
        realistic_yfinance_response.info['quoteType'] = 'ETF'
        realistic_yfinance_response.info['shortName'] = 'SPDR S&P 500 ETF Trust'

        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("SPY")

            assert stock_data.current_price > 0


class TestDataQuality:
    """Test data quality and validation."""

    @pytest.mark.asyncio
    async def test_data_completeness(self, realistic_yfinance_response):
        """Test that all expected fields are present."""
        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            # Verify required fields
            assert stock_data.symbol
            assert stock_data.current_price > 0
            assert stock_data.volume >= 0
            assert isinstance(stock_data.historical_prices, pd.DataFrame)
            assert isinstance(stock_data.fundamentals, dict)
            assert isinstance(stock_data.metadata, dict)

    @pytest.mark.asyncio
    async def test_price_data_consistency(self, realistic_yfinance_response):
        """Test that price data is consistent."""
        fetcher = StockFetcher()

        with patch('yfinance.Ticker', return_value=realistic_yfinance_response):
            stock_data = await fetcher.fetch_stock_data("AAPL")

            # Current price should be reasonable
            assert 0 < stock_data.current_price < 10000

            # Price change should be reasonable (-100% to +100% in a day)
            assert -100 <= stock_data.price_change_percent <= 100

            # Historical prices should be numeric
            assert all(stock_data.historical_prices['Close'] > 0)
