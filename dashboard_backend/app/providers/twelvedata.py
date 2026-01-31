"""
Optional TwelveData fallback when Stooq fails. Requires TWELVEDATA_API_KEY.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import requests

BASE = "https://api.twelvedata.com/time_series"


def _api_key() -> str | None:
    return os.environ.get("TWELVEDATA_API_KEY")


def fetch_twelvedata(symbol: str, days: int = 400) -> list[dict[str, Any]]:
    key = _api_key()
    if not key:
        return []
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "symbol": symbol,
        "interval": "1day",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "apikey": key,
    }
    try:
        r = requests.get(BASE, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values") or []
        out = []
        for v in vals:
            dt = v.get("datetime", "")[:10]
            try:
                c = float(v.get("close", 0))
            except (TypeError, ValueError):
                continue
            out.append({"date": dt, "open": c, "high": c, "low": c, "close": c, "volume": 0})
        return sorted(out, key=lambda x: x["date"]) if out else []
    except Exception:
        return []
