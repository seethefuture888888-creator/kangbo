"""
Provider chain per ticker: yfinance -> stooq -> marketwatch (HK) -> TwelveData -> Binance (BTC).
Returns ohlcv map and dataStatus: provider_used, last_date, row_count, error_reason; never output 0 for price.
"""
from __future__ import annotations

import csv
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.request import Request, urlopen

import requests

from .yfinance_provider import fetch_ohlcv
from .alphavantage_provider import fetch_alphavantage as _fetch_alphavantage
from .alphavantage_provider import AV_SYMBOLS as AV_SYMBOLS_MAP

# Ticker -> proxy symbol when we use proxy (GC=F->xauusd, SI=F->xagusd, HG=F->cper.us)
PROXY_FOR: dict[str, str] = {"GC=F": "xauusd", "SI=F": "xagusd", "HG=F": "cper.us"}
# Commodity ETF fallback when futures/spot all fail: GC=F->GLD, SI=F->SLV, HG=F->CPER
COMMODITY_ETF_FALLBACK: dict[str, str] = {"GC=F": "GLD", "SI=F": "SLV", "HG=F": "CPER"}

# Stooq symbol mapping: our ticker -> stooq symbol (TSLA->tsla.us, 0700.HK->700.hk, GC=F->xauusd, etc.)
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

STOOQ_BASE = "https://stooq.com/q/d/l/?s={symbol}&i=d&d1={d1}&d2={d2}"

BINANCE_BASE = os.environ.get("BINANCE_BASE_URL", "https://data-api.binance.vision")
BINANCE_KLINES = f"{BINANCE_BASE.rstrip('/')}/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400"
BINANCE_KLINES_FALLBACK = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=400"

MW_HK_BASE = "https://www.marketwatch.com/investing/stock/{symbol}/download-data?countrycode=hk"
MW_HK_SYMBOLS = {"0700.HK": "700", "9988.HK": "9988"}

TD_BASE = "https://api.twelvedata.com/time_series"
TD_SYMBOLS = {
    "TSLA": "TSLA", "SMH": "SMH", "0700.HK": "700.HK", "9988.HK": "9988.HK",
    "GC=F": "XAU/USD", "SI=F": "XAG/USD", "HG=F": "CPER", "BTC-USD": "BTC/USD",
}

DASHBOARD_TICKERS = [
    "BTC-USD", "SMH", "TSLA", "9988.HK", "0700.HK",
    "GC=F", "SI=F", "HG=F",
]


