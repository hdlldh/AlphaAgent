"""Unit tests for analyzer markdown section parsing."""

from datetime import date
from unittest.mock import MagicMock

from stock_analyzer.analyzer import Analyzer
from stock_analyzer.models import Insight


def make_analyzer() -> Analyzer:
    """Create analyzer with mocked dependencies for pure parsing tests."""
    return Analyzer(
        llm_client=MagicMock(),
        fetcher=MagicMock(),
        storage=MagicMock()
    )


def test_extract_sections_supports_colon_outside_bold_and_no_truncation():
    analyzer = make_analyzer()
    long_summary = (
        "Costco Wholesale Corporation (COST) is currently trading at $1010.79, "
        "reflecting a 2.44% increase from the previous trading day. The stock is near "
        "its 52-week high of $1067.08, indicating continued bullish momentum and "
        "strong investor confidence in the business model."
    )
    text = f"""**Summary**:
{long_summary}

**Trend Analysis**:
Price action remains constructive with higher highs and steady volume support.

**Risk Factors**:
- Valuation has become stretched relative to long-term averages.

**Opportunities**:
- Membership fee growth may support margin expansion.
"""

    summary, trend = analyzer._extract_summary_and_trend(text)
    risks = analyzer._extract_bullet_section(text, "Risk Factors")
    opportunities = analyzer._extract_bullet_section(text, "Opportunities")

    assert summary == long_summary
    assert len(summary) > 200
    assert trend == "Price action remains constructive with higher highs and steady volume support."
    assert risks == ["Valuation has become stretched relative to long-term averages."]
    assert opportunities == ["Membership fee growth may support margin expansion."]


def test_extract_sections_supports_colon_inside_bold():
    analyzer = make_analyzer()
    text = """**Summary:**
Short summary.

**Trend Analysis:**
Neutral trend.
"""

    summary, trend = analyzer._extract_summary_and_trend(text)

    assert summary == "Short summary."
    assert trend == "Neutral trend."


def test_stale_cache_detection_for_legacy_summary_formats():
    analyzer = make_analyzer()

    header_style = Insight(
        stock_symbol="COST",
        analysis_date=date(2026, 2, 28),
        summary="**Summary**:\nSome text",
        trend_analysis="",
        risk_factors=[],
        opportunities=[],
        confidence_level="medium",
    )
    truncated_style = Insight(
        stock_symbol="COST",
        analysis_date=date(2026, 2, 28),
        summary="x" * 200,
        trend_analysis="",
        risk_factors=[],
        opportunities=[],
        confidence_level="medium",
    )
    healthy = Insight(
        stock_symbol="COST",
        analysis_date=date(2026, 2, 28),
        summary="Clear two-sentence summary with normal ending.",
        trend_analysis="",
        risk_factors=[],
        opportunities=[],
        confidence_level="medium",
    )

    assert analyzer._is_stale_cached_insight(header_style) is True
    assert analyzer._is_stale_cached_insight(truncated_style) is True
    assert analyzer._is_stale_cached_insight(healthy) is False
