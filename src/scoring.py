"""
RiskScore: weighted 0-100.
Credit 35%, Liquidity 30%, Growth 20%, Inflation 15%.
Implemented with available indicators (HY spread, real rate, PMI/proxy, Core CPI).
"""
from __future__ import annotations

from typing import Any

# Weights
W_CREDIT = 0.35
W_LIQUIDITY = 0.30
W_GROWTH = 0.20
W_INFLATION = 0.15


def _percentile_from_change_and_level(
    value: float | None,
    change7d: float | None,
    change1m: float | None,
    higher_is_risk: bool,
) -> float:
    """
    Heuristic 0-100 score: higher = more risk if higher_is_risk else lower = more risk.
    Uses level and changes; if no history, return 50.
    """
    if value is None:
        return 50.0
    # Simple: map value to 0-100 by rough bands; then nudge by changes
    # For HY spread: typical 3-8%, higher = risk. For real rate: 0-3%, higher = tight. etc.
    score = 50.0
    if higher_is_risk:
        # e.g. HY spread: 3->20, 5->50, 7->80
        if value < 3:
            score = 20
        elif value < 5:
            score = 20 + (value - 3) / 2 * 30
        elif value < 8:
            score = 50 + (value - 5) / 3 * 30
        else:
            score = min(95, 80 + (value - 8))
    else:
        # e.g. PMI: below 50 = risk, above 50 = growth
        if value < 48:
            score = 70
        elif value < 50:
            score = 55
        elif value < 53:
            score = 45
        else:
            score = 30
    if change7d is not None and higher_is_risk and change7d > 0:
        score = min(100, score + 5)
    if change1m is not None and higher_is_risk and change1m > 0:
        score = min(100, score + 5)
    return max(0, min(100, round(score, 1)))


def credit_score(hy_spread_value: float | None, change7d: float | None, change1m: float | None) -> float:
    """Higher spread = higher risk. 0-100."""
    return _percentile_from_change_and_level(hy_spread_value, change7d, change1m, higher_is_risk=True)


def liquidity_score(real_rate_value: float | None, change7d: float | None, change1m: float | None) -> float:
    """Higher real rate = tighter liquidity = higher risk. 0-100."""
    return _percentile_from_change_and_level(real_rate_value, change7d, change1m, higher_is_risk=True)


def growth_score(pmi_value: float | None, change7d: float | None, change1m: float | None) -> float:
    """Lower PMI = weaker growth = higher risk. So lower value = higher risk."""
    return _percentile_from_change_and_level(pmi_value, change7d, change1m, higher_is_risk=False)


def inflation_score(core_cpi_value: float | None, change7d: float | None, change1m: float | None) -> float:
    """Higher core CPI = inflation risk. 0-100."""
    return _percentile_from_change_and_level(core_cpi_value, change7d, change1m, higher_is_risk=True)


def risk_score(
    hy_spread: dict[str, Any],
    real_rate: dict[str, Any],
    dxy: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
) -> tuple[float, float, list[str]]:
    """
    Aggregate RiskScore 0-100. Returns (score, confidence, missing_macros).
    confidence: 1.0 if all present; 0.8/0.6/0.4 for 1/2/3 missing.
    """
    missing: list[str] = []
    if hy_spread.get("value") is None:
        missing.append("HY")
    if real_rate.get("value") is None:
        missing.append("REAL10Y")
    if dxy.get("price") is None and dxy.get("value") is None:
        missing.append("DXY")
    if pmi.get("value") is None:
        missing.append("PMI")
    if core_cpi.get("value") is None:
        missing.append("CORE_CPI")
    n = len(missing)
    confidence = 1.0 if n == 0 else (0.8 if n == 1 else (0.6 if n == 2 else 0.4))
    dxy_val = dxy.get("price") or dxy.get("value")
    c = credit_score(hy_spread.get("value"), hy_spread.get("change7d"), hy_spread.get("change1m"))
    lq_ry = liquidity_score(real_rate.get("value"), real_rate.get("change7d"), real_rate.get("change1m"))
    lq_dxy = _percentile_from_change_and_level(dxy_val, dxy.get("change7d"), dxy.get("change30d") or dxy.get("change1m"), higher_is_risk=True)
    lq = (lq_ry + lq_dxy) / 2
    g = growth_score(pmi.get("value"), pmi.get("change7d"), pmi.get("change1m"))
    inf = inflation_score(core_cpi.get("value"), core_cpi.get("change7d"), core_cpi.get("change1m"))
    total = W_CREDIT * c + W_LIQUIDITY * lq + W_GROWTH * g + W_INFLATION * inf
    score = max(0, min(100, round(total, 1)))
    return (score, confidence, missing)
