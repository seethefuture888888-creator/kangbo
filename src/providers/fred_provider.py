"""
FRED data provider. Requires FRED_API_KEY in environment.
Uses /fred/series/observations to fetch series data.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import requests

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# Default series IDs (configurable)
FRED_SERIES = {
    "HY_OAS": "BAMLH0A0HYM2",   # ICE BofA US High Yield Index OAS
    "REAL10Y": "DFII10",         # 10-Year TIPS (real rate proxy)
    "CORE_CPI": "CPILFESL",      # Core CPI (All Items Less Food & Energy)
    "AMTMNO": "AMTMNO",          # Manufacturers' New Orders: Total Manufacturing (PMI proxy)
    "DXY": "DTWEXBGS",           # Nominal Broad U.S. Dollar Index
}


def fetch_fred_series(
    series_id: str,
    api_key: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch observations for a FRED series.
    Returns list of {"date": "YYYY-MM-DD", "value": float}.
    """
    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        return []
    end = end or datetime.utcnow()
    start = start or (end - timedelta(days=365 * 2))
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
        data = r.json()
        obs = data.get("observations", [])
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


def get_latest_and_changes(series_id: str) -> dict[str, Any]:
    """
    Return latest value, change vs 7d ago, change vs ~30d ago, and freshness_days.
    """
    obs = fetch_fred_series(series_id)
    if not obs:
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    obs = obs[-252:]  # last year of data
    latest = obs[-1]
    val = latest["value"]
    date_latest = datetime.strptime(latest["date"], "%Y-%m-%d")
    freshness_days = (datetime.utcnow() - date_latest.replace(tzinfo=None)).days

    change7d = None
    change1m = None
    for i, o in enumerate(reversed(obs[:-1])):
        d = datetime.strptime(o["date"], "%Y-%m-%d")
        days_ago = (date_latest - d).days
        if change7d is None and days_ago >= 5:
            change7d = val - o["value"] if o["value"] else None
        if change1m is None and days_ago >= 28:
            change1m = val - o["value"] if o["value"] else None
        if change7d is not None and change1m is not None:
            break

    return {
        "value": val,
        "change7d": change7d,
        "change1m": change1m,
        "freshness_days": freshness_days if freshness_days is not None else 999,
        "observations": obs,
    }


def get_core_cpi_yoy(api_key: str | None = None) -> dict[str, Any]:
    """Core CPI as YoY %%: (CPILFESL / CPILFESL.shift(12) - 1) * 100. Freshness = (today - last_obs_date).days; no data 999."""
    obs = fetch_fred_series("CPILFESL", api_key=api_key)
    if not obs or len(obs) < 13:
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    obs = sorted(obs, key=lambda x: x["date"])
    vals = [o["value"] for o in obs]
    dates = [o["date"] for o in obs]
    yoy = []
    for i in range(12, len(vals)):
        if vals[i - 12] and vals[i - 12] != 0:
            yoy.append((vals[i] / vals[i - 12] - 1) * 100)
        else:
            yoy.append(None)
    yoy_dates = dates[12:]
    if not yoy_dates or all(v is None for v in yoy):
        return {"value": None, "change7d": None, "change1m": None, "freshness_days": 999}
    last_val = next(v for v in reversed(yoy) if v is not None)
    last_dt = datetime.strptime(yoy_dates[-1], "%Y-%m-%d")
    freshness_days = (datetime.utcnow() - last_dt.replace(tzinfo=None)).days
    change1m = None
    for i in range(len(yoy) - 2, -1, -1):
        if yoy[i] is not None and last_val is not None:
            change1m = last_val - yoy[i]
            break
    return {"value": round(last_val, 2), "change7d": None, "change1m": round(change1m, 4) if change1m is not None else None, "freshness_days": freshness_days}


FRED_AMTMNO_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=AMTMNO&cosd=1992-02-01"


def _fetch_amtmno_csv_fallback() -> list[dict[str, Any]]:
    """Fallback: FRED CSV direct link when API fails or returns empty."""
    try:
        r = requests.get(FRED_AMTMNO_CSV, timeout=30)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        if len(lines) < 2:
            return []
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


def _pmi_zscore_adaptive(orders_yoy: list[float | None], min_window: int = 36, max_window: int = 120) -> list[float | None]:
    """zscore_window = min(120, len(valid)-1), max(36, zscore_window). pmi_like = 50+5*zscore, clamp [35,65]."""
    import math
    valid_count = sum(1 for x in orders_yoy if x is not None)
    zscore_window = min(max_window, max(0, valid_count - 1))
    zscore_window = max(min_window, zscore_window)
    out = []
    for i in range(len(orders_yoy)):
        if i < zscore_window - 1:
            out.append(None)
            continue
        w = [x for x in orders_yoy[max(0, i - zscore_window + 1) : i + 1] if x is not None]
        if len(w) < min_window:
            out.append(None)
            continue
        v = orders_yoy[i]
        if v is None:
            out.append(None)
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / len(w)
        std = math.sqrt(var) if var > 0 else 1e-9
        z = (v - m) / std if std else 0
        pmi = 50 + 5 * z
        pmi = max(35, min(65, pmi))
        out.append(pmi)
    return out


def get_pmi_from_amtmno(api_key: str | None = None) -> dict[str, Any]:
    """PMI-like from AMTMNO: API first, then FRED CSV fallback. orders_yoy = (s/s.shift(12)-1)*100; adaptive zscore; clamp [35,65]. If still no data: value=50, freshness=999, reason PMI_FALLBACK."""
    obs = fetch_fred_series("AMTMNO", api_key=api_key)
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
    valid_count = sum(1 for x in orders_yoy if x is not None)
    if valid_count < 37:
        return {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}
    pmi_like = _pmi_zscore_adaptive(orders_yoy, min_window=36, max_window=120)
    dates = [o["date"] for o in obs[12:]]
    last_val = pmi_like[-1] if pmi_like and pmi_like[-1] is not None else None
    if last_val is None:
        return {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}
    last_dt = datetime.strptime(dates[-1], "%Y-%m-%d")
    freshness_days = (datetime.utcnow() - last_dt.replace(tzinfo=None)).days
    change1m = None
    for i in range(len(pmi_like) - 2, -1, -1):
        if pmi_like[i] is not None:
            change1m = last_val - pmi_like[i]
            break
    return {"value": round(last_val, 2), "change7d": None, "change1m": round(change1m, 4) if change1m is not None else None, "freshness_days": freshness_days}


def get_dxy_from_fred(api_key: str | None = None) -> dict[str, Any]:
    """DXY from FRED DTWEXBGS. Freshness = (today - last_obs_date).days; no data 999."""
    out = get_latest_and_changes(FRED_SERIES["DXY"])
    if out.get("value") is None and out.get("freshness_days") is None:
        out["freshness_days"] = 999
    return out
