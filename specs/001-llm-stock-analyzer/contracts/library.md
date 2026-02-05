# Library API Contract

**Feature**: AI-Powered Stock Analysis
**Date**: 2026-01-30
**Version**: 1.0.0

## Overview

The `stock_analyzer` Python library provides programmatic access to all stock analysis functionality. This contract defines the public API for use by the CLI, Telegram bot, tests, and any future integrations.

---

## Installation

```python
# Development install with uv
uv pip install -e .

# Import in code
from stock_analyzer import (
    Analyzer,
    StockFetcher,
    InsightDeliverer,
    Storage,
    models
)
```

---

## Core Classes

### 1. Analyzer

Main entry point for stock analysis operations.

```python
class Analyzer:
    """Stock analysis coordinator."""

    def __init__(
        self,
        llm_client: LLMClient,  # Supports Claude, OpenAI, or Gemini
        fetcher: StockFetcher,
        storage: Storage
    ):
        """
        Initialize analyzer with dependencies.

        Args:
            llm_client: LLM client (ClaudeLLMClient, OpenAILLMClient, or GeminiLLMClient)
            fetcher: Stock data fetcher
            storage: Storage manager
        """
        ...

    async def analyze_stock(
        self,
        symbol: str,
        date: Optional[datetime.date] = None,
        force: bool = False
    ) -> Insight:
        """
        Analyze a single stock.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            date: Analysis date (default: today)
            force: Force re-analysis even if exists

        Returns:
            Insight object with analysis results

        Raises:
            InvalidSymbolError: Symbol not found or invalid
            DataFetchError: Failed to fetch stock data
            AnalysisError: LLM analysis failed
            StorageError: Database operation failed
        """
        ...

    async def analyze_batch(
        self,
        symbols: List[str],
        parallel: int = 1,
        continue_on_error: bool = False
    ) -> BatchAnalysisResult:
        """
        Analyze multiple stocks.

        Args:
            symbols: List of stock ticker symbols
            parallel: Number of parallel tasks
            continue_on_error: Don't stop on first failure

        Returns:
            BatchAnalysisResult with success/failure counts
        """
        ...

    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol exists."""
        ...
```

**Usage Example**:
```python
async def main():
    analyzer = Analyzer(llm_client, fetcher, storage)

    # Analyze single stock
    insight = await analyzer.analyze_stock("AAPL")
    print(f"Summary: {insight.summary}")

    # Analyze batch
    result = await analyzer.analyze_batch(
        ["AAPL", "TSLA", "MSFT"],
        parallel=3
    )
    print(f"Success: {result.success_count}/{result.total}")
```

---

### 2. StockFetcher

Fetches stock market data from APIs.

```python
class StockFetcher:
    """Stock market data fetcher."""

    def __init__(
        self,
        primary_provider: str = "yfinance",
        backup_provider: Optional[str] = "alpha_vantage",
        api_key: Optional[str] = None
    ):
        """Initialize fetcher with providers."""
        ...

    async def fetch_stock_data(
        self,
        symbol: str,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None
    ) -> StockData:
        """
        Fetch stock data for analysis.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            StockData with OHLCV, fundamentals, metadata

        Raises:
            InvalidSymbolError: Symbol not found
            DataFetchError: API request failed
            RateLimitError: API rate limit exceeded
        """
        ...

    def validate_symbol(self, symbol: str) -> ValidationResult:
        """Validate stock symbol with API."""
        ...
```

**Usage Example**:
```python
fetcher = StockFetcher(primary_provider="yfinance")

# Fetch current data
data = await fetcher.fetch_stock_data("AAPL")
print(f"Price: ${data.current_price}")

# Fetch historical data
data = await fetcher.fetch_stock_data(
    "AAPL",
    start_date=date(2025, 1, 1),
    end_date=date.today()
)
```

---

### 3. InsightDeliverer

Delivers insights to users via various channels.

```python
class InsightDeliverer:
    """Insight delivery manager."""

    def __init__(self, storage: Storage):
        """Initialize deliverer with storage."""
        ...

    def register_channel(
        self,
        channel_name: str,
        channel: DeliveryChannel
    ):
        """Register a delivery channel (telegram, email, etc.)."""
        ...

    async def deliver_insight(
        self,
        insight: Insight,
        user_id: str,
        channel: str = "telegram"
    ) -> DeliveryResult:
        """
        Deliver insight to a user.

        Args:
            insight: Insight to deliver
            user_id: User identifier
            channel: Delivery channel name

        Returns:
            DeliveryResult with status and metadata

        Raises:
            DeliveryError: Delivery failed
            InvalidChannelError: Channel not registered
        """
        ...

    async def deliver_batch(
        self,
        insights: List[Insight],
        user_id: str
    ) -> List[DeliveryResult]:
        """Deliver multiple insights to a user."""
        ...
```

**Usage Example**:
```python
deliverer = InsightDeliverer(storage)
deliverer.register_channel("telegram", TelegramChannel(bot_token))

# Deliver single insight
result = await deliverer.deliver_insight(
    insight,
    user_id="123456789",
    channel="telegram"
)

# Deliver batch
results = await deliverer.deliver_batch(insights, user_id="123456789")
```

