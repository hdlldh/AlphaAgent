"""
Unit tests for retry module.

Tests retry logic with exponential backoff.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

from stock_analyzer.retry import (
    RetryableOperation,
    calculate_backoff,
    handle_rate_limit,
    retry_with_backoff,
)


class TestCalculateBackoff:
    """Test backoff calculation."""

    def test_exponential_backoff_no_jitter(self):
        """Test exponential backoff without jitter."""
        # Base delay = 1.0, exponential_base = 2.0
        delay0 = calculate_backoff(0, base_delay=1.0, jitter=False)
        delay1 = calculate_backoff(1, base_delay=1.0, jitter=False)
        delay2 = calculate_backoff(2, base_delay=1.0, jitter=False)

        assert delay0 == 1.0  # 1.0 * 2^0
        assert delay1 == 2.0  # 1.0 * 2^1
        assert delay2 == 4.0  # 1.0 * 2^2

    def test_exponential_backoff_respects_max_delay(self):
        """Test that backoff doesn't exceed max_delay."""
        delay = calculate_backoff(
            10,  # Large attempt number
            base_delay=1.0,
            max_delay=10.0,
            jitter=False
        )
        assert delay == 10.0  # Should be capped at max_delay

    def test_backoff_with_jitter(self):
        """Test that jitter adds randomness."""
        delays = [
            calculate_backoff(1, base_delay=1.0, jitter=True)
            for _ in range(10)
        ]

        # With jitter, we should get different values
        # (statistically unlikely to get all identical)
        assert len(set(delays)) > 1

        # All delays should be within ±25% of 2.0
        for delay in delays:
            assert 1.5 <= delay <= 2.5

    def test_backoff_never_negative(self):
        """Test that backoff is never negative."""
        for attempt in range(10):
            delay = calculate_backoff(attempt, base_delay=1.0)
            assert delay >= 0


class TestRetryWithBackoffDecorator:
    """Test retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_async_function_succeeds_first_try(self):
        """Test that successful async function is called once."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        async def async_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await async_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_function_retries_on_failure(self):
        """Test that async function retries on failure."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await async_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_function_exhausts_retries(self):
        """Test that async function raises after max attempts."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            await async_func()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_function_only_retries_specified_exceptions(self):
        """Test that decorator only retries specified exception types."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(ValueError,)
        )
        async def async_func():
            nonlocal call_count
            call_count += 1
            raise TypeError("Wrong exception type")

        with pytest.raises(TypeError, match="Wrong exception type"):
            await async_func()

        # Should not retry for TypeError
        assert call_count == 1

    def test_sync_function_succeeds_first_try(self):
        """Test that successful sync function is called once."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        def sync_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = sync_func()
        assert result == "success"
        assert call_count == 1

    def test_sync_function_retries_on_failure(self):
        """Test that sync function retries on failure."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def sync_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = sync_func()
        assert result == "success"
        assert call_count == 3

    def test_sync_function_exhausts_retries(self):
        """Test that sync function raises after max attempts."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def sync_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            sync_func()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_on_retry_callback_is_called(self):
        """Test that on_retry callback is invoked."""
        call_count = 0
        retry_info = []

        def on_retry(exception, attempt, delay):
            retry_info.append({
                "exception": exception,
                "attempt": attempt,
                "delay": delay
            })

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry
        )
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Error {call_count}")
            return "success"

        result = await async_func()
        assert result == "success"
        assert len(retry_info) == 2  # 2 retries before success

        # Check callback was called with correct info
        assert isinstance(retry_info[0]["exception"], ValueError)
        assert retry_info[0]["attempt"] == 0
        assert retry_info[0]["delay"] > 0


