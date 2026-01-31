"""
Technical features: ma20/60/200, 12w momentum, vol20 ann, mdd60/120, percentile.
"""
from __future__ import annotations

import math
from typing import Any


def _closes(series: list[dict[str, Any]]) -> list[tuple[str, float]]:
    out = []
    for r in series:
        c = r.get("close")
        if c is not None:
            out.append((r["date"], float(c)))
    return sorted(out, key=lambda x: x[0])


def ma(series: list[dict[str, Any]], window: int) -> float | None:
    pts = _closes(series)
    if len(pts) < window:
        return None
    return sum(p[1] for p in pts[-window:]) / window


def _ma(series: list[dict[str, Any]], window: int) -> float | None:
    return ma(series, window)


def _mdd(series: list[dict[str, Any]], window: int) -> float | None:
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
            m = max(m, (peak - c) / peak * 100)
    return m


def _vol_ann(series: list[dict[str, Any]], window: int = 20) -> float | None:
    pts = _closes(series)
    if len(pts) < window + 1:
        return None
    vals = [p[1] for p in pts[-(window + 1):]]
    rets = [(vals[i] - vals[i - 1]) / vals[i - 1] for i in range(1, len(vals)) if vals[i - 1]]
    if not rets:
        return None
    mean_r = sum(rets) / len(rets)
    var = sum((r - mean_r) ** 2 for r in rets) / len(rets)
    return math.sqrt(var * 252) * 100 if var >= 0 else None


def _percentile_252(series: list[dict[str, Any]], value: float) -> float | None:
    pts = _closes(series)
    pts = pts[-252:]
    if not pts:
        return None
    vals = sorted([p[1] for p in pts])
    n_below = sum(1 for v in vals if v <= value)
    return (n_below / len(vals)) * 100


def compute_all(series: list[dict[str, Any]], current_price: float | None = None) -> dict[str, Any]:
    pts = _closes(series)
    if current_price is None and pts:
        current_price = pts[-1][1]
    out = {
        "ma20": ma(series, 20),
        "ma60": ma(series, 60),
        "ma200": ma(series, 200),
        "mom12w": None,
        "vol20Ann": _vol_ann(series, 20),
        "mdd60": _mdd(series, 60),
        "mdd120": _mdd(series, 120),
        "volPercentile1y": 50.0,
        "ddPercentile1y": 50.0,
        "rsToBenchmark": 1.0,
        "correlationDXY": 0.0,
        "correlationRealRate": 0.0,
        "correlationSPX": 0.0,
    }
    if len(pts) >= 84:
        mom = (pts[-1][1] / pts[-(84 + 1)][1] - 1) * 100
        out["mom12w"] = mom
    if current_price is not None and series:
        pct = _percentile_252(series, current_price)
        if pct is not None:
            out["volPercentile1y"] = pct
    return out
