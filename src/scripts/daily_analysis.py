#!/usr/bin/env python3
"""
Daily stock analysis job script.

Runs automated stock analysis for all subscribed stocks and delivers insights
to users via Telegram.

This script is designed to run via cron or GitHub Actions on weekdays.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.config import Config
from stock_analyzer.deliverer import InsightDeliverer
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.llm_client import LLMClientFactory
from stock_analyzer.logging import setup_logging, get_logger
from stock_analyzer.storage import Storage

logger = get_logger(__name__)


async def main():
    """
    Main daily analysis workflow.

    Steps:
    1. Load configuration
    2. Get all active subscriptions
    3. Analyze unique stocks
    4. Deliver insights to subscribers
    5. Log job results
    """
    try:
        # Load configuration
        config = Config.from_env()

        # Initialize structured logging
        setup_logging(level=config.log_level)
        logger.info("Starting daily analysis job")
        logger.info(f"Configuration loaded. Database: {config.db_path}")

        # Initialize storage
        storage = Storage(config.db_path)
        storage.init_database()

        # Get all active subscriptions
        subscriptions = storage.get_subscriptions(active_only=True)
        unique_symbols = list(set(sub.stock_symbol for sub in subscriptions))

        if not unique_symbols:
            logger.info("No active subscriptions found. Exiting.")
            return 0

        logger.info(f"Found {len(unique_symbols)} unique stocks to analyze from {len(subscriptions)} subscriptions")

        # Create job record
        job = storage.create_job(stocks_scheduled=len(unique_symbols))
        logger.info(f"Created job ID: {job.id}")

        # Initialize LLM client
        llm_client = LLMClientFactory.create(
            provider=config.llm_provider,
            api_key=config.llm_api_key,
            model=config.llm_model
        )
        logger.info(f"LLM client initialized: {config.llm_provider}")

        # Initialize stock fetcher
        fetcher = StockFetcher(
            primary_provider="yfinance",
            backup_provider="alpha_vantage",
            api_key=config.stock_api_key
        )

        # Initialize analyzer
        analyzer = Analyzer(
            llm_client=llm_client,
            fetcher=fetcher,
            storage=storage
        )

        # Run batch analysis (parallel=2 for reasonable throughput without rate limiting)
        logger.info(f"Analyzing {len(unique_symbols)} stocks...")
        analysis_result = await analyzer.analyze_batch(
            symbols=unique_symbols,
            parallel=2,
            continue_on_error=True
        )

        logger.info(
            f"Analysis complete: {analysis_result.success_count} success, "
            f"{analysis_result.failure_count} failed, "
            f"duration={analysis_result.duration_seconds:.2f}s"
        )

        # Initialize deliverer
        if config.telegram_token:
            deliverer = InsightDeliverer(
                storage=storage,
                telegram_token=config.telegram_token
            )
            logger.info("Delivering insights to subscribers...")

            # Deliver insights for successful analyses
            delivery_count = 0
            delivery_success = 0
            delivery_failed = 0

            for result in analysis_result.results:
                if result.status == "success":
                    # Get the insight for this stock
                    insights = storage.get_insights(result.stock_symbol, limit=1)
                    if insights:
                        insight = insights[0]

                        # Deliver to subscribers of this stock
                        delivery_result = await deliverer.deliver_to_subscribers(
                            insight=insight,
                            channel="telegram"
                        )

                        delivery_count += delivery_result.total
                        delivery_success += delivery_result.success_count
                        delivery_failed += delivery_result.failure_count

            logger.info(
                f"Delivery complete: {delivery_count} total, "
                f"{delivery_success} success, {delivery_failed} failed"
            )

            # Update job with delivery stats
            storage.update_job(
                job.id,
                stocks_processed=analysis_result.total,
                success_count=analysis_result.success_count,
                failure_count=analysis_result.failure_count,
                insights_delivered=delivery_success,
                job_status="completed",
                completion_time=datetime.utcnow(),
                duration_seconds=analysis_result.duration_seconds
            )
        else:
            logger.warning("Telegram token not configured. Skipping delivery.")

            # Update job without delivery
            storage.update_job(
                job.id,
                stocks_processed=analysis_result.total,
                success_count=analysis_result.success_count,
                failure_count=analysis_result.failure_count,
                job_status="completed",
                completion_time=datetime.utcnow(),
                duration_seconds=analysis_result.duration_seconds
            )

        logger.info("Daily analysis job completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("Job cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Job failed with exception: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
