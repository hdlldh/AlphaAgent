"""
Retry utilities with exponential backoff for API calls.

Provides decorators and utilities for handling transient failures in external API calls
with configurable retry logic and exponential backoff.
"""

import asyncio
import random
import time
from functools import wraps
from typing import Callable, Optional, Type, Union

from stock_analyzer.exceptions import RateLimitError
from stock_analyzer.logging import get_logger

logger = get_logger(__name__)


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> float:
    """
    Calculate backoff delay with exponential backoff and optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Add random jitter to prevent thundering herd

    Returns:
        Delay in seconds
    """
    # Calculate exponential delay
    delay = min(base_delay * (exponential_base ** attempt), max_delay)

    # Add jitter (±25% of delay)
    if jitter:
        jitter_range = delay * 0.25
        delay = delay + random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
):
    """
    Decorator for retrying function calls with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Add random jitter to delays
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback called on each retry (exception, attempt, delay)

    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            return await api_call()
    """

    def decorator(func: Callable):
        """Decorator function that applies retry logic."""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Async wrapper that implements retry with backoff."""
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        logger.warning(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}"
                        )
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter,
                    )

                    logger.info(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s (error: {type(e).__name__})"
                    )

                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, delay)

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # All retries exhausted, raise last exception
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Sync wrapper that implements retry with backoff."""
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        logger.warning(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}"
                        )
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter,
                    )

                    logger.info(
                        f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s (error: {type(e).__name__})"
                    )

                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, delay)

                    # Wait before retrying
                    time.sleep(delay)

            # All retries exhausted, raise last exception
            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def handle_rate_limit(
    retry_after: Optional[float] = None,
    default_delay: float = 60.0,
) -> float:
    """
    Handle rate limit error and return appropriate delay.

    Args:
        retry_after: Retry-After value from API (seconds)
        default_delay: Default delay if retry_after not provided

    Returns:
        Delay in seconds before retry
    """
    if retry_after is not None:
        delay = float(retry_after)
        logger.warning(f"Rate limited. Waiting {delay}s before retry.")
        return delay
    else:
        logger.warning(f"Rate limited. Using default delay of {default_delay}s.")
        return default_delay


class RetryableOperation:
    """
    Context manager for retryable operations with manual retry control.

    Example:
        async with RetryableOperation(max_attempts=3) as retry:
            while retry.should_retry():
                try:
                    result = await api_call()
                    return result
                except Exception as e:
                    if not retry.record_failure(e):
                        raise
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.attempt = 0
        self.last_exception = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Suppress exceptions if we want to handle them manually
        return False

    def should_retry(self) -> bool:
        """Check if we should continue retrying."""
        return self.attempt < self.max_attempts

    async def record_failure(self, exception: Exception) -> bool:
        """
        Record a failure and sleep if appropriate.

        Returns:
            True if we should retry, False if retries exhausted
        """
        self.last_exception = exception
        self.attempt += 1

        if self.attempt >= self.max_attempts:
            logger.warning(f"All {self.max_attempts} attempts exhausted")
            return False

        delay = calculate_backoff(
            attempt=self.attempt - 1,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            exponential_base=self.exponential_base,
            jitter=self.jitter,
        )

        logger.info(
            f"Retry attempt {self.attempt}/{self.max_attempts} "
            f"after {delay:.2f}s (error: {type(exception).__name__})"
        )

        await asyncio.sleep(delay)
        return True
