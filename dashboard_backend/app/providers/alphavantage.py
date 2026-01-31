"""
Optional Alpha Vantage fallback (free tier ~25 req/day). Requires ALPHAVANTAGE_API_KEY.
TIME_SERIES_DAILY for stocks/ETF; use only when other providers fail to save quota.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import requests

BASE = "https://www.alphavantage.co/query"

# Our ticker -> Alpha Vantage symbol (stocks/ETF)
AV_SYMBOLS = {
    "TSLA": "TSLA",
    "SMH": "SMH",
    "0700.HK": "0700.HK",
    "9988.HK": "9988.HK",
    "GLD": "GLD",
    "SLV": "SLV",
    "CPER": "CPER",
}


def _api_key() -> str | None:
    return os.environ.get("ALPHAVANTAGE_API_KEY")


def fetch_alphavantage(symbol: str, days: int = 400) -> list[dict[str, Any]]:
    key = _api_key()
    if not key:
        return []
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": key,
        "outputsize": "full" if days > 100 else "compact",
    }
    try:
        r = requests.get(BASE, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        series = data.get("Time Series (Daily)") or data.get("time_series_daily")
        if not series:
            return []
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        out = []
        for date_str, v in series.items():
            if date_str < cutoff:
                continue
            try:
                c = float(v.get("4. close") or v.get("close", 0))
            except (TypeError, ValueError):
                continue
            out.append({"date": date_str, "open": c, "high": c, "low": c, "close": c, "volume": 0})
        return sorted(out, key=lambda x: x["date"])[-days:] if out else []
    except Exception:
        return []
