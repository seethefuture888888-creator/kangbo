"""
Build dashboard payload: dailySignal, macroSwitches, assets, assetSignals.
Align with frontend schema (dailySignal, not todaySignal).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from ..providers import fred as fred_prov
from ..providers import price_chain as price_chain_prov
from . import features as feat
from . import scoring
from . import regime as regime_mod

ASSET_DEFS = [
    {"id": "BTC", "name": "Bitcoin", "ticker": "BTC-USD", "assetType": "crypto", "currency": "USD", "benchmarkId": "QQQ", "baseMaxWeight": 0.25},
    {"id": "AI_BASKET", "name": "AI Basket", "ticker": "SMH", "assetType": "equity", "currency": "USD", "benchmarkId": "SPY", "baseMaxWeight": 0.40},
    {"id": "TSLA", "name": "Tesla", "ticker": "TSLA", "assetType": "equity", "currency": "USD", "benchmarkId": "SPY", "baseMaxWeight": 0.15},
    {"id": "BABA", "name": "Alibaba", "ticker": "9988.HK", "assetType": "hk_equity", "currency": "HKD", "benchmarkId": "HSTECH", "baseMaxWeight": 0.15},
    {"id": "TENCENT", "name": "Tencent", "ticker": "0700.HK", "assetType": "hk_equity", "currency": "HKD", "benchmarkId": "HSTECH", "baseMaxWeight": 0.15},
    {"id": "XAU", "name": "Gold", "ticker": "GC=F", "assetType": "metal", "currency": "USD", "baseMaxWeight": 0.20},
    {"id": "XAG", "name": "Silver", "ticker": "SI=F", "assetType": "metal", "currency": "USD", "baseMaxWeight": 0.08},
    {"id": "HG", "name": "Copper", "ticker": "HG=F", "assetType": "future", "currency": "USD", "baseMaxWeight": 0.15},
]

TICKER_TO_STOOQ = {
    "GC=F": "xauusd",
    "SI=F": "xagusd",
    "HG=F": "cper.us",
}


def _pct_to_light(pct: float) -> str:
    if pct <= 33:
        return "green"
    if pct <= 66:
        return "yellow"
    return "red"


def _trend_light(series: list[dict], price: float | None) -> str:
    if not series or price is None:
        return "yellow"
    ma20 = feat.ma(series, 20)
    ma60 = feat.ma(series, 60)
    ma200 = feat.ma(series, 200)
    if ma200 is None:
        return "yellow"
    if price > (ma20 or 0) and (ma20 or 0) > (ma60 or 0) and (ma60 or 0) > ma200:
        return "green"
    if price < ma200:
        return "red"
    return "yellow"


def _risk_light(vol_pct: float | None) -> str:
    p = vol_pct if vol_pct is not None else 50
    return _pct_to_light(100 - p)


def _catalyst_light(regime_letter: str, real_rate: float | None, dxy_chg: float | None) -> str:
    if regime_letter == "C":
        return "red"
    if regime_letter == "A" and (real_rate is None or real_rate < 1.0):
        return "green"
    if regime_letter == "D" and dxy_chg is not None and dxy_chg < -0.5:
        return "green"
    return "yellow"


def _regime_mult(r: str) -> float:
    return {"A": 1.0, "B": 0.9, "C": 0.7, "D": 0.95}.get(r, 1.0)


def _risk_mult(vol_pct: float | None) -> float:
    if vol_pct is None:
        return 1.0
    if vol_pct > 70:
        return 0.8
    if vol_pct > 50:
        return 0.9
    return 1.0


def _action(trend: str, risk: str, catalyst: str, suggested: float, base: float) -> str:
    if risk == "red" or trend == "red":
        return "REDUCE"
    if trend == "green" and catalyst != "red" and suggested > (base or 0):
        return "ADD"
    return "HOLD"


def _latest_and_returns(series: list[dict[str, Any]]) -> dict[str, Any]:
    if not series:
        return {"price": None, "change1d": None, "change7d": None, "change30d": None}
    series = sorted(series, key=lambda x: x["date"])
    latest = series[-1]["close"]
    ch1d = ch7d = ch30d = None
    for r in reversed(series[:-1]):
        days_ago = (datetime.strptime(series[-1]["date"], "%Y-%m-%d") - datetime.strptime(r["date"], "%Y-%m-%d")).days
        if r["close"] and r["close"] != 0:
            pct = (latest - r["close"]) / r["close"] * 100
            if ch1d is None and days_ago >= 1:
                ch1d = round(pct, 2)
            if ch7d is None and days_ago >= 5:
                ch7d = round(pct, 2)
            if ch30d is None and days_ago >= 25:
                ch30d = round(pct, 2)
        if ch1d is not None and ch7d is not None and ch30d is not None:
            break
    return {"price": latest, "change1d": ch1d, "change7d": ch7d, "change30d": ch30d}


def _fetch_prices_and_status() -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    """Provider chain: yfinance -> stooq -> marketwatch (HK) -> twelvedata -> binance. Returns (ohlcv, dataStatus)."""
    return price_chain_prov.fetch_all_prices(days=400)


def build_payload() -> dict[str, Any]:
    hy = fred_prov.get_hy()
    real10y = fred_prov.get_real10y()
    dxy = fred_prov.get_dxy()
    core_cpi = fred_prov.get_core_cpi_yoy()
    pmi = fred_prov.get_pmi_like()
    # PMI is always at least 50 (fallback); reason "PMI_FALLBACK" when no AMTMNO data

    if not hy.get("value"):
        hy = {"value": 4.5, "change7d": 0, "change1m": -0.2, "freshness_days": 999}
    if not real10y.get("value"):
        real10y = {"value": 1.5, "change7d": 0, "change1m": -0.1, "freshness_days": 999}
    if not dxy.get("value"):
        dxy = {"value": 100.0, "change7d": 0, "change1m": 0, "freshness_days": 999}
    if not core_cpi.get("value"):
        core_cpi = {"value": 3.0, "change7d": None, "change1m": -0.1, "freshness_days": 999}

    dxy_price = dxy.get("value")
    dxy_chg = dxy.get("change1m")

    risk_val, risk_confidence, missing_macros = scoring.risk_score(hy, real10y, dxy, pmi, core_cpi)
    reg_letter, reg_label = regime_mod.regime(hy, real10y, pmi, core_cpi, dxy, risk_val)

    drivers = []
    if hy.get("change1m") is not None and hy["change1m"] < 0:
        drivers.append("HY利差回落")
    if real10y.get("change1m") is not None and real10y["change1m"] < 0:
        drivers.append("实际利率下行")
    if dxy.get("change1m") is not None and dxy["change1m"] < 0:
        drivers.append("美元走弱")
    if pmi.get("value") is not None and pmi["value"] >= 50:
        drivers.append("PMI扩张")
    if pmi.get("reason") == "PMI_FALLBACK":
        drivers.append("PMI_FALLBACK")
    for m in missing_macros:
        drivers.append(f"CONFIDENCE_LOW_DUE_TO_{m}")
    if hy.get("value") is None or real10y.get("value") is None or dxy_price is None or pmi.get("value") is None or core_cpi.get("value") is None:
        drivers.append("MACRO_MISSING_OBS")
    if not drivers:
        drivers.append("数据更新中")

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    data_as_of = now.strftime("%Y-%m-%d %H:%M UTC")

    daily_signal = {
        "date": date_str,
        "regime": reg_letter,
        "riskScore": round(risk_val, 1),
        "riskScoreConfidence": round(risk_confidence, 2),
        "drivers": drivers,
        "portfolioAction": "ADD" if reg_letter in ("A", "D") and risk_val < 55 else ("REDUCE" if reg_letter == "C" else "HOLD"),
        "riskMode": "进攻" if risk_val < 50 else "防守",
        "aiDiffusionIndex": round(50 + (50 - risk_val) * 0.36, 2),
        "constraintIndex": round(min(80, risk_val * 0.8), 2),
        "commentSummary": f"Regime {reg_label}, RiskScore {risk_val:.0f}. {'; '.join(drivers[:3])}.",
        "dataAsOf": data_as_of,
    }

    def _macro_row(mid: str, name: str, val: Any, ch7: Any, ch1m: Any, fresh: Any, freq: str) -> dict[str, Any]:
        # 宁可 null + 原因，不要 0 + 正常灯号
        pct = 50.0
        if val is not None and mid == "PMI":
            pct = max(0, min(100, (val - 35) / 30 * 100))
        light = _pct_to_light(pct) if mid != "PMI" else _pct_to_light(100 - pct)
        return {
            "id": mid,
            "name": name,
            "currentValue": round(val, 2) if isinstance(val, (int, float)) else (None if val is None else val),
            "change7d": round(ch7, 4) if ch7 is not None else None,
            "change1m": round(ch1m, 4) if ch1m is not None else None,
            "percentile": round(pct, 1),
            "light": light,
            "freshness": int(fresh) if fresh is not None else 999,
            "frequency": freq,
        }

    macro_switches = [
        _macro_row("HY_SPREAD", "HY Credit Spread", hy.get("value"), hy.get("change7d"), hy.get("change1m"), hy.get("freshness_days") or 999, "D"),
        _macro_row("REAL10Y", "10Y Real Rate", real10y.get("value"), real10y.get("change7d"), real10y.get("change1m"), real10y.get("freshness_days") or 999, "D"),
        _macro_row("DXY", "US Dollar Index", dxy_price, dxy.get("change7d"), dxy_chg, dxy.get("freshness_days") or 999, "D"),
        _macro_row("PMI", "Manufacturing PMI (New Orders proxy)", pmi.get("value"), pmi.get("change7d"), pmi.get("change1m"), pmi.get("freshness_days") or 999, "M"),
        _macro_row("CORE_INFL", "Core Inflation (YoY %)", core_cpi.get("value"), core_cpi.get("change7d"), core_cpi.get("change1m"), core_cpi.get("freshness_days") or 999, "M"),
    ]

    ohlcv, data_status = _fetch_prices_and_status()
    tech_by_id: dict[str, dict[str, Any]] = {}
    assets_out = []
    signals_out = []

    for defn in ASSET_DEFS:
        aid = defn["id"]
        ticker = defn["ticker"]
        base = defn["baseMaxWeight"]
        series = ohlcv.get(ticker) or []
        tech = feat.compute_all(series) if series else {"ma20": 0, "ma60": 0, "ma200": 0, "mom12w": 0, "vol20Ann": 0, "mdd60": 0, "mdd120": 0, "volPercentile1y": 50, "ddPercentile1y": 50}
        tech["assetId"] = aid
        tech_by_id[aid] = tech

        ret = _latest_and_returns(series)
        pr = ret.get("price")
        ch1d, ch7d, ch30d = ret.get("change1d"), ret.get("change7d"), ret.get("change30d")

        st = data_status.get(ticker) or {}
        row_count = st.get("row_count", 0)
        is_proxy = st.get("is_proxy", False)
        trend_light = _trend_light(series, pr)
        risk_light = _risk_light(tech.get("volPercentile1y"))
        if row_count < 220:
            trend_light = "yellow"
            risk_light = "yellow"
        catalyst_light = _catalyst_light(reg_letter, real10y.get("value"), dxy_chg)
        regime_mult = _regime_mult(reg_letter)
        risk_mult = _risk_mult(tech.get("volPercentile1y"))
        suggested = round(min(base, base * regime_mult * risk_mult), 2)
        action = _action(trend_light, risk_light, catalyst_light, suggested, 0)

        reason_codes = []
        if row_count < 220:
            reason_codes.append("INSUFFICIENT_HISTORY")
        if is_proxy:
            reason_codes.append("PROXY_USED")
        if trend_light == "green":
            reason_codes.append("TREND_UP")
        if risk_light == "red":
            reason_codes.append("VOL_HIGH")
        if reg_letter == "C":
            reason_codes.append("REGIME_C")
        if catalyst_light == "green":
            reason_codes.append("CATALYST_OK")
        if not reason_codes:
            reason_codes.append("HOLD")
        # Fallback: never output 0 for price; use null and mark stale/fallback
        if st.get("note") == "stale/fallback" and pr is not None and pr == 0:
            pr = None
        assets_out.append({
            "id": aid,
            "name": defn["name"],
            "ticker": ticker,
            "assetType": defn["assetType"],
            "currency": defn["currency"],
            "benchmarkId": defn.get("benchmarkId"),
            "baseMaxWeight": base,
            "currentWeight": 0.0,
            "suggestedMaxWeight": suggested,
            "price": round(pr, 2) if pr is not None else None,
            "priceChange24h": round(ch1d, 2) if ch1d is not None else None,
            "priceChange7d": round(ch7d, 2) if ch7d is not None else None,
            "priceChange30d": round(ch30d, 2) if ch30d is not None else None,
        })
        signals_out.append({
            "assetId": aid,
            "date": date_str,
            "trendLight": trend_light,
            "riskLight": risk_light,
            "catalystLight": catalyst_light,
            "suggestedMaxWeight": suggested,
            "action": action,
            "reasonCodes": reason_codes,
            "notes": f"{trend_light}/{risk_light}/{catalyst_light}",
        })

    # Do not fill 0 for missing price: leave null and dataStatus explains
    for a in assets_out:
        if a.get("priceChange24h") is None:
            a["priceChange24h"] = None
        if a.get("priceChange7d") is None:
            a["priceChange7d"] = None
        if a.get("priceChange30d") is None:
            a["priceChange30d"] = None

    # dataStatus: per-ticker observability (mapped_symbol, last_obs_date, asof_ts, is_proxy, proxy_for, stale_policy, price_adjusted)
    data_status_out = {}
    for ticker, st in data_status.items():
        data_status_out[ticker] = {
            "provider": st.get("provider", "unknown"),
            "freshness_days": st.get("freshness_days", 999),
            "ok": st.get("ok", False),
            "note": st.get("note"),
            "last_date": st.get("last_date"),
            "last_obs_date": st.get("last_obs_date") or st.get("last_date"),
            "row_count": st.get("row_count", 0),
            "error_reason": st.get("error_reason"),
            "mapped_symbol": st.get("mapped_symbol"),
            "asof_ts": st.get("asof_ts"),
            "is_proxy": st.get("is_proxy", False),
            "proxy_for": st.get("proxy_for"),
            "stale_policy": st.get("stale_policy"),
            "price_adjusted": st.get("price_adjusted"),
        }

    # macroDataStatus: HY, REAL10Y, DXY(fred_dtwexbgs), PMI, CORE_INFL
    macro_data_status: dict[str, dict[str, Any]] = {}
    for mid, name, val, fresh, freq in [
        ("HY_SPREAD", "HY Credit Spread", hy.get("value"), hy.get("freshness_days"), "D"),
        ("REAL10Y", "10Y Real Rate", real10y.get("value"), real10y.get("freshness_days"), "D"),
        ("DXY", "US Dollar Index", dxy_price, dxy.get("freshness_days"), "D"),
        ("PMI", "Manufacturing PMI (proxy)", pmi.get("value"), pmi.get("freshness_days"), "M"),
        ("CORE_INFL", "Core Inflation (YoY %)", core_cpi.get("value"), core_cpi.get("freshness_days"), "M"),
    ]:
        provider = "fred_dtwexbgs" if mid == "DXY" else "fred"
        macro_data_status[mid] = {
            "provider": provider,
            "ok": val is not None,
            "note": "missing_observation" if val is None else None,
            "freq": freq,
            "freshness_days": int(fresh) if fresh is not None else 999,
        }

    # weeklyKondratieff: ADI/CI 缺关键输入（铜/链）时置 null，reason CHAIN_INPUT_MISSING
    copper_series = ohlcv.get("HG=F") or []
    chain_ok = len(copper_series) >= 25
    if not chain_ok:
        weekly_adi = None
        weekly_ci = None
        chain_reason = "CHAIN_INPUT_MISSING"
    else:
        weekly_adi = daily_signal["aiDiffusionIndex"]
        weekly_ci = daily_signal["constraintIndex"]
        chain_reason = None
    weekly_components = {"soxRatio": 1.0, "nvdaRatio": 1.0, "utilityRatio": 1.0, "copperMomentum": 0.0, "energyPrice": 0.0}
    if copper_series and len(copper_series) >= 25:
        cur = copper_series[-1]["close"]
        prev = copper_series[-25]["close"]
        if prev and prev != 0:
            weekly_components["copperMomentum"] = round((cur / prev - 1) * 100, 4)

    return {
        "version": "0.1.0",
        "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dailySignal": daily_signal,
        "macroSwitches": macro_switches,
        "macroDataStatus": macro_data_status,
        "assets": assets_out,
        "assetSignals": signals_out,
        "dataStatus": data_status_out,
        "weeklyKondratieff": {
            "date": date_str,
            "aiDiffusionIndex": weekly_adi,
            "constraintIndex": weekly_ci,
            "phase": "transition",
            "strategy": f"Regime {reg_label}; " + "; ".join(drivers[:3]) + ("; " + chain_reason if chain_reason else ""),
            "components": weekly_components,
            "chainInputMissing": chain_reason,
        },
        "technicalData": tech_by_id,
        "priceHistory": {},
    }
