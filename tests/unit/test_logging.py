"""
Unit tests for logging module.

Tests structured logging configuration and utilities.
"""

import logging

import pytest

from stock_analyzer.logging import (
    LogContext,
    get_logger,
    log_analysis_complete,
    log_analysis_start,
    log_api_call,
    log_api_error,
    log_api_response,
    log_database_operation,
    log_delivery,
    setup_logging,
)


class TestSetupLogging:
    """Test logging setup and configuration."""

    def test_setup_logging_completes_without_error(self):
        """Test that setup_logging completes without errors."""
        # Should not raise any exceptions
        setup_logging()
        setup_logging(level="DEBUG")
        setup_logging(level="WARNING")

    def test_setup_logging_accepts_custom_format(self):
        """Test setup with custom format string."""
        custom_format = "%(levelname)s - %(message)s"
        # Should not raise any exceptions
        setup_logging(format_string=custom_format)

    def test_setup_logging_accepts_custom_date_format(self):
        """Test setup with custom date format."""
        custom_date = "%Y-%m-%d"
        # Should not raise any exceptions
        setup_logging(date_format=custom_date)


class TestGetLogger:
    """Test logger retrieval."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger(__name__)
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_module_name(self):
        """Test that logger has correct name."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"

    def test_get_logger_different_names_return_different_loggers(self):
        """Test that different names return different logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name != logger2.name


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_completes_without_error(self):
        """Test that LogContext works without errors."""
        logger = get_logger(__name__)

        # Should not raise any exceptions
        with LogContext(logger, operation="test_op", user_id=123):
            logger.info("Test with context")

    def test_log_context_with_multiple_fields(self):
        """Test LogContext with multiple context fields."""
        logger = get_logger(__name__)

        with LogContext(logger, operation="test", symbol="AAPL", user_id=123):
            logger.info("Test message")

        # If we get here without exception, the test passes


class TestConvenienceFunctions:
    """Test convenience logging functions."""

    def test_log_api_call(self):
        """Test log_api_call function."""
        logger = get_logger(__name__)
        # Should not raise exceptions
        log_api_call(logger, "test_provider", "test_method", param1="value1")

    def test_log_api_response(self):
        """Test log_api_response function."""
        logger = get_logger(__name__)
        log_api_response(logger, "test_provider", "success", 1.23)

    def test_log_api_error(self):
        """Test log_api_error function."""
        logger = get_logger(__name__)
        error = ValueError("Test error")
        log_api_error(logger, "test_provider", error)

    def test_log_database_operation(self):
        """Test log_database_operation function."""
        logger = get_logger(__name__)
        log_database_operation(logger, "INSERT", table="users", id=123)

    def test_log_analysis_start(self):
        """Test log_analysis_start function."""
        logger = get_logger(__name__)
        log_analysis_start(logger, "AAPL")
        log_analysis_start(logger, "AAPL", user_id=123)
        log_analysis_start(logger, "AAPL", user_id=None)

    def test_log_analysis_complete(self):
        """Test log_analysis_complete function."""
        logger = get_logger(__name__)
        log_analysis_complete(logger, "AAPL", 2.5, success=True)
        log_analysis_complete(logger, "AAPL", 1.0, success=False)

    def test_log_delivery(self):
        """Test log_delivery function."""
        logger = get_logger(__name__)
        log_delivery(logger, 123, "AAPL", "telegram", success=True)
        log_delivery(logger, 123, "AAPL", "telegram", success=False)


class TestLoggingIntegration:
    """Test logging in realistic scenarios."""

    def test_logging_workflow_completes(self):
        """Test a complete logging workflow."""
        setup_logging(level="INFO")
        logger = get_logger("test_workflow")

        # Simulate analysis workflow - should complete without errors
        log_analysis_start(logger, "AAPL", user_id=123)
        log_api_call(logger, "yfinance", "fetch_data", symbol="AAPL")
        log_api_response(logger, "yfinance", "success", 0.5)
        log_api_call(logger, "claude", "analyze", symbol="AAPL")
        log_api_response(logger, "claude", "success", 2.0)
        log_analysis_complete(logger, "AAPL", 2.5, success=True)
        log_delivery(logger, 123, "AAPL", "telegram", success=True)

    def test_logging_with_errors(self):
        """Test logging when errors occur."""
        logger = get_logger("test_errors")

        # Simulate error scenario - should complete without raising
        error = ValueError("API rate limit exceeded")
        log_api_error(logger, "openai", error)

    def test_multiple_loggers_work(self):
        """Test that multiple loggers can be created."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        logger1.info("Message from module1")
        logger2.info("Message from module2")

        # If we get here, both loggers work
        assert logger1.name == "module1"
        assert logger2.name == "module2"

    def test_all_log_levels_work(self):
        """Test that all log levels can be used."""
        logger = get_logger("test_levels")

        # Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
