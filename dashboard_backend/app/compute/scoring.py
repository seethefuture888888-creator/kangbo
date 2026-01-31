"""
RiskScore 0-100: Credit 35% + Liquidity 30% + Growth 20% + Inflation 15%.
Confidence 0-1: 缺 1 个宏观 -> 0.8, 缺 2 -> 0.6, 缺 3 -> 0.4.
"""
from __future__ import annotations

from typing import Any


def _pct(val: float | None, low: float, high: float, invert: bool = False) -> float:
    if val is None:
        return 50.0
    p = (val - low) / (high - low) * 100 if high != low else 50.0
    p = max(0, min(100, p))
    return 100 - p if invert else p


def risk_score(
    hy: dict[str, Any],
    real10y: dict[str, Any],
    dxy: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
) -> tuple[float, float, list[str]]:
    """
    Returns (score, confidence, missing_macros).
    confidence: 1.0 if all present; 0.8/0.6/0.4 for 1/2/3 missing; driver CONFIDENCE_LOW_DUE_TO_*.
    """
    missing: list[str] = []
    if hy.get("value") is None:
        missing.append("HY")
    if real10y.get("value") is None:
        missing.append("REAL10Y")
    if dxy.get("value") is None:
        missing.append("DXY")
    if pmi.get("value") is None:
        missing.append("PMI")
    if core_cpi.get("value") is None:
        missing.append("CORE_CPI")
    n = len(missing)
    confidence = 1.0 if n == 0 else (0.8 if n == 1 else (0.6 if n == 2 else 0.4))

    credit = _pct(hy.get("value"), 2, 8, invert=True)
    liquidity_ry = _pct(real10y.get("value"), 0, 3, invert=True)
    liquidity_dxy = _pct(dxy.get("value"), 90, 130, invert=True)
    liquidity = (liquidity_ry + liquidity_dxy) / 2
    growth = _pct(pmi.get("value"), 35, 65, invert=False) if pmi.get("value") is not None else 50.0
    inflation = _pct(core_cpi.get("value"), 1, 5, invert=True) if core_cpi.get("value") is not None else 50.0
    total = 0.35 * credit + 0.30 * liquidity + 0.20 * growth + 0.15 * inflation
    score = max(0, min(100, round(total, 1)))
    return (score, confidence, missing)
