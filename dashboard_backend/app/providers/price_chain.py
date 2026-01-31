"""
Provider chain per ticker: yfinance -> stooq -> marketwatch (HK) -> twelvedata -> binance (BTC).
Returns ohlcv map and dataStatus per ticker with: provider, last_obs_date, row_count, mapped_symbol, is_proxy, proxy_for, asof_ts, stale_policy, price_adjusted.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from . import binance as binance_prov
from . import stooq as stooq_prov
from . import marketwatch as mw_prov
from . import twelvedata as td_prov
from . import alphavantage as av_prov

# Optional yfinance
try:
    import yfinance as yf
except ImportError:
    yf = None

ASSET_DEFS_TICKERS = [
    "BTC-USD", "SMH", "TSLA", "9988.HK", "0700.HK",
    "GC=F", "SI=F", "HG=F",
]

# Ticker -> proxy symbol when we use proxy (GC=F->xauusd, SI=F->xagusd, HG=F->cper)
PROXY_FOR: dict[str, str] = {"GC=F": "xauusd", "SI=F": "xagusd", "HG=F": "cper.us"}
# Commodity ETF fallback when futures/spot all fail: GC=F->GLD, SI=F->SLV, HG=F->CPER
COMMODITY_ETF_FALLBACK: dict[str, str] = {"GC=F": "GLD", "SI=F": "SLV", "HG=F": "CPER"}

# TwelveData symbol mapping: our ticker -> TwelveData symbol
TD_SYMBOLS = {
    "TSLA": "TSLA",
    "SMH": "SMH",
    "0700.HK": "700.HK",
    "9988.HK": "9988.HK",
    "GC=F": "XAU/USD",
    "SI=F": "XAG/USD",
    "HG=F": "CPER",
    "BTC-USD": "BTC/USD",
}


def _yf_fetch(ticker: str, days: int) -> list[dict[str, Any]]:
    if yf is None:
        return []
    try:
        end = datetime.utcnow()
        start = end.replace(year=end.year - 2)
        obj = yf.Ticker(ticker)
        hist = obj.history(start=start, end=end, auto_adjust=True)
        if hist is None or hist.empty or len(hist) < 2:
            return []
        hist = hist.reset_index()
        col_date = "Date" if "Date" in hist.columns else "Datetime"
        if col_date not in hist.columns:
            return []
        out = []
        for _, row in hist.iterrows():
            dt = row[col_date]
            if hasattr(dt, "strftime"):
                date_str = dt.strftime("%Y-%m-%d")
            else:
                continue
            try:
                c = float(row.get("Close", 0))
            except (TypeError, ValueError):
                continue
            out.append({"date": date_str, "open": c, "high": c, "low": c, "close": c, "volume": int(row.get("Volume", 0) or 0)})
        return sorted(out, key=lambda x: x["date"])[-days:] if out else []
    except Exception:
        return []


def _td_symbol(ticker: str) -> str:
    return TD_SYMBOLS.get(ticker, ticker.replace("=", "").replace("-", "/") if "=" in ticker or "-" in ticker else ticker)


def _stooq_mapped(ticker: str) -> str:
    return stooq_prov.STOOQ_SYMBOLS.get(ticker, ticker.lower().replace(".", "-") + ".us" if "." not in ticker else ticker.replace(".", "-") + ".hk")


def fetch_one_ticker(
    ticker: str,
    days: int = 400,
) -> tuple[list[dict[str, Any]], str, str | None, int, str | None, str | None, bool, str | None]:
    """
    Try providers in order. Return (series, provider, last_date, row_count, error_reason, mapped_symbol, is_proxy, proxy_for).
    """
    # 1) yfinance (price_adjusted=True)
    if yf is not None:
        try:
            s = _yf_fetch(ticker, days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                return (s, "yfinance", last, len(s), None, ticker, False, None)
        except Exception:
            pass

    # 2) stooq (mapped_symbol, is_proxy for GC=F/SI=F/HG=F)
    try:
        mapped = _stooq_mapped(ticker)
        s = stooq_prov.fetch_stooq(ticker, days=days)
        if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
            last = s[-1]["date"]
            is_proxy = ticker in PROXY_FOR
            proxy_for = PROXY_FOR.get(ticker) if is_proxy else None
            return (s, "stooq", last, len(s), None, mapped, is_proxy, proxy_for)
    except Exception:
        pass

    # 2b) Alpha Vantage (optional, free tier ~25 req/day) — 仅在其他源失败时用，省配额
    if ticker in av_prov.AV_SYMBOLS and os.environ.get("ALPHAVANTAGE_API_KEY"):
        try:
            sym = av_prov.AV_SYMBOLS[ticker]
            s = av_prov.fetch_alphavantage(sym, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                return (s, "alphavantage", last, len(s), None, sym, False, None)
        except Exception:
            pass

    # 3) MarketWatch (HK only)
    if ticker in ("0700.HK", "9988.HK"):
        try:
            s = mw_prov.fetch_marketwatch_hk(ticker, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                mapped = "700" if ticker == "0700.HK" else "9988"
                return (s, "marketwatch", last, len(s), None, mapped, False, None)
        except Exception:
            pass

    # 4) TwelveData (mapped_symbol)
    if os.environ.get("TWELVEDATA_API_KEY"):
        try:
            sym = _td_symbol(ticker)
            s = td_prov.fetch_twelvedata(sym, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                is_proxy = ticker in PROXY_FOR
                proxy_for = PROXY_FOR.get(ticker) if is_proxy else None
                return (s, "twelvedata", last, len(s), None, sym, is_proxy, proxy_for)
        except Exception:
            pass

    # 5) Binance (BTC only)
    if ticker == "BTC-USD":
        try:
            s = binance_prov.fetch_btc_klines()
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                return (s, "binance", last, len(s), None, "BTCUSDT", False, None)
        except Exception:
            pass

    # 6) Commodity ETF fallback: GC=F->GLD, SI=F->SLV, HG=F->CPER (stooq then yfinance)
    if ticker in COMMODITY_ETF_FALLBACK:
        etf = COMMODITY_ETF_FALLBACK[ticker]
        try:
            s = stooq_prov.fetch_stooq(etf, days=days)
            if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                last = s[-1]["date"]
                return (s, f"etf_fallback:{etf}", last, len(s), None, etf.lower() + ".us", True, etf)
        except Exception:
            pass
        if yf is not None:
            try:
                s = _yf_fetch(etf, days)
                if s and len(s) > 0 and (s[-1].get("close") or 0) != 0:
                    last = s[-1]["date"]
                    return (s, f"etf_fallback:{etf}", last, len(s), None, etf, True, etf)
            except Exception:
                pass

    return ([], "fallback", None, 0, "all_sources_failed", None, False, None)


def fetch_all_prices(days: int = 400) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    """
    Fetch prices for all dashboard tickers. Return (ohlcv_map, dataStatus_map).
    dataStatus[ticker] includes: provider, freshness_days, ok, note, last_obs_date, row_count, error_reason,
    mapped_symbol, asof_ts, is_proxy, proxy_for, stale_policy, price_adjusted.
    """
    ohlcv: dict[str, list[dict[str, Any]]] = {}
    data_status: dict[str, dict[str, Any]] = {}
    asof_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for ticker in ASSET_DEFS_TICKERS:
        out = fetch_one_ticker(ticker, days=days)
        series, provider, last_date, row_count, error_reason, mapped_symbol, is_proxy, proxy_for = out
        if series:
            ohlcv[ticker] = series
        else:
            ohlcv[ticker] = []

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
        if mapped_symbol and ticker in ("0700.HK", "9988.HK") and note:
            note = (note or "") + f"; symbol_mapped_to={mapped_symbol}"
        elif mapped_symbol and (ticker in ("0700.HK", "9988.HK")):
            note = f"symbol_mapped_to={mapped_symbol}" if note else None

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

    return ohlcv, data_status
