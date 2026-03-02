"""
Storage layer for stock analyzer using SQLite (personal use).

Provides database operations for analyses, insights, delivery logs, and jobs.
"""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from stock_analyzer.exceptions import StorageError
from stock_analyzer.models import (
    AnalysisJob,
    DeliveryLog,
    Insight,
    StockAnalysis,
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
        Create or migrate database schema for personal use.

        Migration from multi-user to personal:
        1. Drop users and subscriptions tables (no longer needed)
        2. Create simplified schema without user FKs
        3. Preserve existing insights and analyses

        Creates:
        - stock_analyses table
        - insights table (simplified, no analysis_id FK)
        - delivery_logs table (channel_id instead of user_id)
        - analysis_jobs table
        - All indexes for performance
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # MIGRATION STEP 1: Drop multi-user tables
            cursor.execute("DROP TABLE IF EXISTS subscriptions")
            cursor.execute("DROP TABLE IF EXISTS users")

            # MIGRATION STEP 2: Create simplified tables

            # Stock analyses table (unchanged)
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

            # Insights table (MODIFIED: removed analysis_id FK)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_symbol TEXT NOT NULL,
                    analysis_date TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    trend_analysis TEXT NOT NULL,
                    risk_factors TEXT NOT NULL,
                    opportunities TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_insights_symbol_date
                ON insights(stock_symbol, analysis_date DESC)
            """)

            # Delivery logs table (MODIFIED: channel_id instead of user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivery_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_id INTEGER NOT NULL,
                    channel_id TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    delivery_method TEXT NOT NULL,
                    delivered_at TEXT,
                    error_message TEXT,
                    telegram_message_id TEXT,
                    FOREIGN KEY (insight_id) REFERENCES insights(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_insight
                ON delivery_logs(insight_id)
            """)

            # Analysis jobs table (unchanged)
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
        Save insight to database (personal use - no analysis_id FK).

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
                (stock_symbol, analysis_date, summary, trend_analysis,
                 risk_factors, opportunities, confidence_level, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
        Save delivery log to database (personal use - channel_id instead of user_id).

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
                (insight_id, channel_id, delivery_method, delivery_status, error_message, delivered_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    log.insight_id,
                    log.channel_id,
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
