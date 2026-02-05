"""
Structured logging configuration for stock analyzer.

Provides centralized logging setup with:
- Consistent formatting across all modules
- Contextual information (module, function, line number)
- Log levels from configuration
- Structured output for production monitoring
"""

import logging
import sys
from typing import Optional

# Default format for structured logging
DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (uses DEFAULT_FORMAT if None)
        date_format: Custom date format string (uses DEFAULT_DATE_FORMAT if None)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=format_string or DEFAULT_FORMAT,
        datefmt=date_format or DEFAULT_DATE_FORMAT,
        stream=sys.stdout,
        force=True,  # Override any existing configuration
    )

    # Set specific loggers to appropriate levels
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("anthropic").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {level} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding contextual information to logs.

    Usage:
        with LogContext(logger, operation="analyze_stock", symbol="AAPL"):
            logger.info("Starting analysis")
            # ... do work ...
            logger.info("Completed analysis")
    """

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        # Store the old factory
        self.old_factory = logging.getLogRecordFactory()

        # Create a new factory that adds context
        def record_factory(*args, **kwargs):
            """Factory function that adds context fields to log records."""
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore the old factory
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Convenience functions for common logging patterns
def log_api_call(logger: logging.Logger, provider: str, method: str, **kwargs):
    """Log an API call with structured information."""
    logger.debug(f"API call: provider={provider} method={method} kwargs={kwargs}")


def log_api_response(logger: logging.Logger, provider: str, status: str, duration: float):
    """Log an API response with timing information."""
    logger.debug(f"API response: provider={provider} status={status} duration={duration:.2f}s")


def log_api_error(logger: logging.Logger, provider: str, error: Exception):
    """Log an API error with exception details."""
    logger.error(f"API error: provider={provider} error={type(error).__name__}: {error}")


def log_database_operation(logger: logging.Logger, operation: str, **kwargs):
    """Log a database operation."""
    logger.debug(f"DB operation: {operation} kwargs={kwargs}")


def log_analysis_start(logger: logging.Logger, symbol: str, user_id: Optional[int] = None):
    """Log the start of a stock analysis."""
    user_info = f"user_id={user_id}" if user_id else "scheduled"
    logger.info(f"Starting stock analysis: symbol={symbol} {user_info}")


def log_analysis_complete(logger: logging.Logger, symbol: str, duration: float, success: bool):
    """Log completion of a stock analysis."""
    status = "success" if success else "failed"
    logger.info(f"Completed stock analysis: symbol={symbol} duration={duration:.2f}s status={status}")


def log_delivery(logger: logging.Logger, user_id: int, symbol: str, channel: str, success: bool):
    """Log insight delivery."""
    status = "success" if success else "failed"
    logger.info(f"Insight delivery: user_id={user_id} symbol={symbol} channel={channel} status={status}")
