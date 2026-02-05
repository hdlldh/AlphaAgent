"""
Configuration management for stock analyzer.

Loads configuration from environment variables, files, or programmatic settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """
    Configuration for stock analyzer system.

    Supports loading from:
    1. Environment variables (STOCK_ANALYZER_*)
    2. .env file
    3. TOML configuration file
    4. Programmatic settings
    """

    # LLM Provider Configuration
    llm_provider: str = "anthropic"  # "anthropic", "openai", or "gemini"
    llm_model: Optional[str] = None  # Uses provider default if None
    llm_api_key: Optional[str] = None
    llm_fallback_provider: Optional[str] = None
    llm_fallback_model: Optional[str] = None

    # Stock Data API Configuration
    stock_data_provider: str = "yfinance"
    stock_data_backup: str = "alpha_vantage"
    stock_api_key: Optional[str] = None  # For Alpha Vantage

    # Telegram Configuration
    telegram_token: Optional[str] = None
    telegram_parse_mode: str = "Markdown"

    # Storage Configuration
    db_path: str = "./data/stock_analyzer.db"
    retention_days: int = 365

    # Limits
    user_limit: int = 10  # Max subscriptions per user
    system_limit: int = 100  # Max total subscriptions
    analysis_timeout: int = 60  # Seconds

    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # Advanced
    mock_mode: bool = False  # For testing
    retry_max: int = 3
    debug: bool = False

    # Provider-specific settings
    anthropic_enable_caching: bool = True
    anthropic_max_tokens: int = 2048
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2048
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables.

        Environment variables:
        - STOCK_ANALYZER_LLM_PROVIDER
        - ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY
        - STOCK_ANALYZER_LLM_MODEL
        - STOCK_ANALYZER_TELEGRAM_TOKEN
        - STOCK_ANALYZER_STOCK_API_KEY
        - STOCK_ANALYZER_DB_PATH
        - STOCK_ANALYZER_LOG_LEVEL
        - STOCK_ANALYZER_USER_LIMIT
        - STOCK_ANALYZER_SYSTEM_LIMIT
        - etc.
        """
        # Load .env file if it exists
        load_dotenv()

        # Determine LLM provider
        provider = os.getenv("STOCK_ANALYZER_LLM_PROVIDER", "anthropic").lower()

        # Get provider-specific API key
        api_key = None
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")

        # Fallback to generic key
        if not api_key:
            api_key = os.getenv("STOCK_ANALYZER_LLM_API_KEY")

        return cls(
            # LLM configuration
            llm_provider=provider,
            llm_model=os.getenv("STOCK_ANALYZER_LLM_MODEL"),
            llm_api_key=api_key,
            # Stock data configuration
            stock_api_key=os.getenv("STOCK_ANALYZER_STOCK_API_KEY"),
            # Telegram configuration
            telegram_token=os.getenv("STOCK_ANALYZER_TELEGRAM_TOKEN"),
            # Storage configuration
            db_path=os.getenv("STOCK_ANALYZER_DB_PATH", "./data/stock_analyzer.db"),
            # Limits
            user_limit=int(os.getenv("STOCK_ANALYZER_USER_LIMIT", "10")),
            system_limit=int(os.getenv("STOCK_ANALYZER_SYSTEM_LIMIT", "100")),
            analysis_timeout=int(os.getenv("STOCK_ANALYZER_ANALYSIS_TIMEOUT", "60")),
            # Logging
            log_level=os.getenv("STOCK_ANALYZER_LOG_LEVEL", "INFO").upper(),
            # Advanced
            mock_mode=os.getenv("STOCK_ANALYZER_MOCK_MODE", "false").lower() == "true",
            retry_max=int(os.getenv("STOCK_ANALYZER_RETRY_MAX", "3")),
            debug=os.getenv("STOCK_ANALYZER_DEBUG", "false").lower() == "true",
        )

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from TOML file.

        Args:
            config_path: Path to config.toml file

        Returns:
            Config instance
        """
        path = Path(config_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Extract configuration sections
        api_config = data.get("api", {})
        limits_config = data.get("limits", {})
        storage_config = data.get("storage", {})
        telegram_config = data.get("telegram", {})
        logging_config = data.get("logging", {})

        # Provider-specific settings
        anthropic_config = api_config.get("anthropic", {})
        openai_config = api_config.get("openai", {})
        gemini_config = api_config.get("gemini", {})

        return cls(
            # LLM configuration
            llm_provider=api_config.get("llm_provider", "anthropic"),
            llm_model=api_config.get("llm_model"),
            llm_api_key=api_config.get("llm_api_key"),
            llm_fallback_provider=api_config.get("llm_fallback_provider"),
            llm_fallback_model=api_config.get("llm_fallback_model"),
            # Stock data configuration
            stock_data_provider=api_config.get("stock_data_provider", "yfinance"),
            stock_data_backup=api_config.get("stock_data_backup", "alpha_vantage"),
            stock_api_key=api_config.get("stock_api_key"),
            # Telegram configuration
            telegram_token=telegram_config.get("token"),
            telegram_parse_mode=telegram_config.get("parse_mode", "Markdown"),
            # Storage configuration
            db_path=storage_config.get("db_path", "./data/stock_analyzer.db"),
            retention_days=storage_config.get("retention_days", 365),
            # Limits
            user_limit=limits_config.get("user_subscriptions_max", 10),
            system_limit=limits_config.get("system_subscriptions_max", 100),
            analysis_timeout=limits_config.get("analysis_timeout_seconds", 60),
            # Logging
            log_level=logging_config.get("level", "INFO").upper(),
            # Provider-specific
            anthropic_enable_caching=anthropic_config.get("enable_prompt_caching", True),
            anthropic_max_tokens=anthropic_config.get("max_tokens", 2048),
            openai_temperature=openai_config.get("temperature", 0.7),
            openai_max_tokens=openai_config.get("max_tokens", 2048),
            gemini_temperature=gemini_config.get("temperature", 0.7),
            gemini_max_output_tokens=gemini_config.get("max_output_tokens", 2048),
        )

    def validate(self) -> None:
        """
        Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.llm_provider not in ["anthropic", "openai", "gemini"]:
            raise ValueError(
                f"Invalid LLM provider: {self.llm_provider}. "
                f"Must be 'anthropic', 'openai', or 'gemini'."
            )

        if not self.llm_api_key:
            raise ValueError(f"LLM API key is required for provider: {self.llm_provider}")

        if not self.telegram_token:
            raise ValueError("Telegram bot token is required")

        if self.user_limit < 1:
            raise ValueError("User limit must be at least 1")

        if self.system_limit < self.user_limit:
            raise ValueError("System limit must be >= user limit")

        if self.analysis_timeout < 10:
            raise ValueError("Analysis timeout must be at least 10 seconds")

    def get_llm_config(self) -> Dict:
        """Get LLM provider-specific configuration."""
        if self.llm_provider == "anthropic":
            return {
                "api_key": self.llm_api_key,
                "model": self.llm_model or "claude-sonnet-4-5-20250929",
                "enable_caching": self.anthropic_enable_caching,
                "max_tokens": self.anthropic_max_tokens,
            }
        elif self.llm_provider == "openai":
            return {
                "api_key": self.llm_api_key,
                "model": self.llm_model or "gpt-4o",
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            }
        elif self.llm_provider == "gemini":
            return {
                "api_key": self.llm_api_key,
                "model": self.llm_model or "gemini-2.5-pro",
                "temperature": self.gemini_temperature,
                "max_output_tokens": self.gemini_max_output_tokens,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


import sys

# Handle tomllib for Python 3.11+
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        # tomli not available, will fail if trying to use from_file()
        pass
