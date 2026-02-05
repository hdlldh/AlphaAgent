"""
Custom exceptions for stock analyzer system.

All exceptions inherit from StockAnalyzerError for easy catching of any system error.
"""


class StockAnalyzerError(Exception):
    """Base exception for all stock analyzer errors."""

    pass


class InvalidSymbolError(StockAnalyzerError):
    """
    Stock symbol is invalid or not found.

    Raised when:
    - Symbol doesn't exist in market data
    - Symbol is delisted
    - Symbol format is invalid
    """

    def __init__(self, symbol: str, reason: str = "Symbol not found"):
        self.symbol = symbol
        self.reason = reason
        super().__init__(f"Invalid stock symbol '{symbol}': {reason}")


class DataFetchError(StockAnalyzerError):
    """
    Failed to fetch stock data from API.

    Raised when:
    - API request fails
    - Network timeout
    - Invalid API response
    - Both primary and backup APIs fail
    """

    def __init__(self, symbol: str, reason: str, provider: str = None):
        self.symbol = symbol
        self.reason = reason
        self.provider = provider
        provider_info = f" from {provider}" if provider else ""
        super().__init__(f"Failed to fetch data for '{symbol}'{provider_info}: {reason}")


class AnalysisError(StockAnalyzerError):
    """
    LLM analysis operation failed.

    Raised when:
    - LLM API request fails
    - LLM returns invalid response
    - Analysis timeout
    - Token limit exceeded
    """

    def __init__(self, symbol: str, reason: str, model: str = None):
        self.symbol = symbol
        self.reason = reason
        self.model = model
        model_info = f" (model: {model})" if model else ""
        super().__init__(f"Analysis failed for '{symbol}'{model_info}: {reason}")


class DeliveryError(StockAnalyzerError):
    """
    Delivery operation failed.

    Raised when:
    - Telegram API fails
    - Invalid user ID
    - Bot blocked by user
    - Network error during delivery
    """

    def __init__(self, user_id: str, reason: str, channel: str = None):
        self.user_id = user_id
        self.reason = reason
        self.channel = channel
        channel_info = f" via {channel}" if channel else ""
        super().__init__(f"Delivery failed for user '{user_id}'{channel_info}: {reason}")


class StorageError(StockAnalyzerError):
    """
    Database operation failed.

    Raised when:
    - Database connection fails
    - SQL query fails
    - Constraint violation
    - File permission error
    """

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Storage operation '{operation}' failed: {reason}")


class RateLimitError(StockAnalyzerError):
    """
    API rate limit exceeded.

    Raised when:
    - Stock data API rate limit hit
    - LLM API rate limit hit
    - Telegram API rate limit hit
    """

    def __init__(self, provider: str, retry_after: int = None):
        self.provider = provider
        self.retry_after = retry_after
        retry_info = f" (retry after {retry_after}s)" if retry_after else ""
        super().__init__(f"Rate limit exceeded for {provider}{retry_info}")


class SubscriptionLimitError(StockAnalyzerError):
    """
    Subscription limit reached.

    Raised when:
    - User tries to exceed 10 stocks per user limit
    - System tries to exceed 100 total stocks limit
    """

    def __init__(self, limit_type: str, current: int, max_limit: int):
        self.limit_type = limit_type
        self.current = current
        self.max_limit = max_limit
        super().__init__(
            f"{limit_type} subscription limit reached: {current}/{max_limit}"
        )
