"""
Unit tests for configuration module.

Tests configuration loading and validation.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from stock_analyzer.config import Config


class TestConfigFromEnv:
    """Test Config.from_env() method."""

    def test_from_env_defaults(self, monkeypatch):
        """Test loading config with defaults."""
        # Ensure ambient shell env doesn't override defaults.
        monkeypatch.delenv("STOCK_ANALYZER_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_LLM_MODEL", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_LLM_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_STOCK_API_KEY", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_DB_PATH", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_USER_LIMIT", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_SYSTEM_LIMIT", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_ANALYSIS_TIMEOUT", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_LOG_LEVEL", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_MOCK_MODE", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_RETRY_MAX", raising=False)
        monkeypatch.delenv("STOCK_ANALYZER_DEBUG", raising=False)

        # Set minimal required env vars
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_TOKEN", "test-token")

        with patch("stock_analyzer.config.load_dotenv"):
            config = Config.from_env()

        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "test-key"
        assert config.telegram_token == "test-token"
        assert config.db_path == "./data/stock_analyzer.db"
        assert config.user_limit == 10
        assert config.system_limit == 100

    def test_from_env_anthropic_provider(self, monkeypatch):
        """Test loading Anthropic configuration."""
        monkeypatch.setenv("STOCK_ANALYZER_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        config = Config.from_env()

        assert config.llm_provider == "anthropic"
        assert config.llm_api_key == "sk-ant-test"

    def test_from_env_openai_provider(self, monkeypatch):
        """Test loading OpenAI configuration."""
        monkeypatch.setenv("STOCK_ANALYZER_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        config = Config.from_env()

        assert config.llm_provider == "openai"
        assert config.llm_api_key == "sk-test"

    def test_from_env_gemini_provider(self, monkeypatch):
        """Test loading Gemini configuration."""
        monkeypatch.setenv("STOCK_ANALYZER_LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")

        config = Config.from_env()

        assert config.llm_provider == "gemini"
        assert config.llm_api_key == "gemini-test"

    def test_from_env_custom_values(self, monkeypatch):
        """Test loading config with custom values."""
        monkeypatch.setenv("STOCK_ANALYZER_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("STOCK_ANALYZER_LLM_MODEL", "claude-opus-4")
        monkeypatch.setenv("STOCK_ANALYZER_TELEGRAM_TOKEN", "telegram-token")
        monkeypatch.setenv("STOCK_ANALYZER_STOCK_API_KEY", "av-key")
        monkeypatch.setenv("STOCK_ANALYZER_DB_PATH", "/tmp/test.db")
        monkeypatch.setenv("STOCK_ANALYZER_USER_LIMIT", "20")
        monkeypatch.setenv("STOCK_ANALYZER_SYSTEM_LIMIT", "200")
        monkeypatch.setenv("STOCK_ANALYZER_ANALYSIS_TIMEOUT", "120")
        monkeypatch.setenv("STOCK_ANALYZER_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("STOCK_ANALYZER_MOCK_MODE", "true")
        monkeypatch.setenv("STOCK_ANALYZER_RETRY_MAX", "5")
        monkeypatch.setenv("STOCK_ANALYZER_DEBUG", "true")

        config = Config.from_env()

        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-opus-4"
        assert config.llm_api_key == "test-key"
        assert config.telegram_token == "telegram-token"
        assert config.stock_api_key == "av-key"
        assert config.db_path == "/tmp/test.db"
        assert config.user_limit == 20
        assert config.system_limit == 200
        assert config.analysis_timeout == 120
        assert config.log_level == "DEBUG"
        assert config.mock_mode is True
        assert config.retry_max == 5
        assert config.debug is True


class TestConfigValidation:
    """Test Config.validate() method."""

    def test_validate_valid_config(self):
        """Test validation with valid config."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            telegram_token="telegram-token",
            user_limit=10,
            system_limit=100,
            analysis_timeout=60
        )

        # Should not raise
        config.validate()

    def test_validate_invalid_llm_provider(self):
        """Test validation with invalid LLM provider."""
        config = Config(
            llm_provider="invalid",
            llm_api_key="test-key",
            telegram_token="telegram-token"
        )

        with pytest.raises(ValueError, match="Invalid LLM provider"):
            config.validate()

    def test_validate_missing_api_key(self):
        """Test validation with missing API key."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key=None,
            telegram_token="telegram-token"
        )

        with pytest.raises(ValueError, match="API key is required"):
            config.validate()

    def test_validate_missing_telegram_token(self):
        """Test validation with missing Telegram token."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            telegram_token=None
        )

        with pytest.raises(ValueError, match="Telegram bot token is required"):
            config.validate()

    def test_validate_invalid_user_limit(self):
        """Test validation with invalid user limit."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            telegram_token="telegram-token",
            user_limit=0
        )

        with pytest.raises(ValueError, match="User limit must be at least 1"):
            config.validate()

    def test_validate_invalid_system_limit(self):
        """Test validation with system limit < user limit."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            telegram_token="telegram-token",
            user_limit=20,
            system_limit=10
        )

        with pytest.raises(ValueError, match="System limit must be >= user limit"):
            config.validate()

    def test_validate_invalid_analysis_timeout(self):
        """Test validation with too short analysis timeout."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            telegram_token="telegram-token",
            analysis_timeout=5
        )

        with pytest.raises(ValueError, match="Analysis timeout must be at least 10"):
            config.validate()


class TestGetLLMConfig:
    """Test Config.get_llm_config() method."""

    def test_get_llm_config_anthropic(self):
        """Test getting Anthropic LLM config."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model="claude-opus-4",
            anthropic_enable_caching=True,
            anthropic_max_tokens=4096
        )

        llm_config = config.get_llm_config()

        assert llm_config["api_key"] == "test-key"
        assert llm_config["model"] == "claude-opus-4"
        assert llm_config["enable_caching"] is True
        assert llm_config["max_tokens"] == 4096

    def test_get_llm_config_anthropic_default_model(self):
        """Test getting Anthropic config with default model."""
        config = Config(
            llm_provider="anthropic",
            llm_api_key="test-key",
            llm_model=None
        )

        llm_config = config.get_llm_config()

        assert "claude-sonnet" in llm_config["model"]

    def test_get_llm_config_openai(self):
        """Test getting OpenAI LLM config."""
        config = Config(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4-turbo",
            openai_temperature=0.8,
            openai_max_tokens=2048
        )

        llm_config = config.get_llm_config()

        assert llm_config["api_key"] == "test-key"
        assert llm_config["model"] == "gpt-4-turbo"
        assert llm_config["temperature"] == 0.8
        assert llm_config["max_tokens"] == 2048

    def test_get_llm_config_openai_default_model(self):
        """Test getting OpenAI config with default model."""
        config = Config(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model=None
        )

        llm_config = config.get_llm_config()

        assert llm_config["model"] == "gpt-4o"

    def test_get_llm_config_gemini(self):
        """Test getting Gemini LLM config."""
        config = Config(
            llm_provider="gemini",
            llm_api_key="test-key",
            llm_model="gemini-pro",
            gemini_temperature=0.9,
            gemini_max_output_tokens=1024
        )

        llm_config = config.get_llm_config()

        assert llm_config["api_key"] == "test-key"
        assert llm_config["model"] == "gemini-pro"
        assert llm_config["temperature"] == 0.9
        assert llm_config["max_output_tokens"] == 1024

    def test_get_llm_config_gemini_default_model(self):
        """Test getting Gemini config with default model."""
        config = Config(
            llm_provider="gemini",
            llm_api_key="test-key",
            llm_model=None
        )

        llm_config = config.get_llm_config()

        assert llm_config["model"] == "gemini-2.5-pro"

    def test_get_llm_config_unknown_provider(self):
        """Test getting config for unknown provider."""
        config = Config(
            llm_provider="unknown",
            llm_api_key="test-key"
        )

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            config.get_llm_config()


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_llm_provider(self):
        """Test default LLM provider is Anthropic."""
        config = Config()
        assert config.llm_provider == "anthropic"

    def test_default_stock_data_provider(self):
        """Test default stock data provider is yfinance."""
        config = Config()
        assert config.stock_data_provider == "yfinance"
        assert config.stock_data_backup == "alpha_vantage"

    def test_default_telegram_parse_mode(self):
        """Test default Telegram parse mode."""
        config = Config()
        assert config.telegram_parse_mode == "Markdown"

    def test_default_limits(self):
        """Test default subscription limits."""
        config = Config()
        assert config.user_limit == 10
        assert config.system_limit == 100
        assert config.analysis_timeout == 60

    def test_default_log_level(self):
        """Test default log level."""
        config = Config()
        assert config.log_level == "INFO"

    def test_default_advanced_settings(self):
        """Test default advanced settings."""
        config = Config()
        assert config.mock_mode is False
        assert config.retry_max == 3
        assert config.debug is False


