"""
Regime: A/B/C/D. D can be early/late (spread peak + liquidity easing).
Rules based on credit, growth, inflation, liquidity only — no year guessing.
"""
from __future__ import annotations

from typing import Any

# Regime: A = expansion, B = late cycle, C = contraction, D = recovery (early D = spread peak + liquidity easing)


def regime(
    hy_spread: dict[str, Any],
    real_rate: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
    dxy_change1m: float | None = None,
) -> tuple[str, str]:
    """
    Return (regime_letter, regime_label).
    regime_letter: A | B | C | D (D_early | D_late in label).
    """
    hv = hy_spread.get("value")
    rv = real_rate.get("value")
    pv = pmi.get("value")
    cv = core_cpi.get("value")
    h_change1m = hy_spread.get("change1m")
    r_change1m = real_rate.get("change1m")

    # Credit: spread rising = stress; spread falling from peak = easing
    spread_rising = (h_change1m is not None and h_change1m > 0) or (hv is not None and hv > 5.5)
    spread_peak_falling = (h_change1m is not None and h_change1m < -0.3) and (hv is not None and hv > 5.0)
    # Liquidity: real rate high = tight; falling = easing
    liquidity_tight = rv is not None and rv > 1.5
    liquidity_easing = r_change1m is not None and r_change1m < -0.1
    # Growth
    growth_ok = pv is not None and pv >= 50
    growth_weak = pv is not None and pv < 48
    # Inflation
    infl_high = cv is not None and cv > 3.5

    # D: recovery — spread has peaked and started to fall, liquidity easing
    if spread_peak_falling and liquidity_easing:
        if dxy_change1m is not None and dxy_change1m < -0.5:
            return ("D", "D_early")
        return ("D", "D_late")
    # C: contraction — high spread, weak growth
    if spread_rising and growth_weak:
        return ("C", "C")
    # B: late cycle — growth ok but inflation high or liquidity tight
    if growth_ok and (infl_high or liquidity_tight):
        return ("B", "B")
    # A: expansion
    if growth_ok and not liquidity_tight:
        return ("A", "A")
    # Default by spread level
    if hv is not None and hv > 6:
        return ("C", "C")
    if hv is not None and hv > 5:
        return ("B", "B")
    return ("A", "A")