class TestHandleRateLimit:
    """Test rate limit handling."""

    def test_handle_rate_limit_with_retry_after(self):
        """Test rate limit handling with retry_after value."""
        delay = handle_rate_limit(retry_after=120.0)
        assert delay == 120.0

    def test_handle_rate_limit_without_retry_after(self):
        """Test rate limit handling without retry_after."""
        delay = handle_rate_limit(retry_after=None, default_delay=90.0)
        assert delay == 90.0

    def test_handle_rate_limit_converts_string_to_float(self):
        """Test that retry_after string is converted to float."""
        delay = handle_rate_limit(retry_after=60)
        assert delay == 60.0
        assert isinstance(delay, float)


class TestRetryableOperation:
    """Test RetryableOperation context manager."""

    @pytest.mark.asyncio
    async def test_should_retry_returns_true_initially(self):
        """Test that should_retry returns True initially."""
        async with RetryableOperation(max_attempts=3) as retry:
            assert retry.should_retry() is True

    @pytest.mark.asyncio
    async def test_should_retry_returns_false_after_max_attempts(self):
        """Test that should_retry returns False after max attempts."""
        async with RetryableOperation(max_attempts=2) as retry:
            assert retry.should_retry() is True
            await retry.record_failure(ValueError("Error 1"))

            assert retry.should_retry() is True
            await retry.record_failure(ValueError("Error 2"))

            # After 2 attempts (max_attempts=2), should not retry
            assert retry.should_retry() is False

    @pytest.mark.asyncio
    async def test_record_failure_increments_attempt(self):
        """Test that record_failure increments attempt counter."""
        async with RetryableOperation(max_attempts=3, base_delay=0.01) as retry:
            assert retry.attempt == 0

            await retry.record_failure(ValueError("Error"))
            assert retry.attempt == 1

            await retry.record_failure(ValueError("Error"))
            assert retry.attempt == 2

    @pytest.mark.asyncio
    async def test_record_failure_returns_false_when_exhausted(self):
        """Test that record_failure returns False when retries exhausted."""
        async with RetryableOperation(max_attempts=2, base_delay=0.01) as retry:
            result1 = await retry.record_failure(ValueError("Error 1"))
            assert result1 is True  # Should retry

            result2 = await retry.record_failure(ValueError("Error 2"))
            assert result2 is False  # Retries exhausted

    @pytest.mark.asyncio
    async def test_record_failure_stores_last_exception(self):
        """Test that record_failure stores the last exception."""
        async with RetryableOperation(max_attempts=3, base_delay=0.01) as retry:
            error1 = ValueError("Error 1")
            error2 = ValueError("Error 2")

            await retry.record_failure(error1)
            assert retry.last_exception is error1

            await retry.record_failure(error2)
            assert retry.last_exception is error2

    @pytest.mark.asyncio
    async def test_retryable_operation_manual_control(self):
        """Test manual retry control with RetryableOperation."""
        call_count = 0

        async with RetryableOperation(max_attempts=3, base_delay=0.01) as retry:
            while retry.should_retry():
                call_count += 1
                if call_count < 3:
                    should_continue = await retry.record_failure(
                        ValueError(f"Error {call_count}")
                    )
                    if not should_continue:
                        break
                else:
                    # Success on 3rd try
                    break

        assert call_count == 3


class TestRetryTiming:
    """Test retry timing and delays."""

    @pytest.mark.asyncio
    async def test_async_retry_respects_delays(self):
        """Test that async retry waits appropriate delays."""
        call_times = []

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False
        )
        async def async_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"

        await async_func()

        # Check that delays are approximately correct
        # First retry: ~0.1s delay (1.0 * 2^0 = 0.1)
        # Second retry: ~0.2s delay (1.0 * 2^1 = 0.2)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.08 <= delay1 <= 0.15  # ~0.1s with some tolerance
        assert 0.18 <= delay2 <= 0.25  # ~0.2s with some tolerance

    def test_sync_retry_respects_delays(self):
        """Test that sync retry waits appropriate delays."""
        call_times = []

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False
        )
        def sync_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"

        sync_func()

        # Check that delays are approximately correct
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert 0.08 <= delay1 <= 0.15  # ~0.1s with some tolerance
        assert 0.18 <= delay2 <= 0.25  # ~0.2s with some tolerance