class TestStockListParsing:
    """Test stock list parsing with various input formats."""

    def test_parse_stock_list_with_whitespace(self):
        """Test parsing handles leading/trailing whitespace per symbol."""
        config = Config(
            stock_list=" AAPL , MSFT,  GOOGL  ",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        # Should strip whitespace from each symbol
        assert symbols == ["AAPL", "MSFT", "GOOGL"]
        assert all(sym == sym.strip() for sym in symbols)

    def test_parse_stock_list_with_duplicates(self):
        """Test parsing removes duplicate symbols."""
        config = Config(
            stock_list="AAPL,MSFT,AAPL,GOOGL,msft,TSLA,aapl",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        # Should deduplicate (case-insensitive) and preserve first occurrence order
        assert symbols == ["AAPL", "MSFT", "GOOGL", "TSLA"]
        assert len(symbols) == len(set(symbols))

    def test_parse_stock_list_empty_segments(self):
        """Test parsing handles empty segments from multiple commas."""
        config = Config(
            stock_list="AAPL,,MSFT,,,GOOGL,",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        # Should filter out empty segments
        assert symbols == ["AAPL", "MSFT", "GOOGL"]
        assert "" not in symbols

    def test_parse_stock_list_case_normalization(self):
        """Test parsing normalizes all symbols to uppercase."""
        config = Config(
            stock_list="aapl,Msft,GOOGL,tSlA",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        # All symbols should be uppercase
        assert all(sym.isupper() for sym in symbols)
        assert symbols == ["AAPL", "MSFT", "GOOGL", "TSLA"]


class TestStockListInvalidFormatting:
    """Test stock list parsing with invalid input formats."""

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty list."""
        config = Config(
            stock_list="",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        assert symbols == []

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns empty list."""
        config = Config(
            stock_list="   ",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        assert symbols == []

    def test_parse_commas_only(self):
        """Test parsing commas-only string returns empty list."""
        config = Config(
            stock_list=",,,",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        assert symbols == []

    def test_parse_mixed_whitespace_and_commas(self):
        """Test parsing mixed whitespace and commas returns empty list."""
        config = Config(
            stock_list=" , , , ",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test"
        )

        symbols = config.get_stock_symbols()

        assert symbols == []


class TestStockSymbolValidation:
    """Test stock symbol validation rules."""

    def test_validate_valid_symbols(self):
        """Test validation accepts standard stock symbols."""
        config = Config(
            stock_list="AAPL,MSFT,GOOGL,BRK.B",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test",
            llm_provider="anthropic"
        )

        # Should not raise
        config.validate()
        symbols = config.get_stock_symbols()
        assert "AAPL" in symbols
        assert "BRK.B" in symbols  # Symbols with dots are valid

    def test_validate_symbol_with_special_chars(self):
        """Test validation accepts symbols with hyphens and dots."""
        config = Config(
            stock_list="BRK.B,BF.B,GOOG",
            llm_api_key="test-key",
            telegram_token="test-token",
            telegram_channel="@test",
            llm_provider="anthropic"
        )

        # Dots and hyphens should be allowed
        config.validate()
        symbols = config.get_stock_symbols()
        assert "BRK.B" in symbols
        assert "BF.B" in symbols
