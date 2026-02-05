"""
Analyzer module for generating stock insights using LLM.

This module provides the Analyzer class which coordinates stock data fetching,
LLM-based analysis, and storage of insights.
"""

import asyncio
import re
import time
from dataclasses import dataclass
from datetime import date as date_type, timedelta
from typing import List, Optional

from stock_analyzer.exceptions import AnalysisError
from stock_analyzer.fetcher import StockFetcher
from stock_analyzer.llm_client import LLMClient
from stock_analyzer.logging import get_logger, log_analysis_start, log_analysis_complete
from stock_analyzer.models import Insight, StockAnalysis, StockData
from stock_analyzer.storage import Storage

logger = get_logger(__name__)


# Prompt templates for stock analysis
SYSTEM_PROMPT = """You are an expert financial analyst with deep knowledge of stock markets,
technical analysis, and fundamental analysis. Your role is to provide clear, actionable insights
based on stock data while being transparent about risks and opportunities.

Guidelines:
- Provide concise, data-driven analysis
- Clearly separate facts from interpretation
- Highlight both risks and opportunities
- Use bullet points for clarity
- Be honest about uncertainties"""


ANALYSIS_PROMPT_TEMPLATE = """Analyze the following stock data and provide investment insights:

**Stock Symbol**: {symbol}
**Current Price**: ${current_price:.2f}
**Price Change**: {price_change:+.2f}%
**Volume**: {volume}

**Recent Price History**:
{price_history}

**Fundamentals**:
{fundamentals}

Please provide:

1. **Summary**: A brief 2-3 sentence overview of the stock's current status

2. **Trend Analysis**: Analyze the price movement and volume patterns. What do they indicate?

3. **Risk Factors**: List 2-4 specific risks or concerns (use bullet points starting with "- ")

4. **Opportunities**: List 2-4 potential opportunities or positive catalysts (use bullet points starting with "- ")

Format your response with clear section headers using **bold** markdown.
"""


@dataclass
class BatchAnalysisResult:
    """Result of batch analysis operation."""
    total: int
    success_count: int
    failure_count: int
    duration_seconds: float
    results: List['IndividualResult']


@dataclass
class IndividualResult:
    """Result of a single stock analysis in batch."""
    stock_symbol: str
    status: str  # "success" or "error"
    error_message: Optional[str] = None


