"""
Build dashboard payload: assets, macroSwitches, dailySignal, assetSignals.
Structure aligned with frontend types (DailySignal, MacroSwitch, AssetSignal).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import features
from . import regime as regime_module
from . import scoring
from .providers.yfinance_provider import latest_price_and_returns

# Asset definitions: id, name, ticker, assetType, currency, benchmarkId, baseMaxWeight
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

TICKER_TO_ID = {d["ticker"]: d["id"] for d in ASSET_DEFS}


def _value_to_percentile(val: float | None, low: float, high: float, higher_is_bad: bool = True) -> float:
    """Rough percentile 0-100. If higher_is_bad, higher value -> higher percentile."""
    if val is None:
        return 50.0
    p = (val - low) / (high - low) * 100 if high != low else 50.0
    p = max(0, min(100, p))
    return 100 - p if not higher_is_bad else p


def _percentile_to_light(pct: float) -> str:
    if pct <= 33:
        return "green"
    if pct <= 66:
        return "yellow"
    return "red"


def _trend_light(series: list[dict[str, Any]], price: float) -> str:
    """Trend: price vs MA20/60/200. Green = uptrend, red = downtrend."""
    ma20 = features.ma20(series)
    ma60 = features.ma60(series)
    ma200 = features.ma200(series)
    if ma200 is None:
        return "yellow"
    if price > ma20 and (ma20 or 0) > (ma60 or 0) and (ma60 or 0) > ma200:
        return "green"
    if price < ma200:
        return "red"
    return "yellow"


def _risk_light(vol_pct: float | None, dd_pct: float | None) -> str:
    """Risk: vol/drawdown percentile. Low = green."""
    p = vol_pct if vol_pct is not None else (dd_pct if dd_pct is not None else 50)
    return _percentile_to_light(100 - p)  # low percentile = green


def _catalyst_light(regime: str, real_rate: float | None, dxy_change1m: float | None) -> str:
    """Catalyst: regime + real rate + DXY. A + low real rate = green; C = red."""
    if regime == "C":
        return "red"
    if regime == "A" and (real_rate is None or real_rate < 1.0):
        return "green"
    if regime == "D" and (dxy_change1m is not None and dxy_change1m < -0.5):
        return "green"
    return "yellow"


def _regime_multiplier(regime_letter: str) -> float:
    if regime_letter == "A":
        return 1.0
    if regime_letter == "B":
        return 0.9
    if regime_letter == "C":
        return 0.7
    return 0.95  # D


def _risk_multiplier(vol_pct: float | None) -> float:
    if vol_pct is None:
        return 1.0
    if vol_pct > 70:
        return 0.8
    if vol_pct > 50:
        return 0.9
    return 1.0


def _action(trend_light: str, risk_light: str, catalyst_light: str, suggested: float, base: float) -> str:
    if risk_light == "red" or trend_light == "red":
        return "REDUCE"
    if trend_light == "green" and catalyst_light != "red" and suggested > (base or 0):
        return "ADD"
    return "HOLD"


def build_daily_signal(
    date_str: str,
    regime_letter: str,
    regime_label: str,
    risk_score: float,
    drivers: list[str],
    data_as_of: str,
    risk_score_confidence: float | None = None,
) -> dict[str, Any]:
    risk_mode = "进攻" if risk_score < 50 else "防守"
    portfolio_action = "ADD" if regime_letter in ("A", "D") and risk_score < 55 else ("REDUCE" if regime_letter == "C" else "HOLD")
    out = {
        "date": date_str,
        "regime": regime_letter,
        "riskScore": round(risk_score, 1),
        "drivers": drivers,
        "portfolioAction": portfolio_action,
        "riskMode": risk_mode,
        "aiDiffusionIndex": 50 + (50 - risk_score) * 0.36,
        "constraintIndex": min(80, risk_score * 0.8),
        "commentSummary": f"Regime {regime_label}, RiskScore {risk_score:.0f}. {'; '.join(drivers[:3])}.",
        "dataAsOf": data_as_of,
    }
    if risk_score_confidence is not None:
        out["riskScoreConfidence"] = round(risk_score_confidence, 2)
    return out


def build_macro_switches(
    hy: dict[str, Any],
    real10y: dict[str, Any],
    dxy: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
) -> list[dict[str, Any]]:
    def row(mid: str, name: str, val: Any, ch7: Any, ch1m: Any, fresh: Any, freq: str) -> dict[str, Any]:
        pct = _value_to_percentile(val, 0, 100, higher_is_bad=(mid != "PMI")) if val is not None else 50.0
        if mid == "PMI" and val is not None:
            pct = _value_to_percentile(val, 40, 55, higher_is_bad=False)
        return {
            "id": mid,
            "name": name,
            "currentValue": round(val, 2) if isinstance(val, (int, float)) else (None if val is None else val),
            "change7d": round(ch7, 4) if ch7 is not None else None,
            "change1m": round(ch1m, 4) if ch1m is not None else None,
            "percentile": round(pct, 1),
            "light": _percentile_to_light(pct) if mid != "PMI" else _percentile_to_light(100 - pct),
            "freshness": int(fresh) if fresh is not None else 999,
            "frequency": freq,
        }
    dxy_fresh = dxy.get("freshness_days") if dxy.get("price") is not None else 999
    out = [
        row("HY_SPREAD", "HY Credit Spread", hy.get("value"), hy.get("change7d"), hy.get("change1m"), hy.get("freshness_days") or 999, "D"),
        row("REAL10Y", "10Y Real Rate", real10y.get("value"), real10y.get("change7d"), real10y.get("change1m"), real10y.get("freshness_days") or 999, "D"),
        row("DXY", "US Dollar Index", dxy.get("price"), dxy.get("change7d"), dxy.get("change30d"), dxy_fresh if dxy_fresh is not None else 999, "D"),
    ]
    pmi_fresh = pmi.get("freshness_days")
    pmi_val = pmi.get("value") if pmi.get("value") is not None else 50.0
    out.append(row("PMI", "Manufacturing PMI (New Orders proxy)", pmi_val, pmi.get("change7d"), pmi.get("change1m"), pmi_fresh if pmi_fresh is not None else 999, "M"))
    out.append(row("CORE_INFL", "Core Inflation (YoY %)", core_cpi.get("value"), core_cpi.get("change7d"), core_cpi.get("change1m"), core_cpi.get("freshness_days") if core_cpi.get("value") is not None else 999, "M"))
    return out


def build_assets_and_signals(
    ohlcv: dict[str, list[dict[str, Any]]],
    tech_by_id: dict[str, dict[str, Any]],
    regime_letter: str,
    real_rate: float | None,
    dxy_change1m: float | None,
    date_str: str,
    data_status: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data_status = data_status or {}
    assets = []
    signals = []
    for defn in ASSET_DEFS:
        aid = defn["id"]
        ticker = defn["ticker"]
        base = defn["baseMaxWeight"]
        series = ohlcv.get(ticker) or []
        pr = None
        ch1d = ch7d = ch30d = None
        if series:
            ret = latest_price_and_returns(ticker, ohlcv)
            pr = ret.get("price")
            ch1d = ret.get("change1d")
            ch7d = ret.get("change7d")
            ch30d = ret.get("change30d")
        st = data_status.get(ticker) or {}
        if st.get("note") == "stale/fallback" and pr is not None and pr == 0:
            pr = None
        tech = tech_by_id.get(aid) or {}
        vol_pct = tech.get("volPercentile1y")
        dd_pct = tech.get("ddPercentile1y")
        row_count = st.get("row_count", 0)
        is_proxy = st.get("is_proxy", False)
        trend_light = _trend_light(series, pr) if pr is not None and series else "yellow"
        risk_light = _risk_light(vol_pct, dd_pct)
        if row_count < 220:
            trend_light = "yellow"
            risk_light = "yellow"
        catalyst_light = _catalyst_light(regime_letter, real_rate, dxy_change1m)
        regime_mult = _regime_multiplier(regime_letter)
        risk_mult = _risk_multiplier(vol_pct)
        suggested = round(base * regime_mult * risk_mult, 2)
        suggested = min(suggested, base)
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
        if regime_letter == "C":
            reason_codes.append("REGIME_C")
        if catalyst_light == "green":
            reason_codes.append("CATALYST_OK")
        if not reason_codes:
            reason_codes.append("HOLD")
        # Never output 0 for price when fallback; use null
        assets.append({
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
        signals.append({
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
    return assets, signals


def build_payload(
    hy: dict[str, Any],
    real10y: dict[str, Any],
    dxy: dict[str, Any],
    pmi: dict[str, Any],
    core_cpi: dict[str, Any],
    ohlcv: dict[str, list[dict[str, Any]]],
    tech_by_id: dict[str, dict[str, Any]],
    weekly_components: dict[str, Any] | None = None,
    data_status: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    risk_score_val, risk_confidence, missing_macros = scoring.risk_score(hy, real10y, dxy, pmi, core_cpi)
    reg_letter, reg_label = regime_module.regime(hy, real10y, pmi, core_cpi, dxy.get("change30d"))
    drivers = []
    if hy.get("change1m") is not None and hy["change1m"] < 0:
        drivers.append("HY利差回落")
    if real10y.get("change1m") is not None and real10y["change1m"] < 0:
        drivers.append("实际利率下行")
    if dxy.get("change30d") is not None and dxy["change30d"] < 0:
        drivers.append("美元走弱")
    if pmi.get("value") is not None and pmi["value"] >= 50:
        drivers.append("PMI扩张")
    if pmi.get("reason") == "PMI_FALLBACK":
        drivers.append("PMI_FALLBACK")
    for m in missing_macros:
        drivers.append(f"CONFIDENCE_LOW_DUE_TO_{m}")
    if hy.get("value") is None or real10y.get("value") is None or (dxy.get("price") is None and dxy.get("value") is None) or pmi.get("value") is None or core_cpi.get("value") is None:
        drivers.append("MACRO_MISSING_OBS")
    if not drivers:
        drivers.append("数据更新中")
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    data_as_of = now.strftime("%Y-%m-%d %H:%M UTC")
    daily = build_daily_signal(date_str, reg_letter, reg_label, risk_score_val, drivers, data_as_of, risk_score_confidence=risk_confidence)
    macro_switches = build_macro_switches(hy, real10y, dxy, pmi, core_cpi)
    assets, asset_signals = build_assets_and_signals(
        ohlcv, tech_by_id, reg_letter, real10y.get("value"), dxy.get("change30d"), date_str, data_status=data_status
    )
    data_status_out = {}
    for ticker, st in (data_status or {}).items():
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
    macro_data_status = {}
    for mid, val, fresh, freq in [
        ("HY_SPREAD", hy.get("value"), hy.get("freshness_days"), "D"),
        ("REAL10Y", real10y.get("value"), real10y.get("freshness_days"), "D"),
        ("DXY", dxy.get("price") or dxy.get("value"), dxy.get("freshness_days"), "D"),
        ("PMI", pmi.get("value"), pmi.get("freshness_days"), "M"),
        ("CORE_INFL", core_cpi.get("value"), core_cpi.get("freshness_days"), "M"),
    ]:
        macro_data_status[mid] = {
            "provider": "fred_dtwexbgs" if mid == "DXY" else "fred",
            "ok": val is not None,
            "note": "missing_observation" if val is None else None,
            "freq": freq,
            "freshness_days": int(fresh) if fresh is not None else 999,
        }
    copper_series = (ohlcv.get("HG=F") or []) if ohlcv else []
    chain_ok = len(copper_series) >= 25
    if not chain_ok:
        weekly_adi = None
        weekly_ci = None
        chain_reason = "CHAIN_INPUT_MISSING"
    else:
        weekly_adi = daily["aiDiffusionIndex"]
        weekly_ci = daily["constraintIndex"]
        chain_reason = None
    wc = weekly_components or {}
    return {
        "version": "0.1.0",
        "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dailySignal": daily,
        "macroSwitches": macro_switches,
        "macroDataStatus": macro_data_status,
        "assets": assets,
        "assetSignals": asset_signals,
        "dataStatus": data_status_out,
        "weeklyKondratieff": {
            "date": date_str,
            "aiDiffusionIndex": weekly_adi,
            "constraintIndex": weekly_ci,
            "phase": "transition",
            "strategy": f"Regime {reg_label}; " + "; ".join(drivers[:3]) + ("; " + chain_reason if chain_reason else ""),
            "components": {"soxRatio": 1.0, "nvdaRatio": 1.0, "utilityRatio": 1.0, "copperMomentum": 0.0, "energyPrice": 0.0, **wc},
            "chainInputMissing": chain_reason,
        },
        "technicalData": tech_by_id,
        "priceHistory": {},
    }
