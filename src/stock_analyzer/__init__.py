"""
AlphaAgent Stock Analyzer - AI-Powered Personal Stock Analysis System

A multi-provider LLM system for daily stock analysis and insight delivery.
"""

__version__ = "2.0.0"
__author__ = "AlphaAgent Team"

# Exceptions - always available
from stock_analyzer.exceptions import (
    AnalysisError,
    DataFetchError,
    DeliveryError,
    InvalidSymbolError,
    RateLimitError,
    StockAnalyzerError,
    StorageError,
)

# Models - always available
from stock_analyzer.models import (
    AnalysisJob,
    AnalysisResponse,
    DeliveryLog,
    Insight,
    StockAnalysis,
    StockData,
)

# Config - always available
from stock_analyzer.config import Config

# Core classes - import only if they exist
__all__ = [
    # Version
    "__version__",
    "__author__",
    # Config
    "Config",
    # Models
    "StockData",
    "StockAnalysis",
    "Insight",
    "DeliveryLog",
    "AnalysisJob",
    "AnalysisResponse",
    # Exceptions
    "StockAnalyzerError",
    "InvalidSymbolError",
    "DataFetchError",
    "AnalysisError",
    "DeliveryError",
    "StorageError",
    "RateLimitError",
]

# Import optional modules that may not exist yet
try:
    from stock_analyzer.storage import Storage

    __all__.append("Storage")
except ImportError:
    pass

try:
    from stock_analyzer.analyzer import Analyzer

    __all__.append("Analyzer")
except ImportError:
    pass

try:
    from stock_analyzer.fetcher import StockFetcher

    __all__.append("StockFetcher")
except ImportError:
    pass

try:
    from stock_analyzer.deliverer import InsightDeliverer

    __all__.append("InsightDeliverer")
except ImportError:
    pass

try:
    from stock_analyzer.llm_client import (
        ClaudeLLMClient,
        GeminiLLMClient,
        LLMClient,
        LLMClientFactory,
        OpenAILLMClient,
    )

    __all__.extend(
        [
            "LLMClient",
            "ClaudeLLMClient",
            "OpenAILLMClient",
            "GeminiLLMClient",
            "LLMClientFactory",
        ]
    )
except ImportError:
    pass
