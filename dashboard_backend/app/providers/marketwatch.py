"""
MarketWatch CSV fallback for HK stocks only (700, 9988).
URL: https://www.marketwatch.com/investing/stock/{symbol}/download-data?countrycode=hk
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timedelta
from typing import Any

import requests

# HK ticker -> MarketWatch symbol (no leading zero: 0700 -> 700)
MW_HK_SYMBOLS = {"0700.HK": "700", "9988.HK": "9988"}
BASE = "https://www.marketwatch.com/investing/stock/{symbol}/download-data?countrycode=hk"


def fetch_marketwatch_hk(ticker: str, days: int = 400) -> list[dict[str, Any]]:
    """Fetch HK stock history from MarketWatch CSV. Only 700, 9988 supported."""
    symbol = MW_HK_SYMBOLS.get(ticker)
    if not symbol:
        return []
    url = BASE.format(symbol=symbol)
    try:
        r = requests.get(url, headers={"User-Agent": "Dashboard/1.0"}, timeout=15)
        r.raise_for_status()
        text = r.text
        # May be HTML with embedded data or redirect; look for CSV-like content
        if "Date" in text and "," in text:
            # Find CSV block (often in a table or pre)
            lines = text.strip().splitlines()
            start = -1
            for i, line in enumerate(lines):
                if re.match(r"^Date[, ]", line, re.I) or line.startswith("date,"):
                    start = i
                    break
            if start >= 0:
                reader = csv.DictReader(lines[start:])
                out = []
                for row in reader:
                    date_val = row.get("Date") or row.get("date") or ""
                    close_val = row.get("Close") or row.get("close") or row.get(" Price") or ""
                    if not date_val or not close_val:
                        continue
                    try:
                        c = float(str(close_val).replace(",", ""))
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
                if out:
                    end = datetime.utcnow()
                    start_cut = end - timedelta(days=days)
                    out = [x for x in out if x["date"] >= start_cut.strftime("%Y-%m-%d")]
                    return sorted(out, key=lambda x: x["date"])
        return []
    except Exception:
        return []
