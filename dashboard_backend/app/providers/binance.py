"""
Binance public klines for BTC (no key). Base: data-api.binance.vision or api.binance.com.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests

BASE_URL = os.environ.get("BINANCE_BASE_URL", "https://data-api.binance.vision")
URL = f"{BASE_URL.rstrip('/')}/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400"


def fetch_btc_klines() -> list[dict[str, Any]]:
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        out = []
        for c in data:
            ts, o, h, l, close, v = c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
            dt = datetime.utcfromtimestamp(ts / 1000)
            out.append({"date": dt.strftime("%Y-%m-%d"), "open": o, "high": h, "low": l, "close": close, "volume": int(v)})
        return sorted(out, key=lambda x: x["date"])
    except Exception:
        try:
            fallback = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400"
            r = requests.get(fallback, timeout=15)
            r.raise_for_status()
            data = r.json()
            out = []
            for c in data:
                ts, o, h, l, close, v = c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
                dt = datetime.utcfromtimestamp(ts / 1000)
                out.append({"date": dt.strftime("%Y-%m-%d"), "open": o, "high": h, "low": l, "close": close, "volume": int(v)})
            return sorted(out, key=lambda x: x["date"])
        except Exception:
            return []