class Analyzer:
    """
    Coordinates stock analysis workflow.

    Uses StockFetcher to get data, LLMClient to generate insights,
    and Storage to persist results.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        fetcher: StockFetcher,
        storage: Storage
    ):
        """
        Initialize Analyzer.

        Args:
            llm_client: LLM client for generating analysis
            fetcher: Stock data fetcher
            storage: Storage for persisting results
        """
        self.llm_client = llm_client
        self.fetcher = fetcher
        self.storage = storage

    async def analyze_stock(
        self,
        symbol: str,
        date: Optional[date_type] = None,
        force: bool = False
    ) -> Insight:
        """
        Analyze a single stock and generate insights.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            date: Analysis date (defaults to today)
            force: If True, re-analyze even if exists for today

        Returns:
            Insight object with analysis results

        Raises:
            InvalidSymbolError: If symbol is invalid
            DataFetchError: If data fetching fails
            AnalysisError: If LLM analysis fails
        """
        analysis_date = date or date_type.today()
        start_time = time.time()

        log_analysis_start(logger, symbol)
        logger.debug(f"Analysis parameters: date={analysis_date} force={force}")

        # Check if analysis already exists (unless force=True)
        if not force:
            existing = self.storage.get_analysis(symbol, analysis_date)
            if existing and existing.analysis_status == "success":
                # Return existing insight
                logger.info(f"Returning cached analysis for {symbol} from {analysis_date}")
                insights = self.storage.get_insights(symbol, limit=1)
                if insights:
                    return insights[0]

        try:
            # Fetch stock data
            logger.debug(f"Fetching stock data for {symbol}")
            stock_data = await self.fetcher.fetch_stock_data(
                symbol,
                start_date=analysis_date - timedelta(days=30),
                end_date=analysis_date
            )

            # Generate analysis prompt
            prompt = self._build_prompt(stock_data)
            logger.debug(f"Generated prompt for {symbol}, length={len(prompt)}")

            # Get LLM analysis
            logger.debug(f"Requesting LLM analysis for {symbol}")
            response = await self.llm_client.analyze(
                prompt=prompt,
                stock_data=stock_data,
                system_prompt=SYSTEM_PROMPT
            )

            # Extract structured data from response
            logger.debug(f"Extracting structured data from LLM response for {symbol}")
            summary, trend_analysis = self._extract_summary_and_trend(response.text)
            risk_factors = self._extract_bullet_section(response.text, "Risk Factors")
            opportunities = self._extract_bullet_section(response.text, "Opportunities")
            confidence_level = self._determine_confidence(stock_data, response.text)
            logger.debug(f"Confidence level for {symbol}: {confidence_level}")

            # Calculate duration
            duration = time.time() - start_time

            # Save analysis record
            analysis = StockAnalysis(
                stock_symbol=symbol,
                analysis_date=analysis_date,
                analysis_status="success",
                price_snapshot=stock_data.current_price,
                volume=stock_data.volume,
                duration_seconds=duration,
                error_message=None
            )
            analysis_id = self.storage.save_analysis(analysis)

            # Create and save insight
            insight = Insight(
                analysis_id=analysis_id,
                stock_symbol=symbol,
                analysis_date=analysis_date,
                summary=summary,
                trend_analysis=trend_analysis,
                risk_factors=risk_factors,
                opportunities=opportunities,
                confidence_level=confidence_level,
                metadata={
                    "llm_model": response.model,
                    "tokens_used": response.tokens_used,
                    "duration_seconds": duration,
                    **response.metadata
                }
            )
            insight_id = self.storage.save_insight(insight)
            insight.id = insight_id

            log_analysis_complete(logger, symbol, duration, success=True)
            logger.info(f"Tokens used: {response.tokens_used}, Model: {response.model}")

            return insight

        except Exception as e:
            # Save failed analysis
            duration = time.time() - start_time
            log_analysis_complete(logger, symbol, duration, success=False)
            logger.error(f"Analysis failed for {symbol}: {type(e).__name__}: {e}")
            analysis = StockAnalysis(
                stock_symbol=symbol,
                analysis_date=analysis_date,
                analysis_status="failed",
                price_snapshot=0.0,
                volume=0,
                duration_seconds=duration,
                error_message=str(e)
            )
            self.storage.save_analysis(analysis)

            # Re-raise as AnalysisError if not already
            if isinstance(e, AnalysisError):
                raise
            raise AnalysisError(symbol, str(e), "unknown")

    async def analyze_batch(
        self,
        symbols: List[str],
        parallel: int = 1,
        continue_on_error: bool = False
    ) -> BatchAnalysisResult:
        """
        Analyze multiple stocks in batch.

        Args:
            symbols: List of stock symbols
            parallel: Number of parallel analyses (1 = sequential)
            continue_on_error: If True, continue on individual failures

        Returns:
            BatchAnalysisResult with summary and individual results
        """
        start_time = time.time()
        results = []

        logger.info(f"Starting batch analysis: {len(symbols)} symbols, parallel={parallel}")

        if parallel <= 1:
            # Sequential execution
            for symbol in symbols:
                try:
                    await self.analyze_stock(symbol)
                    results.append(IndividualResult(
                        stock_symbol=symbol,
                        status="success"
                    ))
                except Exception as e:
                    results.append(IndividualResult(
                        stock_symbol=symbol,
                        status="error",
                        error_message=str(e)
                    ))
                    if not continue_on_error:
                        break
        else:
            # Parallel execution with semaphore
            semaphore = asyncio.Semaphore(parallel)

            async def analyze_with_semaphore(symbol: str):
                """Analyze stock with semaphore for parallel execution limit."""
                async with semaphore:
                    try:
                        await self.analyze_stock(symbol)
                        return IndividualResult(
                            stock_symbol=symbol,
                            status="success"
                        )
                    except Exception as e:
                        return IndividualResult(
                            stock_symbol=symbol,
                            status="error",
                            error_message=str(e)
                        )

            # Run all analyses
            if continue_on_error:
                results = await asyncio.gather(
                    *[analyze_with_semaphore(s) for s in symbols],
                    return_exceptions=False
                )
            else:
                # Stop on first error
                for symbol in symbols:
                    result = await analyze_with_semaphore(symbol)
                    results.append(result)
                    if result.status == "error":
                        break

        duration = time.time() - start_time
        success_count = sum(1 for r in results if r.status == "success")
        failure_count = sum(1 for r in results if r.status == "error")

        logger.info(
            f"Batch analysis complete: {len(symbols)} total, "
            f"{success_count} success, {failure_count} failed, "
            f"duration={duration:.2f}s"
        )

        return BatchAnalysisResult(
            total=len(symbols),
            success_count=success_count,
            failure_count=failure_count,
            duration_seconds=duration,
            results=results
        )

    def _build_prompt(self, stock_data: StockData) -> str:
        """Build analysis prompt from stock data."""
        # Format price history
        if stock_data.historical_prices is not None and len(stock_data.historical_prices) > 0:
            recent_prices = stock_data.historical_prices.tail(5)
            price_history_lines = []
            for idx, row in recent_prices.iterrows():
                date_str = row.get('Date', idx)
                price_str = f"{row['Close']:.2f}"
                volume = row.get('Volume')
                if volume is not None and isinstance(volume, (int, float)):
                    volume_str = f"{int(volume):,}"
                    line = f"  {date_str}: ${price_str} (Volume: {volume_str})"
                else:
                    line = f"  {date_str}: ${price_str}"
                price_history_lines.append(line)
            price_history = "\n".join(price_history_lines)
        else:
            price_history = "  No historical data available"

        # Format fundamentals
        if stock_data.fundamentals:
            fundamentals = "\n".join([
                f"  {key}: {value}" for key, value in stock_data.fundamentals.items()
            ])
        else:
            fundamentals = "  No fundamental data available"

        # Format volume with commas if it's a number
        if isinstance(stock_data.volume, (int, float)):
            volume_str = f"{int(stock_data.volume):,}"
        else:
            volume_str = str(stock_data.volume) if stock_data.volume is not None else "N/A"

        return ANALYSIS_PROMPT_TEMPLATE.format(
            symbol=stock_data.symbol,
            current_price=stock_data.current_price,
            price_change=stock_data.price_change_percent,
            volume=volume_str,
            price_history=price_history,
            fundamentals=fundamentals
        )

    def _extract_summary_and_trend(self, text: str) -> tuple[str, str]:
        """Extract summary and trend analysis sections."""
        # Extract Summary - match text after "**Summary:**" header until next section
        summary_match = re.search(
            r'\*\*Summary:?\*\*[ \t]*\n(.+?)(?=\n[ \t]*\*\*|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        summary = summary_match.group(1).strip() if summary_match else text[:200]

        # Extract Trend Analysis - match text after "**Trend Analysis:**" header until next section
        trend_match = re.search(
            r'\*\*Trend Analysis:?\*\*[ \t]*\n(.+?)(?=\n[ \t]*\*\*|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        trend_analysis = trend_match.group(1).strip() if trend_match else ""

        return summary, trend_analysis

    def _extract_bullet_section(self, text: str, section_name: str) -> List[str]:
        """Extract bullet points from a section."""
        # Find section - match text after section header until next section or end
        pattern = rf'\*\*{section_name}:?\*\*[ \t]*\n(.+?)(?=\n[ \t]*\*\*|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if not match:
            return []

        section_text = match.group(1)

        # Extract bullet points (lines starting with -, *, or numbers)
        bullets = []
        for line in section_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Match bullets: "- text", "* text", "• text"
            bullet_match = re.match(r'^[-*•]\s*(.+)$', line)
            if bullet_match:
                bullets.append(bullet_match.group(1).strip())
            # Match numbered bullets: "1. text"
            elif re.match(r'^\d+\.\s*(.+)$', line):
                bullet_match = re.match(r'^\d+\.\s*(.+)$', line)
                bullets.append(bullet_match.group(1).strip())

        return bullets

    def _determine_confidence(self, stock_data: StockData, analysis_text: str) -> str:
        """
        Determine confidence level based on data quality and analysis.

        Returns "high", "medium", or "low"
        """
        # Start with medium confidence
        confidence_score = 5  # Scale of 0-10

        # Adjust based on data quality
        if stock_data.historical_prices is not None and len(stock_data.historical_prices) > 20:
            confidence_score += 2
        elif stock_data.historical_prices is None or len(stock_data.historical_prices) < 5:
            confidence_score -= 2

        if stock_data.fundamentals and len(stock_data.fundamentals) > 3:
            confidence_score += 1
        elif not stock_data.fundamentals:
            confidence_score -= 1

        # Adjust based on analysis content
        uncertainty_keywords = ['uncertain', 'unclear', 'limited data', 'insufficient']
        if any(keyword in analysis_text.lower() for keyword in uncertainty_keywords):
            confidence_score -= 1

        # Map score to level
        if confidence_score >= 7:
            return "high"
        elif confidence_score >= 4:
            return "medium"
        else:
            return "low"