---

### 4. Storage

Database operations for persistence.

```python
class Storage:
    """SQLite storage manager."""

    def __init__(self, db_path: str):
        """Initialize storage with database path."""
        ...

    def init_database(self):
        """Create tables and indexes."""
        ...

    # Subscription operations
    def add_subscription(
        self,
        user_id: str,
        stock_symbol: str,
        preferences: Optional[Dict] = None
    ) -> Subscription:
        """Add a stock subscription."""
        ...

    def remove_subscription(self, user_id: str, stock_symbol: str):
        """Remove a stock subscription."""
        ...

    def get_subscriptions(
        self,
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for user or all users."""
        ...

    # Analysis operations
    def save_analysis(self, analysis: StockAnalysis):
        """Save stock analysis to database."""
        ...

    def get_analysis(
        self,
        stock_symbol: str,
        date: datetime.date
    ) -> Optional[StockAnalysis]:
        """Get analysis for stock and date."""
        ...

    # Insight operations
    def save_insight(self, insight: Insight):
        """Save insight to database."""
        ...

    def get_insights(
        self,
        stock_symbol: str,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        limit: int = 30
    ) -> List[Insight]:
        """Get historical insights."""
        ...

    # Job operations
    def create_job(self, stocks_scheduled: int) -> AnalysisJob:
        """Create a new analysis job."""
        ...

    def update_job(self, job_id: int, **updates):
        """Update job status and statistics."""
        ...
```

**Usage Example**:
```python
storage = Storage("./data/stock_analyzer.db")
storage.init_database()

# Add subscription
sub = storage.add_subscription("123456789", "AAPL")

# Save analysis
storage.save_analysis(analysis)
storage.save_insight(insight)

# Query history
insights = storage.get_insights(
    "AAPL",
    start_date=date(2025, 1, 1),
    limit=90
)
```

---

## Data Models

### Insight

```python
@dataclass
class Insight:
    """Stock analysis insight."""
    id: Optional[int]
    stock_symbol: str
    analysis_date: datetime.date
    summary: str
    trend_analysis: str
    risk_factors: List[str]
    opportunities: List[str]
    confidence_level: Literal["high", "medium", "low"]
    metadata: Dict[str, Any]
    created_at: datetime.datetime
```

### StockData

```python
@dataclass
class StockData:
    """Stock market data."""
    symbol: str
    current_price: float
    price_change_percent: float
    volume: int
    historical_prices: pd.DataFrame
    fundamentals: Dict[str, Any]
    metadata: Dict[str, Any]
```

### StockAnalysis

```python
@dataclass
class StockAnalysis:
    """Stock analysis record."""
    id: Optional[int]
    stock_symbol: str
    analysis_date: datetime.date
    price_snapshot: float
    price_change_percent: Optional[float]
    volume: Optional[int]
    analysis_status: Literal["success", "failed", "pending"]
    error_message: Optional[str]
    created_at: datetime.datetime
    duration_seconds: Optional[float]
```

---

## Exceptions

```python
class StockAnalyzerError(Exception):
    """Base exception for stock analyzer."""
    pass

class InvalidSymbolError(StockAnalyzerError):
    """Stock symbol is invalid or not found."""
    pass

class DataFetchError(StockAnalyzerError):
    """Failed to fetch stock data."""
    pass

class AnalysisError(StockAnalyzerError):
    """Analysis operation failed."""
    pass

class DeliveryError(StockAnalyzerError):
    """Delivery operation failed."""
    pass

class StorageError(StockAnalyzerError):
    """Database operation failed."""
    pass

class RateLimitError(StockAnalyzerError):
    """API rate limit exceeded."""
    pass

class SubscriptionLimitError(StockAnalyzerError):
    """Subscription limit reached."""
    pass
```

---

## Type Hints

All public APIs use comprehensive type hints:

```python
from typing import List, Optional, Dict, Any, Literal
from datetime import date, datetime
import pandas as pd

# Example
async def analyze_stock(
    symbol: str,
    date: Optional[date] = None,
    force: bool = False
) -> Insight:
    ...
```

---

## Async/Await Support

All I/O operations are async:

```python
# Async context manager
async with Analyzer(llm_client, fetcher, storage) as analyzer:
    insight = await analyzer.analyze_stock("AAPL")

# Manual lifecycle
analyzer = Analyzer(llm_client, fetcher, storage)
await analyzer.initialize()
try:
    insight = await analyzer.analyze_stock("AAPL")
finally:
    await analyzer.close()
```

---

## Testing Support

Mock classes for testing:

```python
from stock_analyzer.testing import (
    MockLLMClient,
    MockStockFetcher,
    MockStorage
)

# Unit test example
async def test_analyze_stock():
    fetcher = MockStockFetcher()
    fetcher.add_mock_data("AAPL", price=185.75)

    llm = MockLLMClient()
    llm.add_mock_response("AAPL", "Positive outlook...")

    storage = MockStorage()

    analyzer = Analyzer(llm, fetcher, storage)
    insight = await analyzer.analyze_stock("AAPL")

    assert insight.stock_symbol == "AAPL"
    assert insight.confidence_level == "high"
```

