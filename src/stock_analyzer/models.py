"""
Data models for stock analyzer system.

All models use dataclasses for simplicity and type safety.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

import pandas as pd


@dataclass
class User:
    """
    Telegram user receiving stock analysis insights.

    Attributes:
        user_id: Telegram user ID (unique identifier)
        telegram_username: Telegram username for reference
        created_at: Timestamp when user first interacted
        last_active: Timestamp of last interaction
        preferences: User preferences as JSON blob
    """

    user_id: str
    telegram_username: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class Subscription:
    """
    User's subscription to receive analysis for a specific stock.

    Attributes:
        id: Unique subscription identifier
        user_id: References the subscribed user
        stock_symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
        subscription_date: Timestamp when subscription created
        active_status: 1 = active, 0 = inactive/unsubscribed
        preferences: Subscription-specific preferences as JSON blob
    """

    user_id: str
    stock_symbol: str
    id: Optional[int] = None
    subscription_date: datetime = field(default_factory=datetime.utcnow)
    active_status: int = 1
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class StockData:
    """
    Stock market data from APIs (yfinance, Alpha Vantage).

    Attributes:
        symbol: Stock ticker symbol
        current_price: Current stock price
        price_change_percent: Percentage change from previous day
        volume: Trading volume
        historical_prices: DataFrame with historical OHLCV data
        fundamentals: Fundamental data (P/E ratio, market cap, etc.)
        metadata: Additional metadata (source, timestamp, etc.)
    """

    symbol: str
    current_price: float
    price_change_percent: float
    volume: int
    historical_prices: pd.DataFrame
    fundamentals: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StockAnalysis:
    """
    Single analysis run for a specific stock on a specific date.

    Attributes:
        id: Unique analysis identifier
        stock_symbol: Stock ticker symbol analyzed
        analysis_date: Date of analysis (YYYY-MM-DD)
        price_snapshot: Stock price at time of analysis
        price_change_percent: Percentage change from previous day
        volume: Trading volume
        analysis_status: "success", "failed", or "pending"
        error_message: Error details if status = "failed"
        created_at: Timestamp when analysis completed
        duration_seconds: Time taken to complete analysis
    """

    stock_symbol: str
    analysis_date: date
    price_snapshot: float
    analysis_status: Literal["success", "failed", "pending"] = "pending"
    id: Optional[int] = None
    price_change_percent: Optional[float] = None
    volume: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None


@dataclass
class Insight:
    """
    AI-generated analysis content for a stock.

    Attributes:
        id: Unique insight identifier
        analysis_id: References the analysis run
        stock_symbol: Stock ticker symbol (denormalized for query performance)
        analysis_date: Date of analysis (denormalized)
        summary: Brief summary of the analysis (1-2 sentences)
        trend_analysis: LLM-generated trend interpretation
        risk_factors: Identified risks (list of strings)
        opportunities: Identified opportunities (list of strings)
        confidence_level: "high", "medium", or "low"
        metadata: Additional context (sources, prompt version, tokens used, etc.)
        created_at: Timestamp when insight generated
    """

    stock_symbol: str
    analysis_date: date
    summary: str
    trend_analysis: str
    risk_factors: List[str]
    opportunities: List[str]
    confidence_level: Literal["high", "medium", "low"]
    analysis_id: Optional[int] = None
    id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DeliveryLog:
    """
    Tracks delivery of insights to users via Telegram.

    Attributes:
        id: Unique delivery log identifier
        insight_id: References the delivered insight
        user_id: References the recipient user
        delivery_status: "success", "failed", or "pending"
        delivery_method: "telegram" (extensible for future methods)
        delivered_at: Timestamp when delivered (null if failed)
        error_message: Error details if status = "failed"
        telegram_message_id: Telegram message ID for reference
    """

    insight_id: int
    user_id: str
    delivery_status: Literal["success", "failed", "pending"] = "pending"
    delivery_method: str = "telegram"
    id: Optional[int] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    telegram_message_id: Optional[str] = None


@dataclass
class AnalysisJob:
    """
    Scheduled execution of the daily analysis workflow.

    Attributes:
        id: Unique job identifier
        execution_time: Timestamp when job started
        completion_time: Timestamp when job completed
        job_status: "running", "completed", or "failed"
        stocks_scheduled: Number of stocks planned to analyze
        stocks_processed: Number of stocks actually processed
        success_count: Number of successful analyses
        failure_count: Number of failed analyses
        insights_delivered: Number of insights successfully delivered
        errors: List of error messages
        duration_seconds: Total job duration
    """

    execution_time: datetime
    stocks_scheduled: int
    job_status: Literal["running", "completed", "failed"] = "running"
    id: Optional[int] = None
    completion_time: Optional[datetime] = None
    stocks_processed: int = 0
    success_count: int = 0
    failure_count: int = 0
    insights_delivered: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: Optional[float] = None


@dataclass
class AnalysisResponse:
    """
    Response from LLM API analysis call.

    Attributes:
        text: Generated analysis text
        tokens_used: Number of tokens consumed
        model: Model name used for analysis
        metadata: Additional response metadata
    """

    text: str
    tokens_used: int
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)
