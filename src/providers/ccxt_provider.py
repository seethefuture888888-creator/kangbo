"""
Optional ccxt provider: BTC 1h/1d OHLCV.
Pipeline runs without ccxt; if installed, can be used for higher-frequency BTC.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

try:
    import ccxt
except ImportError:
    ccxt = None


def fetch_btc_ohlcv(
    timeframe: str = "1d",
    limit: int = 400,
) -> list[dict[str, Any]]:
    """
    Fetch BTC OHLCV via ccxt (e.g. binance).
    Returns [ {"date": "YYYY-MM-DD", "open", "high", "low", "close", "volume"}, ... ].
    """
    if ccxt is None:
        return []
    try:
        exchange = ccxt.binance({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe=timeframe, limit=limit)
        out = []
        for candle in ohlcv:
            ts, o, h, l, c, v = candle[0], candle[1], candle[2], candle[3], candle[4], candle[5]
            dt = datetime.utcfromtimestamp(ts / 1000)
            out.append({
                "date": dt.strftime("%Y-%m-%d"),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": float(v),
            })
        return out
    except Exception:
        return []