---

## LLM Provider Abstraction

### LLMClient (Abstract Base)

```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None
    ) -> AnalysisResponse:
        """Generate stock analysis."""
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
```

### ClaudeLLMClient (Anthropic)

```python
from anthropic import AsyncAnthropic

class ClaudeLLMClient(LLMClient):
    """Anthropic Claude LLM client."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        enable_caching: bool = True,
        max_tokens: int = 2048
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.enable_caching = enable_caching
        self.max_tokens = max_tokens

    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None
    ) -> AnalysisResponse:
        messages = [{"role": "user", "content": prompt}]

        system = []
        if system_prompt:
            system.append({
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"} if self.enable_caching else None
            })

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system if system else None,
            messages=messages
        )

        return AnalysisResponse(
            text=response.content[0].text,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=self.model
        )
```

### OpenAILLMClient

```python
from openai import AsyncOpenAI

class OpenAILLMClient(LLMClient):
    """OpenAI LLM client."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None
    ) -> AnalysisResponse:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return AnalysisResponse(
            text=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            model=self.model
        )
```

### GeminiLLMClient

```python
import google.generativeai as genai

class GeminiLLMClient(LLMClient):
    """Google Gemini LLM client."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro",
        temperature: float = 0.7,
        max_output_tokens: int = 2048
    ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    async def analyze(
        self,
        prompt: str,
        stock_data: StockData,
        system_prompt: Optional[str] = None
    ) -> AnalysisResponse:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = await self.model.generate_content_async(
            full_prompt,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens
            }
        )

        return AnalysisResponse(
            text=response.text,
            tokens_used=response.usage_metadata.total_token_count,
            model=self.model.model_name
        )
```

### LLMClientFactory

```python
class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create(
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMClient:
        """
        Create LLM client for specified provider.

        Args:
            provider: "anthropic", "openai", or "gemini"
            api_key: API key for the provider
            model: Model name (uses default if not specified)
            **kwargs: Provider-specific configuration

        Returns:
            LLMClient instance

        Raises:
            ValueError: Unknown provider
        """
        if provider == "anthropic":
            return ClaudeLLMClient(
                api_key=api_key,
                model=model or "claude-sonnet-4-5-20250929",
                **kwargs
            )
        elif provider == "openai":
            return OpenAILLMClient(
                api_key=api_key,
                model=model or "gpt-4o",
                **kwargs
            )
        elif provider == "gemini":
            return GeminiLLMClient(
                api_key=api_key,
                model=model or "gemini-2.5-pro",
                **kwargs
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

## Configuration

```python
from stock_analyzer import Config

# Load from file (with multi-provider support)
config = Config.from_file("~/.stock-analyzer/config.toml")

# Load from environment
config = Config.from_env()

# Programmatic configuration (Claude)
config = Config(
    llm_provider="anthropic",
    llm_model="claude-sonnet-4-5",
    llm_api_key=os.getenv("ANTHROPIC_API_KEY"),
    stock_data_provider="yfinance",
    db_path="./data/stock_analyzer.db",
    user_limit=10,
    system_limit=100
)

# Programmatic configuration (OpenAI)
config = Config(
    llm_provider="openai",
    llm_model="gpt-4o",
    llm_api_key=os.getenv("OPENAI_API_KEY"),
    stock_data_provider="yfinance",
    db_path="./data/stock_analyzer.db"
)

# Programmatic configuration (Gemini)
config = Config(
    llm_provider="gemini",
    llm_model="gemini-2.5-flash",
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    stock_data_provider="yfinance",
    db_path="./data/stock_analyzer.db"
)

# Use with components
analyzer = Analyzer.from_config(config)

# Or create LLM client directly
llm_client = LLMClientFactory.create(
    provider="anthropic",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-5",
    enable_caching=True
)
analyzer = Analyzer(llm_client, fetcher, storage)
```

### Configuration File (Multi-Provider)

`~/.stock-analyzer/config.toml`:

```toml
[api]
# Primary provider
llm_provider = "anthropic"  # or "openai" or "gemini"
llm_model = "claude-sonnet-4-5"
llm_api_key = "${ANTHROPIC_API_KEY}"

# Fallback provider (optional)
llm_fallback_provider = "openai"
llm_fallback_model = "gpt-4o-mini"
llm_fallback_api_key = "${OPENAI_API_KEY}"

# Provider-specific settings
[api.anthropic]
enable_prompt_caching = true
max_tokens = 2048

[api.openai]
temperature = 0.7
max_tokens = 2048

[api.gemini]
temperature = 0.7
max_output_tokens = 2048

[stock_data]
provider = "yfinance"
backup_provider = "alpha_vantage"
alpha_vantage_api_key = "${ALPHA_VANTAGE_API_KEY}"
```

---

## Version History

- **1.0.0** (2026-01-30): Initial library API
