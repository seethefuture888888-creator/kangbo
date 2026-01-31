"""
Stooq CSV. HK: 0700.HK -> 700.hk, 9988.HK -> 9988.hk (drop leading zero for 0700).
Commodities: xauusd, xagusd; copper proxy: cper.us
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from typing import Any
from urllib.request import Request, urlopen

BASE = "https://stooq.com/q/d/l/?s={ticker}&i=d&d1={d1}&d2={d2}"

# Stooq symbol mapping: our ticker -> stooq symbol
STOOQ_SYMBOLS = {
    "SMH": "smh.us",
    "TSLA": "tsla.us",
    "9988.HK": "9988.hk",
    "0700.HK": "700.hk",
    "GC=F": "xauusd",
    "SI=F": "xagusd",
    "HG=F": "cper.us",
    "GLD": "gld.us",
    "SLV": "slv.us",
    "CPER": "cper.us",
}


def _parse_stooq_csv(text: str) -> list[dict[str, Any]]:
    out = []
    lines = text.strip().splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines)
    for row in reader:
        date_val = row.get("Date") or row.get("date")
        if not date_val:
            continue
        close_val = row.get("Close") or row.get("close") or row.get("Price") or row.get("Adj Close")
        try:
            c = float(close_val or 0)
        except (TypeError, ValueError):
            continue
        if len(date_val) == 10 and date_val[4] == "-":
            date_str = date_val
        else:
            try:
                date_str = datetime.strptime(date_val[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                continue
        out.append({"date": date_str, "open": c, "high": c, "low": c, "close": c, "volume": 0})
    return sorted(out, key=lambda x: x["date"]) if out else []


def fetch_stooq(ticker: str, days: int = 400) -> list[dict[str, Any]]:
    symbol = STOOQ_SYMBOLS.get(ticker, ticker.lower().replace(".", "-") + ".us" if "." not in ticker else ticker.replace(".", "-") + ".hk")
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    d1, d2 = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    url = BASE.format(ticker=symbol, d1=d1, d2=d2)
    for ua in ["Dashboard/1.0", "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"]:
        try:
            req = Request(url, headers={"User-Agent": ua})
            with urlopen(req, timeout=20) as r:
                text = r.read().decode("utf-8", errors="ignore")
            out = _parse_stooq_csv(text)
            if out:
                return out
        except Exception:
            continue
    return []