def _date_str(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _fetch_binance_btc() -> list[dict[str, Any]]:
    import time
    for url in (BINANCE_KLINES, BINANCE_KLINES_FALLBACK):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            break
        except Exception:
            time.sleep(2)
            continue
    else:
        return []
    out = []
    for c in data:
        ts, o, h, l, close, v = c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
        dt = datetime.utcfromtimestamp(ts / 1000)
        out.append({"date": _date_str(dt), "open": o, "high": h, "low": l, "close": close, "volume": int(v)})
    return sorted(out, key=lambda x: x["date"])


def _fetch_stooq(ticker: str, days: int = 400) -> list[dict[str, Any]]:
    symbol = STOOQ_SYMBOLS.get(ticker, ticker.lower().replace(".", "-") + ".us" if "." not in ticker else ticker.replace(".", "-") + ".hk")
    if "0700" in ticker:
        symbol = "700.hk"
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    d1, d2 = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    url = STOOQ_BASE.format(symbol=symbol, d1=d1, d2=d2)
    try:
        req = Request(url, headers={"User-Agent": "Dashboard/1.0"})
        with urlopen(req, timeout=15) as r:
            text = r.read().decode("utf-8", errors="ignore")
        reader = csv.DictReader(text.strip().splitlines())
        out = []
        for row in reader:
            date_val = row.get("Date") or row.get("date")
            if not date_val:
                continue
            try:
                c = float(row.get("Close", 0) or row.get("close", 0))
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
    except Exception:
        return []


def _fetch_marketwatch_hk(ticker: str, days: int = 400) -> list[dict[str, Any]]:
    symbol = MW_HK_SYMBOLS.get(ticker)
    if not symbol:
        return []
    url = MW_HK_BASE.format(symbol=symbol)
    try:
        r = requests.get(url, headers={"User-Agent": "Dashboard/1.0"}, timeout=15)
        r.raise_for_status()
        text = r.text
        if "Date" in text and "," in text:
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
                    close_val = row.get("Close") or row.get("close") or ""
                    if not date_val or not close_val:
                        continue
                    try:
                        c = float(str(close_val).replace(",", ""))
                    except (TypeError, ValueError):
                        continue
                    try:
                        date_str = datetime.strptime(date_val[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                    out.append({"date": date_str, "open": c, "high": c, "low": c, "close": c, "volume": 0})
                if out:
                    start_cut = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                    out = [x for x in out if x["date"] >= start_cut]
                    return sorted(out, key=lambda x: x["date"])
        return []
    except Exception:
        return []


def _fetch_twelvedata(ticker: str, days: int = 400) -> list[dict[str, Any]]:
    key = os.environ.get("TWELVEDATA_API_KEY")
    if not key:
        return []
    sym = TD_SYMBOLS.get(ticker, ticker)
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {"symbol": sym, "interval": "1day", "start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"), "apikey": key}
    try:
        r = requests.get(TD_BASE, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values") or []
        out = []
        for v in vals:
            dt = (v.get("datetime") or "")[:10]
            try:
                c = float(v.get("close", 0))
            except (TypeError, ValueError):
                continue
            out.append({"date": dt, "open": c, "high": c, "low": c, "close": c, "volume": 0})
        return sorted(out, key=lambda x: x["date"]) if out else []
    except Exception:
        return []


def _stooq_mapped(ticker: str) -> str:
    return STOOQ_SYMBOLS.get(ticker, ticker.lower().replace(".", "-") + ".us" if "." not in ticker else ticker.replace(".", "-") + ".hk")


def _fetch_one_ticker(ticker: str, days: int) -> tuple[list[dict[str, Any]], str, str | None, int, str | None, str | None, bool, str | None]:
    """Return (series, provider, last_date, row_count, error_reason, mapped_symbol, is_proxy, proxy_for)."""
    # 1) yfinance (price_adjusted=True)
    try:
        ohlcv = fetch_ohlcv(tickers=[ticker], days=days)
        s = (ohlcv.get(ticker) or [])
        if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
            return (s, "yfinance", s[-1]["date"], len(s), None, ticker, False, None)
    except Exception:
        pass

    # 2) stooq (mapped_symbol, is_proxy for GC=F/SI=F/HG=F)
    try:
        mapped = _stooq_mapped(ticker)
        s = _fetch_stooq(ticker, days=days)
        if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
            is_proxy = ticker in PROXY_FOR
            proxy_for = PROXY_FOR.get(ticker) if is_proxy else None
            return (s, "stooq", s[-1]["date"], len(s), None, mapped, is_proxy, proxy_for)
    except Exception:
        pass

    # 2b) Alpha Vantage（可选，免费约 25 次/天）— 仅在其他源失败时用
    if ticker in AV_SYMBOLS_MAP and os.environ.get("ALPHAVANTAGE_API_KEY"):
        try:
            sym = AV_SYMBOLS_MAP[ticker]
            s = _fetch_alphavantage(sym, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                return (s, "alphavantage", s[-1]["date"], len(s), None, sym, False, None)
        except Exception:
            pass

    # 3) MarketWatch (HK only)
    if ticker in ("0700.HK", "9988.HK"):
        try:
            s = _fetch_marketwatch_hk(ticker, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                mapped = "700" if ticker == "0700.HK" else "9988"
                return (s, "marketwatch", s[-1]["date"], len(s), None, mapped, False, None)
        except Exception:
            pass

    # 4) TwelveData
    try:
        sym = TD_SYMBOLS.get(ticker, ticker)
        s = _fetch_twelvedata(ticker, days=days)
        if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
            is_proxy = ticker in PROXY_FOR
            proxy_for = PROXY_FOR.get(ticker) if is_proxy else None
            return (s, "twelvedata", s[-1]["date"], len(s), None, sym, is_proxy, proxy_for)
    except Exception:
        pass

    # 5) Binance (BTC only)
    if ticker == "BTC-USD":
        try:
            s = _fetch_binance_btc()
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                return (s, "binance", s[-1]["date"], len(s), None, "BTCUSDT", False, None)
        except Exception:
            pass

    # 6) Commodity ETF fallback: GC=F->GLD, SI=F->SLV, HG=F->CPER (stooq then yfinance)
    if ticker in COMMODITY_ETF_FALLBACK:
        etf = COMMODITY_ETF_FALLBACK[ticker]
        try:
            s = _fetch_stooq(etf, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                return (s, f"etf_fallback:{etf}", s[-1]["date"], len(s), None, etf.lower() + ".us", True, etf)
        except Exception:
            pass
        try:
            ohlcv = fetch_ohlcv(tickers=[etf], days=days)
            s = ohlcv.get(etf) or []
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                return (s, f"etf_fallback:{etf}", s[-1]["date"], len(s), None, etf, True, etf)
        except Exception:
            pass

    return ([], "fallback", None, 0, "all_sources_failed", None, False, None)


def download_price_map(
    days: int = 400,
    fred_api_key: str | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    """
    Returns (ohlcv_map, dataStatus_map). dataStatus includes: mapped_symbol, last_obs_date, asof_ts, is_proxy, proxy_for, stale_policy, price_adjusted.
    """
    ohlcv: dict[str, list[dict[str, Any]]] = {}
    data_status: dict[str, dict[str, Any]] = {}
    asof_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for ticker in DASHBOARD_TICKERS:
        out = _fetch_one_ticker(ticker, days=days)
        series, provider, last_date, row_count, error_reason, mapped_symbol, is_proxy, proxy_for = out
        ohlcv[ticker] = series if series else []

        if last_date:
            try:
                d = datetime.strptime(last_date, "%Y-%m-%d")
                freshness_days = (datetime.utcnow() - d.replace(tzinfo=None)).days
            except Exception:
                freshness_days = 999
        else:
            freshness_days = 999

        ok = bool(series and len(series) > 0 and (series[-1].get("close") or 0) != 0)
        note = "stale/fallback" if provider == "fallback" or not series else None
        if mapped_symbol and ticker in ("0700.HK", "9988.HK"):
            note = (note or "") + f"; symbol_mapped_to={mapped_symbol}" if note else f"symbol_mapped_to={mapped_symbol}"
        provider_display = f"proxy:{proxy_for}" if is_proxy and proxy_for else provider

        data_status[ticker] = {
            "provider": provider_display,
            "freshness_days": freshness_days,
            "ok": ok,
            "note": note,
            "last_date": last_date,
            "last_obs_date": last_date,
            "row_count": row_count,
            "error_reason": error_reason,
            "mapped_symbol": mapped_symbol,
            "asof_ts": asof_ts,
            "is_proxy": is_proxy,
            "proxy_for": proxy_for,
            "stale_policy": None,
            "price_adjusted": provider == "yfinance",
        }

    # DXY proxy and commodity fallbacks for weekly chain
    for t in ["DX-Y.NYB", "GLD", "SLV", "CPER", "USO"]:
        if t not in ohlcv:
            ohlcv[t] = fetch_ohlcv(tickers=[t], days=days).get(t) or []

    return ohlcv, data_status
