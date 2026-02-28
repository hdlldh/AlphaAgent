"""
Command-line interface for stock analyzer.

Provides commands for analyzing stocks, running batch analyses, and managing
the daily analysis job.
"""

import json
import sys
from datetime import date as date_type
from typing import List, Optional

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.config import Config
from stock_analyzer.exceptions import (
    AnalysisError,
    DataFetchError,
    InvalidSymbolError,
    StockAnalyzerError,
)
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.llm_client import LLMClientFactory
from stock_analyzer.logging import setup_logging, get_logger
from stock_analyzer.storage import Storage

logger = get_logger(__name__)


class CLI:
    """Command-line interface for stock analyzer."""

    def __init__(
        self,
        config: Optional[Config] = None,
        db_path: Optional[str] = None,
        analyzer: Optional[Analyzer] = None
    ):
        """
        Initialize CLI.

        Args:
            config: Configuration object (loads from env if None)
            db_path: Database path (uses config if None)
            analyzer: Analyzer instance (creates if None)
        """
        self.config = config or Config.from_env()
        self.db_path = db_path or self.config.db_path

        # Initialize logging
        setup_logging(level=self.config.log_level)
        logger.debug(f"CLI initialized with db_path={self.db_path}")

        # Initialize components
        self.storage = Storage(self.db_path)
        self.storage.init_database()

        if analyzer:
            self.analyzer = analyzer
        else:
            # Create analyzer
            llm_client = LLMClientFactory.create(
                provider=self.config.llm_provider,
                api_key=self.config.llm_api_key,
                model=self.config.llm_model,
            )
            fetcher = StockFetcher(
                primary_provider="yfinance",
                backup_provider="alpha_vantage",
                api_key=self.config.stock_api_key,
            )
            self.analyzer = Analyzer(
                llm_client=llm_client, fetcher=fetcher, storage=self.storage
            )

    async def analyze(
        self,
        symbol: str,
        date: Optional[date_type] = None,
        force: bool = False,
        json_output: bool = False,
    ) -> int:
        """
        Analyze a single stock.

        Args:
            symbol: Stock symbol
            date: Analysis date (defaults to today)
            force: Force re-analysis even if exists
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=invalid symbol, 2=data fetch error, 3=analysis error)
        """
        try:
            insight = await self.analyzer.analyze_stock(symbol, date=date, force=force)

            if json_output:
                output = {
                    "status": "success",
                    "stock_symbol": insight.stock_symbol,
                    "analysis_date": insight.analysis_date.isoformat(),
                    "summary": insight.summary,
                    "trend_analysis": insight.trend_analysis,
                    "risk_factors": insight.risk_factors,
                    "opportunities": insight.opportunities,
                    "confidence_level": insight.confidence_level,
                    "metadata": insight.metadata,
                }
                print(json.dumps(output, indent=2))
            else:
                # Human-readable format
                print(f"\n{'=' * 70}")
                print(f"Stock Analysis: {insight.stock_symbol}")
                print(f"Date: {insight.analysis_date}")
                print(f"Confidence: {insight.confidence_level.upper()}")
                print(f"{'=' * 70}\n")

                print(f"Summary:\n{insight.summary}\n")

                if insight.trend_analysis:
                    print(f"Trend Analysis:\n{insight.trend_analysis}\n")

                if insight.risk_factors:
                    print("Risk Factors:")
                    for risk in insight.risk_factors:
                        print(f"  • {risk}")
                    print()

                if insight.opportunities:
                    print("Opportunities:")
                    for opp in insight.opportunities:
                        print(f"  • {opp}")
                    print()

            return 0

        except InvalidSymbolError as e:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "error_type": "invalid_symbol",
                            "error_message": str(e),
                        }
                    )
                )
            else:
                print(f"Error: Invalid symbol '{symbol}' - {e}", file=sys.stderr)
            return 1

        except DataFetchError as e:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "error_type": "data_fetch",
                            "error_message": str(e),
                        }
                    )
                )
            else:
                print(f"Error: Failed to fetch data for '{symbol}' - {e}", file=sys.stderr)
            return 2

        except AnalysisError as e:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "error_type": "analysis",
                            "error_message": str(e),
                        }
                    )
                )
            else:
                print(f"Error: Analysis failed for '{symbol}' - {e}", file=sys.stderr)
            return 3

        except Exception as e:
            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "error_type": "unknown",
                            "error_message": str(e),
                        }
                    )
                )
            else:
                print(f"Error: Unexpected error - {e}", file=sys.stderr)
            return 3

    async def analyze_batch(
        self,
        symbols: List[str],
        parallel: int = 1,
        continue_on_error: bool = False,
        json_output: bool = False,
    ) -> int:
        """
        Analyze multiple stocks in batch.

        Args:
            symbols: List of stock symbols
            parallel: Number of parallel analyses
            continue_on_error: Continue on individual failures
            json_output: Output as JSON

        Returns:
            Exit code (0=success)
        """
        try:
            result = await self.analyzer.analyze_batch(
                symbols, parallel=parallel, continue_on_error=continue_on_error
            )

            if json_output:
                results_list = []
                for r in result.results:
                    result_dict = {
                        "stock_symbol": r.stock_symbol,
                        "status": r.status,
                    }
                    # Only include error_message if it's a string
                    if hasattr(r, 'error_message') and isinstance(r.error_message, str):
                        result_dict["error_message"] = r.error_message
                    results_list.append(result_dict)

                output = {
                    "status": "success",
                    "total": result.total,
                    "success_count": result.success_count,
                    "failure_count": result.failure_count,
                    "duration_seconds": result.duration_seconds,
                    "results": results_list,
                }
                print(json.dumps(output, indent=2))
            else:
                # Human-readable format
                print(f"\n{'=' * 70}")
                print(f"Batch Analysis Results")
                print(f"{'=' * 70}")
                print(f"Total: {result.total}")
                print(f"Success: {result.success_count}")
                print(f"Failed: {result.failure_count}")
                print(f"Duration: {result.duration_seconds:.2f}s")
                print(f"{'=' * 70}\n")

                if result.failure_count > 0:
                    print("Failed analyses:")
                    for r in result.results:
                        if r.status == "error":
                            print(f"  • {r.stock_symbol}: {r.error_message}")
                    print()

            return 0

        except Exception as e:
            if json_output:
                print(
                    json.dumps(
                        {"status": "error", "error_message": str(e)}
                    )
                )
            else:
                print(f"Error: Batch analysis failed - {e}", file=sys.stderr)
            return 1

    async def run_daily_job(
        self, dry_run: bool = False, json_output: bool = False
    ) -> int:
        """
        Run the daily analysis job.

        Args:
            dry_run: If True, show what would be analyzed without running
            json_output: Output as JSON

        Returns:
            Exit code (0=success)
        """
        try:
            # Get all active subscriptions
            symbols = self._get_active_subscriptions()

            if not symbols:
                if json_output:
                    print(
                        json.dumps(
                            {"status": "success", "message": "No active subscriptions"}
                        )
                    )
                else:
                    print("No active subscriptions to analyze.")
                return 0

            if dry_run:
                if json_output:
                    print(
                        json.dumps(
                            {
                                "status": "success",
                                "dry_run": True,
                                "stocks_scheduled": len(symbols),
                                "symbols": symbols,
                            }
                        )
                    )
                else:
                    print(f"\nDRY RUN - Would analyze {len(symbols)} stocks:")
                    for symbol in symbols:
                        print(f"  • {symbol}")
                    print()
                return 0

            # Create job
            job = self.storage.create_job(stocks_scheduled=len(symbols))

            # Run batch analysis
            result = await self.analyzer.analyze_batch(
                symbols, parallel=2, continue_on_error=True
            )

            # Update job
            self.storage.update_job(
                job.id,
                stocks_processed=result.total,
                success_count=result.success_count,
                failure_count=result.failure_count,
                job_status="completed",
            )

            if json_output:
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "job_id": job.id,
                            "stocks_scheduled": len(symbols),
                            "total": result.total,
                            "success_count": result.success_count,
                            "failure_count": result.failure_count,
                            "duration_seconds": result.duration_seconds,
                        }
                    )
                )
            else:
                print(f"\n{'=' * 70}")
                print(f"Daily Analysis Job Completed")
                print(f"{'=' * 70}")
                print(f"Job ID: {job.id}")
                print(f"Stocks analyzed: {result.total}")
                print(f"Success: {result.success_count}")
                print(f"Failed: {result.failure_count}")
                print(f"Duration: {result.duration_seconds:.2f}s")
                print(f"{'=' * 70}\n")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({"status": "error", "error_message": str(e)}))
            else:
                print(f"Error: Daily job failed - {e}", file=sys.stderr)
            return 1

    def _get_active_subscriptions(self) -> List[str]:
        """Get list of unique stock symbols from active subscriptions."""
        subscriptions = self.storage.get_subscriptions(active_only=True)
        # Return unique symbols
        return list(set(sub.stock_symbol for sub in subscriptions))

    async def subscribe(
        self,
        user_id: str,
        symbol: str,
        json_output: bool = False
    ) -> int:
        """
        Subscribe a user to a stock.

        Args:
            user_id: User ID (Telegram ID)
            symbol: Stock symbol
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            from stock_analyzer.models import Subscription

            # Normalize symbol
            symbol = symbol.upper().strip()

            # Check if already subscribed
            existing = self.storage.get_subscriptions(
                user_id=user_id,
                stock_symbol=symbol,
                active_only=True
            )
            if existing:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": f"Already subscribed to {symbol}"
                    }))
                else:
                    print(f"Already subscribed to {symbol}")
                return 1

            # Check subscription limit
            count = self.storage.get_subscription_count(user_id=user_id, active_only=True)
            if count >= 10:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": f"Subscription limit reached ({count}/10)"
                    }))
                else:
                    print(f"Error: Subscription limit reached ({count}/10)", file=sys.stderr)
                return 1

            # Validate symbol
            is_valid = await self.analyzer.fetcher.validate_symbol(symbol)
            if not is_valid:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": f"Invalid symbol: {symbol}"
                    }))
                else:
                    print(f"Error: Invalid symbol: {symbol}", file=sys.stderr)
                return 1

            # Add subscription
            subscription = Subscription(
                user_id=user_id,
                stock_symbol=symbol
            )
            self.storage.add_subscription(subscription)

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "user_id": user_id,
                    "symbol": symbol,
                    "subscription_count": count + 1
                }))
            else:
                print(f"✓ Successfully subscribed {user_id} to {symbol}")
                print(f"  Subscriptions: {count + 1}/10")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to subscribe - {e}", file=sys.stderr)
            return 1

    def unsubscribe(
        self,
        user_id: str,
        symbol: str,
        json_output: bool = False
    ) -> int:
        """
        Unsubscribe a user from a stock.

        Args:
            user_id: User ID (Telegram ID)
            symbol: Stock symbol
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            # Normalize symbol
            symbol = symbol.upper().strip()

            # Check if subscribed
            existing = self.storage.get_subscriptions(
                user_id=user_id,
                stock_symbol=symbol,
                active_only=True
            )
            if not existing:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": f"Not subscribed to {symbol}"
                    }))
                else:
                    print(f"Error: Not subscribed to {symbol}", file=sys.stderr)
                return 1

            # Remove subscription
            self.storage.remove_subscription(user_id, symbol)

            # Get updated count
            count = self.storage.get_subscription_count(user_id=user_id, active_only=True)

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "user_id": user_id,
                    "symbol": symbol,
                    "subscription_count": count
                }))
            else:
                print(f"✓ Successfully unsubscribed {user_id} from {symbol}")
                print(f"  Remaining subscriptions: {count}/10")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to unsubscribe - {e}", file=sys.stderr)
            return 1

    def list_subscriptions(
        self,
        user_id: Optional[str] = None,
        json_output: bool = False
    ) -> int:
        """
        List subscriptions.

        Args:
            user_id: Optional user ID to filter by. If None, list all.
            json_output: Output as JSON

        Returns:
            Exit code (0=success)
        """
        try:
            # Get subscriptions
            subscriptions = self.storage.get_subscriptions(
                user_id=user_id,
                active_only=True
            )

            if json_output:
                subs_list = [
                    {
                        "user_id": sub.user_id,
                        "stock_symbol": sub.stock_symbol,
                        "subscription_date": sub.subscription_date.isoformat() if sub.subscription_date else None
                    }
                    for sub in subscriptions
                ]
                print(json.dumps({
                    "status": "success",
                    "total": len(subscriptions),
                    "subscriptions": subs_list
                }))
            else:
                if not subscriptions:
                    print("No active subscriptions found.")
                    return 0

                # Group by user if listing all
                if user_id:
                    print(f"\nSubscriptions for user {user_id}:")
                    print(f"{'=' * 70}")
                    for sub in sorted(subscriptions, key=lambda s: s.stock_symbol):
                        sub_date = sub.subscription_date.strftime("%Y-%m-%d") if sub.subscription_date else "N/A"
                        print(f"  • {sub.stock_symbol} (since {sub_date})")
                    count = len(subscriptions)
                    print(f"{'=' * 70}")
                    print(f"Total: {count}/10\n")
                else:
                    # Group by user
                    by_user = {}
                    for sub in subscriptions:
                        if sub.user_id not in by_user:
                            by_user[sub.user_id] = []
                        by_user[sub.user_id].append(sub)

                    print(f"\nAll Active Subscriptions:")
                    print(f"{'=' * 70}")
                    for uid, subs in sorted(by_user.items()):
                        symbols = ", ".join(sorted(s.stock_symbol for s in subs))
                        print(f"  {uid}: {symbols} ({len(subs)}/10)")
                    print(f"{'=' * 70}")
                    print(f"Total users: {len(by_user)}")
                    print(f"Total subscriptions: {len(subscriptions)}\n")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to list subscriptions - {e}", file=sys.stderr)
            return 1

    async def validate(
        self,
        symbol: str,
        json_output: bool = False
    ) -> int:
        """
        Validate a stock symbol.

        Args:
            symbol: Stock symbol to validate
            json_output: Output as JSON

        Returns:
            Exit code (0=valid, 1=invalid)
        """
        try:
            # Normalize symbol
            symbol = symbol.upper().strip()

            # Validate
            is_valid = await self.analyzer.fetcher.validate_symbol(symbol)

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "symbol": symbol,
                    "valid": is_valid
                }))
            else:
                if is_valid:
                    print(f"✓ {symbol} is a valid stock symbol")
                else:
                    print(f"✗ {symbol} is not a valid stock symbol")

            return 0 if is_valid else 1

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Validation failed - {e}", file=sys.stderr)
            return 1

    def history(
        self,
        symbol: str,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        limit: int = 30,
        offset: int = 0,
        json_output: bool = False
    ) -> int:
        """
        Get historical insights for a stock.

        Args:
            symbol: Stock symbol
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            limit: Maximum number of insights to return
            offset: Number of insights to skip (for pagination)
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            # Normalize symbol
            symbol = symbol.upper().strip()

            # Get insights
            insights = self.storage.get_insights(
                stock_symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )

            if json_output:
                insights_list = [
                    {
                        "stock_symbol": i.stock_symbol,
                        "analysis_date": i.analysis_date.isoformat(),
                        "summary": i.summary,
                        "trend_analysis": i.trend_analysis,
                        "risk_factors": i.risk_factors,
                        "opportunities": i.opportunities,
                        "confidence_level": i.confidence_level,
                        "created_at": i.created_at.isoformat() if i.created_at else None
                    }
                    for i in insights
                ]
                print(json.dumps({
                    "status": "success",
                    "symbol": symbol,
                    "total": len(insights),
                    "limit": limit,
                    "offset": offset,
                    "insights": insights_list
                }))
            else:
                if not insights:
                    print(f"No insights found for {symbol}")
                    if start_date or end_date:
                        date_range = ""
                        if start_date:
                            date_range += f" from {start_date}"
                        if end_date:
                            date_range += f" to {end_date}"
                        print(f"Date range:{date_range}")
                    return 0

                # Table header
                print(f"\n{'=' * 100}")
                print(f"Historical Insights for {symbol}")
                if start_date or end_date:
                    date_range = ""
                    if start_date:
                        date_range += f" from {start_date}"
                    if end_date:
                        date_range += f" to {end_date}"
                    print(f"Date range:{date_range}")
                print(f"{'=' * 100}\n")

                # Display insights
                for i, insight in enumerate(insights, start=offset + 1):
                    print(f"[{i}] {insight.analysis_date} - Confidence: {insight.confidence_level.upper()}")
                    print(f"\n{insight.summary}\n")

                    if insight.trend_analysis:
                        print(f"Trend: {insight.trend_analysis}\n")

                    if insight.risk_factors:
                        print("Risks:")
                        for risk in insight.risk_factors:
                            print(f"  • {risk}")
                        print()

                    if insight.opportunities:
                        print("Opportunities:")
                        for opp in insight.opportunities:
                            print(f"  • {opp}")
                        print()

                    print(f"{'-' * 100}\n")

                # Summary
                print(f"{'=' * 100}")
                print(f"Showing {len(insights)} insights (offset: {offset}, limit: {limit})")
                print(f"{'=' * 100}\n")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to fetch history - {e}", file=sys.stderr)
            return 1

    def init_db(
        self,
        json_output: bool = False
    ) -> int:
        """
        Initialize the database.

        Creates the database file and all tables if they don't exist.
        Safe to run multiple times (idempotent).

        Args:
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            # Check if database already exists
            import os
            db_exists = os.path.exists(self.db_path)

            # Initialize database (idempotent)
            self.storage.init_database()

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "database_path": self.db_path,
                    "already_existed": db_exists
                }))
            else:
                if db_exists:
                    print(f"✓ Database already initialized: {self.db_path}")
                else:
                    print(f"✓ Database created successfully: {self.db_path}")

                print("\nDatabase tables:")
                print("  • users")
                print("  • subscriptions")
                print("  • stock_analyses")
                print("  • insights")
                print("  • delivery_logs")
                print("  • analysis_jobs")
                print("\nDatabase ready for use!")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to initialize database - {e}", file=sys.stderr)
            return 1

    def stats(
        self,
        json_output: bool = False
    ) -> int:
        """
        Display system statistics.

        Shows:
        - Total subscriptions (per user and system-wide)
        - Total analyses performed
        - Total insights generated
        - Recent job statistics
        - Database statistics

        Args:
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            from datetime import datetime, timedelta

            # Get subscription statistics
            all_subscriptions = self.storage.get_subscriptions(active_only=True)
            unique_users = len(set(sub.user_id for sub in all_subscriptions))
            unique_stocks = len(set(sub.stock_symbol for sub in all_subscriptions))

            # Get subscription counts per user
            user_sub_counts = {}
            for sub in all_subscriptions:
                user_sub_counts[sub.user_id] = user_sub_counts.get(sub.user_id, 0) + 1

            avg_subs_per_user = len(all_subscriptions) / unique_users if unique_users > 0 else 0
            max_subs_per_user = max(user_sub_counts.values()) if user_sub_counts else 0

            # Get analysis statistics
            conn = self.storage._get_connection()
            cursor = conn.cursor()

            # Total analyses
            cursor.execute("SELECT COUNT(*) FROM stock_analyses")
            total_analyses = cursor.fetchone()[0]

            # Successful analyses
            cursor.execute("SELECT COUNT(*) FROM stock_analyses WHERE analysis_status = 'success'")
            successful_analyses = cursor.fetchone()[0]

            # Total insights
            cursor.execute("SELECT COUNT(*) FROM insights")
            total_insights = cursor.fetchone()[0]

            # Analyses in last 7 days
            seven_days_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM stock_analyses WHERE analysis_date >= ?",
                (seven_days_ago,)
            )
            recent_analyses = cursor.fetchone()[0]

            # Total deliveries
            cursor.execute("SELECT COUNT(*) FROM delivery_logs")
            total_deliveries = cursor.fetchone()[0]

            # Successful deliveries
            cursor.execute("SELECT COUNT(*) FROM delivery_logs WHERE delivery_status = 'success'")
            successful_deliveries = cursor.fetchone()[0]

            # Recent jobs (last 10)
            cursor.execute("""
                SELECT id, execution_time, job_status, stocks_scheduled, success_count,
                       failure_count, insights_delivered
                FROM analysis_jobs
                ORDER BY execution_time DESC
                LIMIT 10
            """)
            recent_jobs = cursor.fetchall()

            # Top analyzed stocks
            cursor.execute("""
                SELECT stock_symbol, COUNT(*) as count
                FROM stock_analyses
                WHERE analysis_status = 'success'
                GROUP BY stock_symbol
                ORDER BY count DESC
                LIMIT 5
            """)
            top_stocks = cursor.fetchall()

            conn.close()

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "subscriptions": {
                        "total": len(all_subscriptions),
                        "unique_users": unique_users,
                        "unique_stocks": unique_stocks,
                        "avg_per_user": round(avg_subs_per_user, 2),
                        "max_per_user": max_subs_per_user
                    },
                    "analyses": {
                        "total": total_analyses,
                        "successful": successful_analyses,
                        "success_rate": round(successful_analyses / total_analyses * 100, 2) if total_analyses > 0 else 0,
                        "recent_7_days": recent_analyses
                    },
                    "insights": {
                        "total": total_insights
                    },
                    "deliveries": {
                        "total": total_deliveries,
                        "successful": successful_deliveries,
                        "success_rate": round(successful_deliveries / total_deliveries * 100, 2) if total_deliveries > 0 else 0
                    },
                    "top_stocks": [{"symbol": s[0], "count": s[1]} for s in top_stocks],
                    "recent_jobs": [
                        {
                            "id": j[0],
                            "time": j[1],
                            "status": j[2],
                            "scheduled": j[3],
                            "success": j[4],
                            "failed": j[5],
                            "delivered": j[6]
                        }
                        for j in recent_jobs
                    ]
                }))
            else:
                print("=" * 80)
                print("STOCK ANALYZER - SYSTEM STATISTICS")
                print("=" * 80)
                print()

                print("📊 SUBSCRIPTIONS")
                print(f"  Total Active: {len(all_subscriptions)}")
                print(f"  Unique Users: {unique_users}")
                print(f"  Unique Stocks: {unique_stocks}")
                print(f"  Avg per User: {avg_subs_per_user:.1f}")
                print(f"  Max per User: {max_subs_per_user}")
                print()

                print("🔍 ANALYSES")
                print(f"  Total: {total_analyses}")
                print(f"  Successful: {successful_analyses}")
                if total_analyses > 0:
                    print(f"  Success Rate: {successful_analyses / total_analyses * 100:.1f}%")
                print(f"  Last 7 Days: {recent_analyses}")
                print()

                print("💡 INSIGHTS")
                print(f"  Total Generated: {total_insights}")
                print()

                print("📨 DELIVERIES")
                print(f"  Total: {total_deliveries}")
                print(f"  Successful: {successful_deliveries}")
                if total_deliveries > 0:
                    print(f"  Success Rate: {successful_deliveries / total_deliveries * 100:.1f}%")
                print()

                if top_stocks:
                    print("⭐ TOP ANALYZED STOCKS")
                    for symbol, count in top_stocks:
                        print(f"  {symbol}: {count} analyses")
                    print()

                if recent_jobs:
                    print("📅 RECENT JOBS (Last 10)")
                    for job in recent_jobs:
                        job_id, exec_time, status, scheduled, success, failed, delivered = job
                        status_icon = "✓" if status == "completed" else "✗" if status == "failed" else "⋯"
                        print(f"  {status_icon} [{exec_time}] {scheduled} scheduled, {success} success, {failed} failed, {delivered} delivered")
                    print()

                print("=" * 80)

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to fetch statistics - {e}", file=sys.stderr)
            return 1

    def deliver(
        self,
        symbol: Optional[str] = None,
        user_id: Optional[int] = None,
        dry_run: bool = False,
        json_output: bool = False
    ) -> int:
        """
        Manually trigger insight delivery.

        Args:
            symbol: Stock symbol to deliver (delivers to all subscribers)
            user_id: User ID to deliver to (delivers all their subscribed stocks)
            dry_run: Show what would be delivered without actually delivering
            json_output: Output as JSON

        Returns:
            Exit code (0=success, 1=error)
        """
        try:
            import asyncio
            from stock_analyzer.deliverer import InsightDeliverer

            if not self.config.telegram_token:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": "Telegram token not configured"
                    }))
                else:
                    print("Error: Telegram token not configured", file=sys.stderr)
                return 1

            # Determine what to deliver
            if symbol and user_id:
                if json_output:
                    print(json.dumps({
                        "status": "error",
                        "error_message": "Cannot specify both symbol and user_id"
                    }))
                else:
                    print("Error: Cannot specify both symbol and user_id", file=sys.stderr)
                return 1

            # Get insights to deliver
            insights_to_deliver = []

            if symbol:
                # Get latest insight for this symbol
                insights = self.storage.get_insights(symbol, limit=1)
                if not insights:
                    if json_output:
                        print(json.dumps({
                            "status": "error",
                            "error_message": f"No insights found for {symbol}"
                        }))
                    else:
                        print(f"Error: No insights found for {symbol}", file=sys.stderr)
                    return 1

                # Get all subscribers for this stock
                subscriptions = self.storage.get_subscriptions(stock_symbol=symbol, active_only=True)
                insight = insights[0]
                insights_to_deliver = [(sub.user_id, insight) for sub in subscriptions]

            elif user_id:
                # Get all subscriptions for this user
                subscriptions = self.storage.get_subscriptions(user_id=user_id, active_only=True)
                if not subscriptions:
                    if json_output:
                        print(json.dumps({
                            "status": "error",
                            "error_message": f"No active subscriptions for user {user_id}"
                        }))
                    else:
                        print(f"Error: No active subscriptions for user {user_id}", file=sys.stderr)
                    return 1

                # Get latest insight for each subscribed stock
                for sub in subscriptions:
                    insights = self.storage.get_insights(sub.stock_symbol, limit=1)
                    if insights:
                        insights_to_deliver.append((user_id, insights[0]))

            else:
                # Deliver all pending insights (all active subscriptions)
                subscriptions = self.storage.get_subscriptions(active_only=True)
                unique_stocks = set(sub.stock_symbol for sub in subscriptions)

                for stock_symbol in unique_stocks:
                    insights = self.storage.get_insights(stock_symbol, limit=1)
                    if insights:
                        insight = insights[0]
                        stock_subs = [s for s in subscriptions if s.stock_symbol == stock_symbol]
                        for sub in stock_subs:
                            insights_to_deliver.append((sub.user_id, insight))

            if not insights_to_deliver:
                if json_output:
                    print(json.dumps({
                        "status": "success",
                        "message": "No insights to deliver"
                    }))
                else:
                    print("No insights to deliver")
                return 0

            # Dry run - just show what would be delivered
            if dry_run:
                if json_output:
                    print(json.dumps({
                        "status": "success",
                        "dry_run": True,
                        "total_deliveries": len(insights_to_deliver),
                        "deliveries": [
                            {
                                "user_id": user_id,
                                "symbol": insight.stock_symbol,
                                "date": insight.analysis_date.isoformat()
                            }
                            for user_id, insight in insights_to_deliver
                        ]
                    }))
                else:
                    print(f"DRY RUN: Would deliver {len(insights_to_deliver)} insights")
                    for user_id, insight in insights_to_deliver:
                        print(f"  → User {user_id}: {insight.stock_symbol} ({insight.analysis_date})")
                return 0

            # Actually deliver
            deliverer = InsightDeliverer(
                storage=self.storage,
                telegram_token=self.config.telegram_token
            )

            async def deliver_all():
                """Deliver all insights to their respective users."""
                success_count = 0
                failure_count = 0

                for uid, insight in insights_to_deliver:
                    try:
                        result = await deliverer.deliver_insight(insight, uid, "telegram")
                        if result.status == "success":
                            success_count += 1
                        else:
                            failure_count += 1
                    except Exception as e:
                        logger.error(f"Failed to deliver to user {uid}: {e}")
                        failure_count += 1

                return success_count, failure_count

            success_count, failure_count = asyncio.run(deliver_all())

            if json_output:
                print(json.dumps({
                    "status": "success",
                    "total": len(insights_to_deliver),
                    "successful": success_count,
                    "failed": failure_count
                }))
            else:
                print(f"Delivery complete:")
                print(f"  Total: {len(insights_to_deliver)}")
                print(f"  Successful: {success_count}")
                print(f"  Failed: {failure_count}")

            return 0

        except Exception as e:
            if json_output:
                print(json.dumps({
                    "status": "error",
                    "error_message": str(e)
                }))
            else:
                print(f"Error: Failed to deliver - {e}", file=sys.stderr)
            return 1


def main():
    """
    Main entry point for stock-analyzer CLI.

    This is the function called when running `stock-analyzer` command.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="stock-analyzer",
        description="AI-powered stock analysis system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stock-analyzer init-db                    # Initialize database
  stock-analyzer analyze AAPL               # Analyze Apple stock
  stock-analyzer subscribe 123 AAPL         # Subscribe user 123 to AAPL
  stock-analyzer history AAPL --limit 10    # View AAPL history
  stock-analyzer stats                      # View system statistics
  stock-analyzer run-daily-job              # Run daily analysis job

