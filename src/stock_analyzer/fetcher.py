"""
Stock data fetcher with multi-provider support.

Primary provider: yfinance (free, reliable)
Backup provider: Alpha Vantage (requires API key, 25 calls/day free)
"""

import time
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
import requests

from stock_analyzer.exceptions import (
    DataFetchError,
    InvalidSymbolError,
    RateLimitError,
)
from stock_analyzer.logging import get_logger, log_api_call, log_api_response, log_api_error
from stock_analyzer.models import StockData

logger = get_logger(__name__)


class StockFetcher:
    """
    Stock market data fetcher with automatic fallback.

    Fetches stock data from yfinance (primary) with automatic fallback
    to Alpha Vantage if primary fails.
    """

    def __init__(
        self,
        primary_provider: str = "yfinance",
        backup_provider: Optional[str] = "alpha_vantage",
        api_key: Optional[str] = None,
    ):
        """
        Initialize stock fetcher.

        Args:
            primary_provider: Primary data provider ("yfinance" or "alpha_vantage")
            backup_provider: Backup provider for fallback (None to disable)
            api_key: API key for Alpha Vantage (required if using it)
        """
        self.primary_provider = primary_provider
        self.backup_provider = backup_provider
        self.api_key = api_key

    async def fetch_stock_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> StockData:
        """
        Fetch stock data for a symbol.

        Tries primary provider first, falls back to backup if primary fails.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")
            start_date: Start date for historical data (default: 30 days ago)
            end_date: End date for historical data (default: today)

        Returns:
            StockData with current price, historical data, and fundamentals

        Raises:
            InvalidSymbolError: Symbol is invalid or not found
            DataFetchError: Failed to fetch data from all providers
            RateLimitError: API rate limit exceeded
            ValueError: Invalid date range
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise InvalidSymbolError(symbol, "Symbol must be a non-empty string")

        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        # Set default dates
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Try primary provider
        logger.debug(f"Fetching data for {symbol} from {self.primary_provider}")
        try:
            if self.primary_provider == "yfinance":
                return await self._fetch_from_yfinance(symbol, start_date, end_date)
            elif self.primary_provider == "alpha_vantage":
                return await self._fetch_from_alpha_vantage(symbol, start_date, end_date)
            else:
                raise ValueError(f"Unknown provider: {self.primary_provider}")

        except (InvalidSymbolError, RateLimitError) as e:
            # Don't fall back for these errors
            logger.warning(f"Non-recoverable error fetching {symbol}: {type(e).__name__}")
            raise

        except Exception as e:
            # Try backup provider
            logger.warning(f"Primary provider failed for {symbol}, trying backup: {e}")
            if self.backup_provider:
                try:
                    if self.backup_provider == "alpha_vantage":
                        return await self._fetch_from_alpha_vantage(
                            symbol, start_date, end_date
                        )
                    elif self.backup_provider == "yfinance":
                        return await self._fetch_from_yfinance(
                            symbol, start_date, end_date
                        )
                except Exception as backup_error:
                    raise DataFetchError(
                        symbol,
                        f"Both providers failed. Primary: {str(e)}. Backup: {str(backup_error)}",
                    )

            # No backup provider available
            raise DataFetchError(symbol, str(e), self.primary_provider)

    async def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a stock symbol exists and has recent trading data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            True if symbol is valid and has recent data, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Check if symbol has basic info
            if not info or len(info) < 5:
                return False

            # Check if symbol has recent trading data
            history = ticker.history(period="5d")
            if history.empty:
                return False

            return True

        except Exception:
            return False

    async def _fetch_from_yfinance(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockData:
        """
        Fetch stock data from yfinance.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            StockData object

        Raises:
            InvalidSymbolError: Symbol not found or invalid
            DataFetchError: Failed to fetch data
        """
        start_time = time.time()
        log_api_call(logger, "yfinance", "fetch_stock_data", symbol=symbol)

        try:
            ticker = yf.Ticker(symbol)

            # Get current info
            info = ticker.info

            # Validate that we got real data (not just empty dict)
            if not info or len(info) < 5:
                raise InvalidSymbolError(symbol, "Symbol not found or has no data")

            # Get historical data
            history = ticker.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),  # Include end date
            )

            if history.empty:
                raise InvalidSymbolError(
                    symbol, "No historical data available (possibly delisted)"
                )

            # Extract current price data
            current_price = info.get("regularMarketPrice") or info.get("currentPrice")
            if current_price is None and not history.empty:
                # Use last close price if current price not available
                current_price = float(history['Close'].iloc[-1])

            price_change_percent = info.get("regularMarketChangePercent", 0.0)
            volume = info.get("regularMarketVolume") or info.get("volume", 0)

            # Extract fundamentals
            fundamentals = {
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52week_high": info.get("fiftyTwoWeekHigh"),
                "52week_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }

            # Remove None values
            fundamentals = {k: v for k, v in fundamentals.items() if v is not None}

            duration = time.time() - start_time
            log_api_response(logger, "yfinance", "success", duration)
            logger.debug(f"Fetched {len(history)} data points for {symbol} from yfinance")

            return StockData(
                symbol=symbol.upper(),
                current_price=float(current_price),
                price_change_percent=float(price_change_percent),
                volume=int(volume),
                historical_prices=history,
                fundamentals=fundamentals,
                metadata={
                    "source": "yfinance",
                    "fetch_time": datetime.utcnow().isoformat(),
                    "data_points": len(history),
                },
            )

        except InvalidSymbolError as e:
            log_api_error(logger, "yfinance", e)
            raise
        except Exception as e:
            log_api_error(logger, "yfinance", e)
            raise DataFetchError(symbol, f"yfinance error: {str(e)}", "yfinance")

    async def _fetch_from_alpha_vantage(
        self, symbol: str, start_date: date, end_date: date
    ) -> StockData:
        """
        Fetch stock data from Alpha Vantage API.

        Requires API key. Free tier: 25 calls per day.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            StockData object

        Raises:
            DataFetchError: Failed to fetch data or missing API key
            RateLimitError: API rate limit exceeded
            InvalidSymbolError: Symbol not found
        """
        if not self.api_key:
            raise DataFetchError(
                symbol,
                "API key required for Alpha Vantage",
                "alpha_vantage",
            )

        start_time = time.time()
        log_api_call(logger, "alpha_vantage", "TIME_SERIES_DAILY", symbol=symbol)

        try:
            # Fetch daily time series
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "full",  # Get full history
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                raise InvalidSymbolError(symbol, data["Error Message"])

            if "Note" in data:
                # Rate limit message
                raise RateLimitError("alpha_vantage", retry_after=86400)  # 24 hours

            if "Time Series (Daily)" not in data:
                raise DataFetchError(
                    symbol,
                    "Invalid API response format",
                    "alpha_vantage",
                )

            time_series = data["Time Series (Daily)"]

            # Filter by date range and build DataFrame
            historical_data = []
            for date_str, values in time_series.items():
                trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                if start_date <= trade_date <= end_date:
                    historical_data.append({
                        "Date": trade_date,
                        "Open": float(values["1. open"]),
                        "High": float(values["2. high"]),
                        "Low": float(values["3. low"]),
                        "Close": float(values["4. close"]),
                        "Volume": int(values["5. volume"]),
                    })

            if not historical_data:
                raise InvalidSymbolError(
                    symbol, "No data available for date range"
                )

            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            # Get most recent data point
            latest = historical_data[-1] if historical_data else None
            if not latest:
                raise InvalidSymbolError(symbol, "No recent data available")

            current_price = latest["Close"]

            # Calculate price change (if we have previous day)
            price_change_percent = 0.0
            if len(historical_data) >= 2:
                prev_close = historical_data[-2]["Close"]
                price_change_percent = ((current_price - prev_close) / prev_close) * 100

            volume = latest["Volume"]

            duration = time.time() - start_time
            log_api_response(logger, "alpha_vantage", "success", duration)
            logger.debug(f"Fetched {len(df)} data points for {symbol} from Alpha Vantage")

            return StockData(
                symbol=symbol.upper(),
                current_price=current_price,
                price_change_percent=price_change_percent,
                volume=volume,
                historical_prices=df,
                fundamentals={},  # Alpha Vantage requires separate API calls for fundamentals
                metadata={
                    "source": "alpha_vantage",
                    "fetch_time": datetime.utcnow().isoformat(),
                    "data_points": len(df),
                },
            )

        except (InvalidSymbolError, RateLimitError) as e:
            log_api_error(logger, "alpha_vantage", e)
            raise
        except requests.RequestException as e:
            log_api_error(logger, "alpha_vantage", e)
            raise DataFetchError(symbol, f"Network error: {str(e)}", "alpha_vantage")
        except Exception as e:
            log_api_error(logger, "alpha_vantage", e)
            raise DataFetchError(symbol, f"Alpha Vantage error: {str(e)}", "alpha_vantage")
