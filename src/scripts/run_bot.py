#!/usr/bin/env python3
"""
Run Telegram bot for local development.

This script starts the bot in polling mode, which is suitable for
development and testing. For production, consider using webhooks.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.bot import TelegramBot
from stock_analyzer.config import Config
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.llm_client import LLMClientFactory
from stock_analyzer.logging import setup_logging, get_logger
from stock_analyzer.storage import Storage

logger = get_logger(__name__)


def main():
    """
    Start the Telegram bot.

    Loads configuration, initializes database and bot, then starts polling.
    """
    try:
        # Load configuration
        config = Config.from_env()

        # Initialize structured logging
        setup_logging(level=config.log_level)
        logger.info("Loading configuration...")

        # Validate Telegram token
        if not config.telegram_token:
            logger.error("TELEGRAM_TOKEN not set in environment")
            logger.error("Please set STOCK_ANALYZER_TELEGRAM_TOKEN or TELEGRAM_TOKEN")
            sys.exit(1)

        # Initialize storage
        logger.info(f"Initializing database: {config.db_path}")
        storage = Storage(config.db_path)
        storage.init_database()

        # Initialize stock fetcher
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider="alpha_vantage",
            api_key=config.stock_api_key
        )

        # Initialize LLM client
        logger.info(f"Initializing LLM client: {config.llm_provider}")
        llm_client = LLMClientFactory.create(
            provider=config.llm_provider,
            api_key=config.llm_api_key,
            model=config.llm_model
        )

        # Initialize analyzer
        analyzer = Analyzer(
            llm_client=llm_client,
            fetcher=fetcher,
            storage=storage
        )

        # Create bot
        logger.info("Initializing Telegram bot...")
        bot = TelegramBot(
            storage=storage,
            token=config.telegram_token,
            fetcher=fetcher,
            analyzer=analyzer
        )

        # Start bot
        logger.info("Starting bot polling...")
        logger.info("Press Ctrl+C to stop")
        bot.run()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
