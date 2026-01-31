"""
yfinance provider: OHLCV daily for tickers.
Used for DXY proxy (DX-Y.NYB), BTC-USD, SMH, TSLA, 9988.HK, 0700.HK, GC=F, SI=F, HG=F.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

try:
    import yfinance as yf
except ImportError:
    yf = None

# Default ticker list for dashboard
DEFAULT_TICKERS = [
    "BTC-USD",
    "SMH",
    "TSLA",
    "9988.HK",
    "0700.HK",
    "GC=F",
    "SI=F",
    "HG=F",
    "DX-Y.NYB",  # US Dollar Index proxy
]


def fetch_ohlcv(
    tickers: list[str] | None = None,
    days: int = 400,
) -> dict[str, list[dict[str, Any]]]:
    """
    Fetch daily OHLCV for each ticker.
    Returns { ticker: [ {"date": "YYYY-MM-DD", "open", "high", "low", "close", "volume"}, ... ] }.
    """
    if yf is None:
        return {}
    tickers = tickers or DEFAULT_TICKERS
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    out = {}
    for t in tickers:
        try:
            obj = yf.Ticker(t)
            hist = obj.history(start=start, end=end, auto_adjust=True)
            if hist is None or hist.empty:
                out[t] = []
                continue
            hist = hist.reset_index()
            if "Date" in hist.columns:
                hist["date"] = hist["Date"].dt.strftime("%Y-%m-%d")
            elif "Datetime" in hist.columns:
                hist["date"] = hist["Datetime"].dt.strftime("%Y-%m-%d")
            else:
                out[t] = []
                continue
            rows = []
            for _, row in hist.iterrows():
                rows.append({
                    "date": row["date"],
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                })
            out[t] = rows
        except Exception:
            out[t] = []
    return out


def latest_price_and_returns(ticker: str, ohlcv: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """From OHLCV cache, get latest close, pct change 1d, 7d, 30d."""
    series = ohlcv.get(ticker) or []
    if not series:
        return {"price": None, "change1d": None, "change7d": None, "change30d": None}
    series = sorted(series, key=lambda x: x["date"])
    latest = series[-1]["close"]
    change1d = None
    change7d = None
    change30d = None
    for i, r in enumerate(reversed(series[:-1])):
        idx = len(series) - 2 - i
        if idx < 0:
            break
        prev = series[idx]["close"]
        if prev and prev != 0:
            days_ago = (datetime.strptime(series[-1]["date"], "%Y-%m-%d") -
                        datetime.strptime(r["date"], "%Y-%m-%d")).days
            pct = (latest - prev) / prev * 100
            if change1d is None and days_ago >= 1:
                change1d = round(pct, 2)
            if change7d is None and days_ago >= 5:
                change7d = round(pct, 2)
            if change30d is None and days_ago >= 25:
                change30d = round(pct, 2)
        if change1d is not None and change7d is not None and change30d is not None:
            break
    return {"price": latest, "change1d": change1d, "change7d": change7d, "change30d": change30d}
