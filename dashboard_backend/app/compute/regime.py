"""
Regime A/B/C/D (no year guessing).
A: credit tight + growth weak or RiskScore < 40
B: credit improving + liquidity not tight + growth improving
C: inflation up + liquidity tight + growth not weak
D: growth down + inflation down; early/late by spread peak + liquidity easing
"""
from __future__ import annotations

from typing import Any


def regime(
    hy: dict[str, Any],
    real10y: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
    dxy: dict[str, Any],
    risk_score_val: float,
) -> tuple[str, str]:
    hv = hy.get("value")
    hch = hy.get("change1m")
    rv = real10y.get("value")
    rch = real10y.get("change1m")
    pv = pmi.get("value")
    cv = core_cpi.get("value")
    dch = dxy.get("change1m")

    spread_peak_falling = hch is not None and hch < -0.2 and (hv or 0) > 5.0
    liquidity_easing = rch is not None and rch < -0.05
    growth_weak = pv is not None and pv < 48
    growth_ok = pv is not None and pv >= 50
    infl_high = cv is not None and cv > 3.0
    liquidity_tight = rv is not None and rv > 1.5

    if risk_score_val < 40:
        return ("A", "A")
    if spread_peak_falling and liquidity_easing:
        return ("D", "D_late")
    if growth_weak and (hv is not None and hv > 6):
        return ("C", "C")
    if growth_ok and (infl_high or liquidity_tight):
        return ("B", "B")
    if growth_ok:
        return ("A", "A")
    if hv is not None and hv > 6:
        return ("C", "C")
    if hv is not None and hv > 5:
        return ("B", "B")
    return ("A", "A")
