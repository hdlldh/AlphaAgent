"""
Storage layer for stock analyzer using SQLite.

Provides database operations for users, subscriptions, analyses, insights, delivery logs, and jobs.
"""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from stock_analyzer.exceptions import StorageError, SubscriptionLimitError
from stock_analyzer.models import (
    AnalysisJob,
    DeliveryLog,
    Insight,
    StockAnalysis,
    Subscription,
    User,
)


class Storage:
    """
    SQLite storage manager for stock analyzer.

    Handles all database operations including initialization, user management,
    subscriptions, analyses, insights, delivery logs, and job tracking.
    """

    def __init__(self, db_path: str):
        """
        Initialize storage with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()

    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            sqlite3.Connection

        Raises:
            StorageError: If connection fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.Error as e:
            raise StorageError("database_connection", f"Failed to connect: {e}")

    def init_database(self):
        """
        Create all tables and indexes.

        Creates:
        - users table
        - subscriptions table
        - stock_analyses table
        - insights table
        - delivery_logs table
        - analysis_jobs table
        - All indexes for performance
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    telegram_username TEXT,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    preferences TEXT
                )
            """)

            # Subscriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    stock_symbol TEXT NOT NULL,
                    subscription_date TEXT NOT NULL,
                    active_status INTEGER NOT NULL DEFAULT 1,
                    preferences TEXT,
                    UNIQUE(user_id, stock_symbol),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_user
                ON subscriptions(user_id, active_status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_symbol
                ON subscriptions(stock_symbol, active_status)
            """)

            # Stock analyses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_symbol TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    price_snapshot REAL NOT NULL,
                    price_change_percent REAL,
                    volume INTEGER,
                    analysis_status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    duration_seconds REAL,
                    UNIQUE(stock_symbol, analysis_date)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_symbol_date
                ON stock_analyses(stock_symbol, analysis_date DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_date
                ON stock_analyses(analysis_date DESC)
            """)

            # Insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL,
                    stock_symbol TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    trend_analysis TEXT NOT NULL,
                    risk_factors TEXT NOT NULL,
                    opportunities TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES stock_analyses(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_insights_analysis
                ON insights(analysis_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_insights_symbol_date
                ON insights(stock_symbol, analysis_date DESC)
            """)

            # Delivery logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivery_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    delivery_method TEXT NOT NULL,
                    delivered_at TEXT,
                    error_message TEXT,
                    telegram_message_id TEXT,
                    FOREIGN KEY (insight_id) REFERENCES insights(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_user
                ON delivery_logs(user_id, delivery_status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_insight
                ON delivery_logs(insight_id)
            """)

            # Analysis jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_time TEXT NOT NULL,
                    completion_time TEXT,
                    job_status TEXT NOT NULL,
                    stocks_scheduled INTEGER NOT NULL,
                    stocks_processed INTEGER NOT NULL DEFAULT 0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    insights_delivered INTEGER NOT NULL DEFAULT 0,
                    errors TEXT,
                    duration_seconds REAL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_execution_time
                ON analysis_jobs(execution_time DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON analysis_jobs(job_status)
            """)

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("init_database", f"Failed to initialize database: {e}")
        finally:
            conn.close()

    # ==================== User Operations ====================

    def add_user(self, user: User):
        """
        Add a new user or update if exists.

        Args:
            user: User object to add
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            preferences_json = json.dumps(user.preferences) if user.preferences else None

            cursor.execute(
                """
                INSERT INTO users (user_id, telegram_username, created_at, last_active, preferences)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    telegram_username = excluded.telegram_username,
                    last_active = excluded.last_active,
                    preferences = excluded.preferences
            """,
                (
                    user.user_id,
                    user.telegram_username,
                    user.created_at.isoformat(),
                    user.last_active.isoformat(),
                    preferences_json,
                ),
            )
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("add_user", str(e))
        finally:
            conn.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: Telegram user ID

        Returns:
            User object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return User(
                user_id=row["user_id"],
                telegram_username=row["telegram_username"],
                created_at=datetime.fromisoformat(row["created_at"]),
                last_active=datetime.fromisoformat(row["last_active"]),
                preferences=json.loads(row["preferences"]) if row["preferences"] else None,
            )

        finally:
            conn.close()

    def update_user_last_active(self, user_id: str, last_active: datetime):
        """Update user's last active timestamp."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (last_active.isoformat(), user_id),
            )
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("update_user_last_active", str(e))
        finally:
            conn.close()

    # ==================== Subscription Operations ====================

    def add_subscription(self, subscription: Subscription) -> Subscription:
        """
        Add a new subscription.

        Args:
            subscription: Subscription object to add

        Returns:
            Subscription with populated ID

        Raises:
            SubscriptionLimitError: If user or system limits exceeded
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check user limit
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM subscriptions
                WHERE user_id = ? AND active_status = 1
            """,
                (subscription.user_id,),
            )
            user_count = cursor.fetchone()["count"]

            if user_count >= 10:
                raise SubscriptionLimitError("User", user_count, 10)

            # Check system limit
            cursor.execute(
                "SELECT COUNT(*) as count FROM subscriptions WHERE active_status = 1"
            )
            system_count = cursor.fetchone()["count"]

            if system_count >= 100:
                raise SubscriptionLimitError("System", system_count, 100)

            # Add subscription
            preferences_json = (
                json.dumps(subscription.preferences) if subscription.preferences else None
            )

            cursor.execute(
                """
                INSERT INTO subscriptions (user_id, stock_symbol, subscription_date, active_status, preferences)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    subscription.user_id,
                    subscription.stock_symbol,
                    subscription.subscription_date.isoformat(),
                    subscription.active_status,
                    preferences_json,
                ),
            )

            subscription.id = cursor.lastrowid
            conn.commit()

            return subscription

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("add_subscription", str(e))
        finally:
            conn.close()

    def remove_subscription(self, user_id: str, stock_symbol: str):
        """
        Remove subscription by setting active_status = 0.

        Args:
            user_id: Telegram user ID
            stock_symbol: Stock ticker symbol
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE subscriptions
                SET active_status = 0
                WHERE user_id = ? AND stock_symbol = ?
            """,
                (user_id, stock_symbol),
            )
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("remove_subscription", str(e))
        finally:
            conn.close()

    def get_subscriptions(
        self,
        user_id: Optional[str] = None,
        stock_symbol: Optional[str] = None,
        active_only: bool = True
    ) -> List[Subscription]:
        """
        Get subscriptions, optionally filtered by user, stock, and active status.

        Args:
            user_id: If provided, filter by user. If None, get all subscriptions.
            stock_symbol: If provided, filter by stock symbol.
            active_only: If True, only return active subscriptions

        Returns:
            List of Subscription objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM subscriptions WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if stock_symbol:
                query += " AND stock_symbol = ?"
                params.append(stock_symbol)

            if active_only:
                query += " AND active_status = 1"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            subscriptions = []
            for row in rows:
                subscriptions.append(
                    Subscription(
                        id=row["id"],
                        user_id=row["user_id"],
                        stock_symbol=row["stock_symbol"],
                        subscription_date=datetime.fromisoformat(row["subscription_date"]),
                        active_status=row["active_status"],
                        preferences=json.loads(row["preferences"])
                        if row["preferences"]
                        else None,
                    )
                )

            return subscriptions

        finally:
            conn.close()

    def get_subscription_count(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> int:
        """
        Get count of subscriptions.

        Args:
            user_id: If provided, count for specific user. If None, count all.
            active_only: If True, only count active subscriptions

        Returns:
            Number of subscriptions
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT COUNT(*) FROM subscriptions WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if active_only:
                query += " AND active_status = 1"

            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            return count

        finally:
            conn.close()

    # ==================== Analysis Operations ====================

    def save_analysis(self, analysis: StockAnalysis) -> int:
        """
        Save stock analysis, updating if exists.

        Args:
            analysis: StockAnalysis object to save

        Returns:
            Analysis ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO stock_analyses
                (stock_symbol, analysis_date, price_snapshot, price_change_percent, volume,
                 analysis_status, error_message, created_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(stock_symbol, analysis_date) DO UPDATE SET
                    price_snapshot = excluded.price_snapshot,
                    price_change_percent = excluded.price_change_percent,
                    volume = excluded.volume,
                    analysis_status = excluded.analysis_status,
                    error_message = excluded.error_message,
                    created_at = excluded.created_at,
                    duration_seconds = excluded.duration_seconds
            """,
                (
                    analysis.stock_symbol,
                    analysis.analysis_date.isoformat(),
                    analysis.price_snapshot,
                    analysis.price_change_percent,
                    analysis.volume,
                    analysis.analysis_status,
                    analysis.error_message,
                    analysis.created_at.isoformat(),
                    analysis.duration_seconds,
                ),
            )
            analysis_id = cursor.lastrowid

            # If it was an update, get the existing ID
            if analysis_id == 0:
                cursor.execute(
                    """
                    SELECT id FROM stock_analyses
                    WHERE stock_symbol = ? AND analysis_date = ?
                    """,
                    (analysis.stock_symbol, analysis.analysis_date.isoformat())
                )
                result = cursor.fetchone()
                analysis_id = result[0] if result else 0

            conn.commit()
            return analysis_id

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("save_analysis", str(e))
        finally:
            conn.close()

    def get_analysis(self, stock_symbol: str, analysis_date: date) -> Optional[StockAnalysis]:
        """
        Get analysis for specific stock and date.

        Args:
            stock_symbol: Stock ticker symbol
            analysis_date: Date of analysis

        Returns:
            StockAnalysis object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM stock_analyses
                WHERE stock_symbol = ? AND analysis_date = ?
            """,
                (stock_symbol, analysis_date.isoformat()),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return StockAnalysis(
                id=row["id"],
                stock_symbol=row["stock_symbol"],
                analysis_date=date.fromisoformat(row["analysis_date"]),
                price_snapshot=row["price_snapshot"],
                price_change_percent=row["price_change_percent"],
                volume=row["volume"],
                analysis_status=row["analysis_status"],
                error_message=row["error_message"],
                created_at=datetime.fromisoformat(row["created_at"]),
                duration_seconds=row["duration_seconds"],
            )

        finally:
            conn.close()

    # ==================== Insight Operations ====================

    def save_insight(self, insight: Insight) -> int:
        """
        Save insight to database.

        Args:
            insight: Insight object to save

        Returns:
            Insight ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            metadata_json = json.dumps(insight.metadata) if insight.metadata else None
            risk_factors_json = json.dumps(insight.risk_factors)
            opportunities_json = json.dumps(insight.opportunities)

            cursor.execute(
                """
                INSERT INTO insights
                (analysis_id, stock_symbol, analysis_date, summary, trend_analysis,
                 risk_factors, opportunities, confidence_level, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    insight.analysis_id,
                    insight.stock_symbol,
                    insight.analysis_date.isoformat(),
                    insight.summary,
                    insight.trend_analysis,
                    risk_factors_json,
                    opportunities_json,
                    insight.confidence_level,
                    metadata_json,
                    insight.created_at.isoformat(),
                ),
            )

            insight_id = cursor.lastrowid
            insight.id = insight_id
            conn.commit()
            return insight_id

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("save_insight", str(e))
        finally:
            conn.close()

    def get_insights(
        self,
        stock_symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 30,
        offset: int = 0,
    ) -> List[Insight]:
        """
        Get historical insights for a stock with optional date filtering and pagination.

        Args:
            stock_symbol: Stock ticker symbol
            start_date: Start date filter (inclusive)
            end_date: End date filter (inclusive)
            limit: Maximum number of insights to return
            offset: Number of insights to skip (for pagination)

        Returns:
            List of Insight objects, ordered by date descending
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM insights WHERE stock_symbol = ?"
            params = [stock_symbol]

            if start_date:
                query += " AND analysis_date >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND analysis_date <= ?"
                params.append(end_date.isoformat())

            query += " ORDER BY analysis_date DESC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            insights = []
            for row in rows:
                insights.append(
                    Insight(
                        id=row["id"],
                        analysis_id=row["analysis_id"],
                        stock_symbol=row["stock_symbol"],
                        analysis_date=date.fromisoformat(row["analysis_date"]),
                        summary=row["summary"],
                        trend_analysis=row["trend_analysis"],
                        risk_factors=json.loads(row["risk_factors"]),
                        opportunities=json.loads(row["opportunities"]),
                        confidence_level=row["confidence_level"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )

            return insights

        finally:
            conn.close()

    # ==================== Job Operations ====================

    def create_job(self, stocks_scheduled: int) -> AnalysisJob:
        """
        Create a new analysis job.

        Args:
            stocks_scheduled: Number of stocks planned to analyze

        Returns:
            AnalysisJob with populated ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            execution_time = datetime.utcnow()

            cursor.execute(
                """
                INSERT INTO analysis_jobs
                (execution_time, job_status, stocks_scheduled)
                VALUES (?, ?, ?)
            """,
                (execution_time.isoformat(), "running", stocks_scheduled),
            )

            job_id = cursor.lastrowid
            conn.commit()

            return AnalysisJob(
                id=job_id,
                execution_time=execution_time,
                job_status="running",
                stocks_scheduled=stocks_scheduled,
            )

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("create_job", str(e))
        finally:
            conn.close()

    def update_job(self, job_id: int, **updates):
        """
        Update job with progress and status.

        Args:
            job_id: Job ID to update
            **updates: Fields to update (stocks_processed, success_count, failure_count, etc.)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Build update query from provided fields
            set_clauses = []
            params = []

            for key, value in updates.items():
                if key in [
                    "completion_time",
                    "job_status",
                    "stocks_processed",
                    "success_count",
                    "failure_count",
                    "insights_delivered",
                    "errors",
                    "duration_seconds",
                ]:
                    set_clauses.append(f"{key} = ?")

                    if key == "completion_time" and isinstance(value, datetime):
                        params.append(value.isoformat())
                    elif key == "errors" and isinstance(value, list):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)

            if set_clauses:
                query = f"UPDATE analysis_jobs SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(job_id)

                cursor.execute(query, params)
                conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("update_job", str(e))
        finally:
            conn.close()

    def save_delivery_log(self, log: DeliveryLog) -> int:
        """
        Save delivery log to database.

        Args:
            log: DeliveryLog to save

        Returns:
            Log ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO delivery_logs
                (insight_id, user_id, delivery_method, delivery_status, error_message, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    log.insight_id,
                    log.user_id,
                    log.delivery_method,
                    log.delivery_status,
                    log.error_message,
                    log.delivered_at.isoformat() if log.delivered_at else None,
                ),
            )

            log_id = cursor.lastrowid
            conn.commit()
            return log_id

        except sqlite3.Error as e:
            conn.rollback()
            raise StorageError("save_delivery_log", str(e))
        finally:
            conn.close()