For more information, see: https://github.com/AlphaAgent
        """
    )

    # Common arguments
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--db-path",
        help="Database path (overrides config)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-db command
    subparsers.add_parser("init-db", help="Initialize database")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a stock")
    analyze_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    analyze_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-analysis even if today's cached result exists",
    )

    # analyze-batch command
    batch_parser = subparsers.add_parser("analyze-batch", help="Analyze multiple stocks")
    batch_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    batch_parser.add_argument("--parallel", type=int, default=1, help="Parallel workers")

    # subscribe command
    subscribe_parser = subparsers.add_parser("subscribe", help="Subscribe user to stock")
    subscribe_parser.add_argument("user_id", type=int, help="User ID")
    subscribe_parser.add_argument("symbol", help="Stock symbol")

    # unsubscribe command
    unsubscribe_parser = subparsers.add_parser("unsubscribe", help="Unsubscribe user from stock")
    unsubscribe_parser.add_argument("user_id", type=int, help="User ID")
    unsubscribe_parser.add_argument("symbol", help="Stock symbol")

    # list-subscriptions command
    list_parser = subparsers.add_parser("list-subscriptions", help="List subscriptions")
    list_parser.add_argument("user_id", nargs="?", type=int, help="User ID (optional)")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate stock symbol")
    validate_parser.add_argument("symbol", help="Stock symbol")

    # history command
    history_parser = subparsers.add_parser("history", help="View historical insights")
    history_parser.add_argument("symbol", help="Stock symbol")
    history_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    history_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    history_parser.add_argument("--limit", type=int, default=30, help="Max results")
    history_parser.add_argument("--offset", type=int, default=0, help="Offset for pagination")

    # run-daily-job command
    job_parser = subparsers.add_parser("run-daily-job", help="Run daily analysis job")
    job_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # stats command
    subparsers.add_parser("stats", help="Show system statistics")

    # deliver command
    deliver_parser = subparsers.add_parser("deliver", help="Manually trigger delivery")
    deliver_parser.add_argument("--symbol", help="Stock symbol to deliver")
    deliver_parser.add_argument("--user-id", type=int, help="User ID to deliver to")
    deliver_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = CLI(db_path=args.db_path)

    # Route to appropriate command
    try:
        if args.command == "init-db":
            return cli.init_db(json_output=args.json)

        elif args.command == "analyze":
            import asyncio
            return asyncio.run(
                cli.analyze(args.symbol, force=args.force, json_output=args.json)
            )

        elif args.command == "analyze-batch":
            import asyncio
            return asyncio.run(cli.analyze_batch(
                args.symbols,
                parallel=args.parallel,
                json_output=args.json
            ))

        elif args.command == "subscribe":
            return cli.subscribe(args.user_id, args.symbol, json_output=args.json)

        elif args.command == "unsubscribe":
            return cli.unsubscribe(args.user_id, args.symbol, json_output=args.json)

        elif args.command == "list-subscriptions":
            return cli.list_subscriptions(user_id=args.user_id, json_output=args.json)

        elif args.command == "validate":
            import asyncio
            return asyncio.run(cli.validate(args.symbol, json_output=args.json))

        elif args.command == "history":
            from datetime import date as date_type
            start_date = date_type.fromisoformat(args.start) if args.start else None
            end_date = date_type.fromisoformat(args.end) if args.end else None
            return cli.history(
                args.symbol,
                start_date=start_date,
                end_date=end_date,
                limit=args.limit,
                offset=args.offset,
                json_output=args.json
            )

        elif args.command == "run-daily-job":
            import asyncio
            return asyncio.run(cli.run_daily_job(
                dry_run=args.dry_run,
                json_output=args.json
            ))

        elif args.command == "stats":
            return cli.stats(json_output=args.json)

        elif args.command == "deliver":
            return cli.deliver(
                symbol=args.symbol,
                user_id=args.user_id,
                dry_run=args.dry_run,
                json_output=args.json
            )

        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.json:
            print(json.dumps({"status": "error", "error_message": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
