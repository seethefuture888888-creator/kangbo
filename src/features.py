"""
Technical features: MA20/60/200, 12-week momentum, annualized vol, MDD(60/120), percentile(252d).
"""
from __future__ import annotations

import math
from typing import Any


def _closes(series: list[dict[str, Any]]) -> list[tuple[str, float]]:
    """(date, close) sorted by date ascending."""
    out = []
    for r in series:
        c = r.get("close")
        if c is not None:
            out.append((r["date"], float(c)))
    return sorted(out, key=lambda x: x[0])


def ma(series: list[dict[str, Any]], window: int) -> float | None:
    """Moving average of close over last `window` observations."""
    pts = _closes(series)
    if len(pts) < window:
        return None
    vals = [p[1] for p in pts[-window:]]
    return sum(vals) / len(vals)


def ma20(series: list[dict[str, Any]]) -> float | None:
    return ma(series, 20)


def ma60(series: list[dict[str, Any]]) -> float | None:
    return ma(series, 60)


def ma200(series: list[dict[str, Any]]) -> float | None:
    return ma(series, 200)


def mom12w(series: list[dict[str, Any]]) -> float | None:
    """12-week (≈84 trading days) momentum: (close_now / close_12w_ago - 1) * 100."""
    pts = _closes(series)
    n = min(84, len(pts) - 1)
    if n < 1 or len(pts) < n + 1:
        return None
    return (pts[-1][1] / pts[-(n + 1)][1] - 1) * 100


def vol_annualized(series: list[dict[str, Any]], window: int = 20) -> float | None:
    """Annualized volatility (std of daily returns * sqrt(252))."""
    pts = _closes(series)
    if len(pts) < window + 1:
        return None
    vals = [p[1] for p in pts[-(window + 1):]]
    rets = []
    for i in range(1, len(vals)):
        if vals[i - 1] and vals[i - 1] != 0:
            rets.append((vals[i] - vals[i - 1]) / vals[i - 1])
    if not rets:
        return None
    mean_r = sum(rets) / len(rets)
    var = sum((r - mean_r) ** 2 for r in rets) / len(rets)
    return math.sqrt(var * 252) * 100 if var >= 0 else None


def mdd(series: list[dict[str, Any]], window: int) -> float | None:
    """Max drawdown over last `window` days, in percent."""
    pts = _closes(series)
    if len(pts) < 2 or window < 2:
        return None
    pts = pts[-window:]
    peak = pts[0][1]
    m = 0.0
    for _, c in pts:
        if c > peak:
            peak = c
        if peak > 0:
            dd = (peak - c) / peak * 100
            if dd > m:
                m = dd
    return m


def mdd60(series: list[dict[str, Any]]) -> float | None:
    return mdd(series, 60)


def mdd120(series: list[dict[str, Any]]) -> float | None:
    return mdd(series, 120)


def percentile_252(series: list[dict[str, Any]], value: float, key: str = "close") -> float | None:
    """
    Percentile of `value` in the last 252 observations of `key`.
    Returns 0-100 (percent of observations <= value).
    """
    pts = _closes(series) if key == "close" else [(r["date"], r.get(key)) for r in series if r.get(key) is not None]
    pts = [(d, v) for d, v in pts if v is not None]
    pts = sorted(pts, key=lambda x: x[0])[-252:]
    if not pts:
        return None
    vals = sorted([p[1] for p in pts])
    n_below = sum(1 for v in vals if v <= value)
    return (n_below / len(vals)) * 100


def compute_all(
    series: list[dict[str, Any]],
    current_price: float | None = None,
) -> dict[str, Any]:
    """Compute MA20/60/200, mom12w, vol20, mdd60, mdd120, volPercentile1y, ddPercentile1y."""
    if current_price is None and series:
        pts = _closes(series)
        current_price = pts[-1][1] if pts else None
    out = {
        "ma20": ma20(series),
        "ma60": ma60(series),
        "ma200": ma200(series),
        "mom12w": mom12w(series),
        "vol20Ann": vol_annualized(series, 20),
        "mdd60": mdd60(series),
        "mdd120": mdd120(series),
    }
    if current_price is not None and series:
        out["volPercentile1y"] = percentile_252(series, current_price)
        out["ddPercentile1y"] = None  # could derive from drawdown series; keep simple
    else:
        out["volPercentile1y"] = 50.0
        out["ddPercentile1y"] = 50.0
    # Placeholder for correlations (need benchmark series)
    out["rsToBenchmark"] = 1.0
    out["correlationDXY"] = 0.0
    out["correlationRealRate"] = 0.0
    out["correlationSPX"] = 0.0
    return out
