"""
FRED 宏观数据：HY, Real10Y, DXY, Core CPI YoY, PMI-like(AMTMNO).
"""
from __future__ import annotations

import math
import os
from datetime import datetime, timedelta
from typing import Any

import requests

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
SERIES = {
    "HY": "BAMLH0A0HYM2",
    "REAL10Y": "DFII10",
    "DXY": "DTWEXBGS",
    "CORE_CPI": "CPILFESL",
    "AMTMNO": "AMTMNO",
}


def _api_key() -> str | None:
    return os.environ.get("FRED_API_KEY")


def fetch_fred_series(
    series_id: str,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    key = _api_key()
    if not key:
        return []
    end = end or datetime.utcnow()
    start = start or (end - timedelta(days=365 * 3))
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "observation_start": start.strftime("%Y-%m-%d"),
        "observation_end": end.strftime("%Y-%m-%d"),
        "sort_order": "asc",
    }
    try:
        r = requests.get(FRED_BASE, params=params, timeout=30)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        out = []
        for o in obs:
            v = o.get("value")
            if v in (".", None, ""):
                continue
            try:
                out.append({"date": o["date"], "value": float(v)})
            except (TypeError, ValueError):
                continue
        return out
    except Exception:
        return []


def _latest_and_changes(obs: list[dict], freq_days: int = 1) -> dict[str, Any]:
    if not obs:
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    obs = sorted(obs, key=lambda x: x["date"])[-252:]
    latest = obs[-1]
    val = latest["value"]
    dt = datetime.strptime(latest["date"], "%Y-%m-%d")
    freshness = (datetime.utcnow() - dt.replace(tzinfo=None)).days
    change7d = change1m = None
    for o in reversed(obs[:-1]):
        d = datetime.strptime(o["date"], "%Y-%m-%d")
        days_ago = (dt - d).days
        if change7d is None and days_ago >= 5:
            change7d = val - o["value"] if o.get("value") is not None else None
        if change1m is None and days_ago >= 28:
            change1m = val - o["value"] if o.get("value") is not None else None
        if change7d is not None and change1m is not None:
            break
    return {"value": val, "change7d": change7d, "change1m": change1m, "freshness_days": freshness, "observations": obs}


def get_hy() -> dict[str, Any]:
    obs = fetch_fred_series(SERIES["HY"])
    return _latest_and_changes(obs)


def get_real10y() -> dict[str, Any]:
    obs = fetch_fred_series(SERIES["REAL10Y"])
    return _latest_and_changes(obs)


def get_dxy() -> dict[str, Any]:
    obs = fetch_fred_series(SERIES["DXY"])
    return _latest_and_changes(obs)


def get_core_cpi_yoy() -> dict[str, Any]:
    obs = fetch_fred_series(SERIES["CORE_CPI"])
    if not obs or len(obs) < 13:
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    obs = sorted(obs, key=lambda x: x["date"])
    vals = [o["value"] for o in obs]
    yoy = []
    for i in range(12, len(vals)):
        if vals[i - 12] and vals[i - 12] != 0:
            yoy.append((vals[i] / vals[i - 12] - 1) * 100)
        else:
            yoy.append(None)
    dates = [o["date"] for o in obs[12:]]
    if not yoy or all(v is None for v in yoy):
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    last_val = next(v for v in reversed(yoy) if v is not None)
    last_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
    freshness = (datetime.utcnow() - last_dt.replace(tzinfo=None)).days
    change1m = None
    for i in range(len(yoy) - 2, -1, -1):
        if yoy[i] is not None:
            change1m = last_val - yoy[i]
            break
    return {"value": round(last_val, 2), "change7d": None, "change1m": round(change1m, 4) if change1m is not None else None, "freshness_days": freshness}


FRED_AMTMNO_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=AMTMNO&cosd=1992-02-01"


def _fetch_amtmno_csv_fallback() -> list[dict[str, Any]]:
    """Fallback: FRED CSV direct link when API fails or returns empty."""
    try:
        r = requests.get(FRED_AMTMNO_CSV, timeout=30)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return []
        # Header: Date,AMTMNO
        out = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) < 2:
                continue
            date_s, val_s = parts[0].strip(), parts[1].strip()
            if val_s in (".", "", "None"):
                continue
            try:
                out.append({"date": date_s, "value": float(val_s)})
            except (TypeError, ValueError):
                continue
        return out
    except Exception:
        return []


def _zscore_clamp_adaptive(vals: list[float | None], min_window: int = 36, max_window: int = 120) -> list[float | None]:
    """zscore_window = min(max_window, len(valid)-1), max(min_window, zscore_window). pmi = 50+5*z, clamp [35,65]."""
    valid_count = sum(1 for v in vals if v is not None)
    zscore_window = min(max_window, max(0, valid_count - 1))
    zscore_window = max(min_window, zscore_window)
    out = []
    for i in range(len(vals)):
        if i < zscore_window - 1:
            out.append(None)
            continue
        w = vals[max(0, i - zscore_window + 1) : i + 1]
        w = [x for x in w if x is not None]
        if len(w) < min_window:
            out.append(None)
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / len(w)
        std = math.sqrt(var) if var > 0 else 1e-9
        v = vals[i]
        if v is None:
            out.append(None)
            continue
        z = (v - m) / std if std else 0
        pmi = 50 + 5 * z
        pmi = max(35, min(65, pmi))
        out.append(pmi)
    return out


def get_pmi_like() -> dict[str, Any]:
    """PMI-like from AMTMNO: API first, then CSV fallback. Adaptive window. Fallback value=50, freshness=999, reason PMI_FALLBACK."""
    obs = fetch_fred_series(SERIES["AMTMNO"])
    if not obs or len(obs) < 13:
        obs = _fetch_amtmno_csv_fallback()
    if not obs or len(obs) < 13:
        return {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}
    obs = sorted(obs, key=lambda x: x["date"])
    vals = [o["value"] for o in obs]
    orders_yoy: list[float | None] = []
    for i in range(12, len(vals)):
        if vals[i - 12] and vals[i - 12] != 0:
            orders_yoy.append((vals[i] / vals[i - 12] - 1) * 100)
        else:
            orders_yoy.append(None)
    valid = [x for x in orders_yoy if x is not None]
    if len(valid) < 37:
        return {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}
    pmi_like = _zscore_clamp_adaptive(orders_yoy, min_window=36, max_window=120)
    dates = [o["date"] for o in obs[12:]]
    last_val = pmi_like[-1] if pmi_like and pmi_like[-1] is not None else None
    if last_val is None:
        return {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}
    last_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
    freshness = (datetime.utcnow() - last_dt.replace(tzinfo=None)).days
    change1m = None
    for i in range(len(pmi_like) - 2, -1, -1):
        if pmi_like[i] is not None:
            change1m = last_val - pmi_like[i]
            break
    return {"value": round(last_val, 2), "change7d": None, "change1m": round(change1m, 4) if change1m is not None else None, "freshness_days": freshness}
