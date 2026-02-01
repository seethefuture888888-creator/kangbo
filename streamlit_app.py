"""
Streamlit dashboard: read dashboard.json and render Daily / Asset / Weekly views.
Run locally: streamlit run streamlit_app.py
Deploy: set DASHBOARD_JSON_URL in Streamlit Secrets, or commit dashboard.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

DEFAULT_JSON = Path(__file__).resolve().parent / "dashboard_frontend" / "app" / "public" / "data" / "dashboard.json"


def load_dashboard_from_url(url: str) -> dict | None:
    try:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def load_dashboard(path: Path | None = None) -> dict | None:
    url = os.environ.get("DASHBOARD_JSON_URL")
    if url:
        return load_dashboard_from_url(url)
    path = path or DEFAULT_JSON
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def light_badge(status: str | None) -> str:
    if status == "green":
        return "\U0001F7E2 Green"
    if status == "yellow":
        return "\U0001F7E1 Yellow"
    if status == "red":
        return "\U0001F534 Red"
    return "\u26AA Unknown"


def fmt_num(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:,.{digits}f}"
    return str(value)


def fmt_pct(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:+.{digits}f}%"
    return str(value)


def daily_narrative(daily: dict, assets: list[dict], signals: list[dict]) -> str:
    drivers = daily.get("drivers") or []
    top = "; ".join(drivers[:3]) if drivers else "-"
    action = daily.get("portfolioAction", "-")
    regime = daily.get("regime", "-")
    risk = daily.get("riskScore", "-")
    return f"Regime {regime}, RiskScore {risk}. Drivers: {top}. Action: {action}."


def render_daily(daily: dict, macros: list[dict], macro_status: dict, assets: list[dict], signals: list[dict]) -> None:
    st.header("Daily Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date", daily.get("date", "-"))
    c2.metric("Regime", daily.get("regime", "-"))
    c3.metric("RiskScore", daily.get("riskScore", "-"))
    c4.metric("Portfolio Action", daily.get("portfolioAction", "-"))

    st.write("**Risk Mode:**", daily.get("riskMode", "-"))
    st.write("**Drivers:**", ", ".join(daily.get("drivers") or []))
    if daily.get("commentSummary"):
        st.info(daily.get("commentSummary"))
    st.caption(daily.get("dataAsOf", ""))

    st.subheader("Macro Switches")
    if macros:
        cols = st.columns(min(len(macros), 5))
        for i, m in enumerate(macros):
            col = cols[i % len(cols)]
            mid = m.get("id")
            stat = macro_status.get(mid, {})
            col.markdown(f"**{m.get('name', mid)}**")
            col.write(f"Light: {light_badge(m.get('light'))}")
            col.write(f"Value: {fmt_num(m.get('currentValue'))}")
            col.write(f"Change 7d: {fmt_num(m.get('change7d'))}")
            col.write(f"Change 1m: {fmt_num(m.get('change1m'))}")
            col.write(f"Percentile: {fmt_num(m.get('percentile'), 1)}")
            col.write(f"Freshness(days): {m.get('freshness', '-')}")
            if stat:
                col.write(f"Status OK: {stat.get('ok')}")
    else:
        st.write("No macro data.")

    st.subheader("Portfolio Bar")
    current_total = sum((a.get("currentWeight") or 0) for a in assets)
    max_total = sum((a.get("suggestedMaxWeight") or 0) for a in assets)
    st.metric("Current Total Weight", round(current_total, 4))
    st.metric("Suggested Total Max", round(max_total, 4))
    st.progress(min(1.0, current_total / max_total) if max_total else 0.0)
    if max_total:
        gap = max_total - current_total
        if gap > 0:
            st.success(f"Add capacity: {gap:.2%}")
        else:
            st.warning(f"Reduce needed: {abs(gap):.2%}")

    st.subheader("Asset Heatmap")
    if assets:
        import pandas as pd

        rows = []
        for a in assets:
            sig = next((s for s in signals if s.get("assetId") == a.get("id")), {})
            rows.append({
                "Asset": a.get("name"),
                "Ticker": a.get("ticker"),
                "Trend": light_badge(sig.get("trendLight")),
                "Risk": light_badge(sig.get("riskLight")),
                "Catalyst": light_badge(sig.get("catalystLight")),
                "Max Weight": a.get("suggestedMaxWeight"),
                "Action": sig.get("action"),
                "Notes": sig.get("notes"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("No asset data.")

    st.subheader("Daily Narrative")
    st.write(daily_narrative(daily, assets, signals))


def render_asset_detail(assets: list[dict], signals: list[dict], tech: dict, price_history: dict) -> None:
    st.header("Asset Detail")
    if not assets:
        st.write("No asset data.")
        return

    asset_map = {a.get("id"): a for a in assets}
    choices = [a.get("id") for a in assets if a.get("id")]
    selected = st.selectbox("Select Asset", choices, index=0)
    asset = asset_map.get(selected, {})
    signal = next((s for s in signals if s.get("assetId") == selected), {})
    t = tech.get(selected, {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Asset", asset.get("name", "-"))
    c2.metric("Ticker", asset.get("ticker", "-"))
    c3.metric("Price", fmt_num(asset.get("price")))

    st.subheader("Three Lights")
    c1, c2, c3 = st.columns(3)
    c1.write(f"Trend: {light_badge(signal.get('trendLight'))}")
    c2.write(f"Risk: {light_badge(signal.get('riskLight'))}")
    c3.write(f"Catalyst: {light_badge(signal.get('catalystLight'))}")

    st.subheader("Technical Snapshot")
    if t:
        st.write({
            "MA20": t.get("ma20"),
            "MA60": t.get("ma60"),
            "MA200": t.get("ma200"),
            "Mom12w": t.get("mom12w"),
            "Vol20Ann": t.get("vol20Ann"),
            "MDD60": t.get("mdd60"),
            "MDD120": t.get("mdd120"),
            "VolPct1y": t.get("volPercentile1y"),
            "DDPct1y": t.get("ddPercentile1y"),
            "RS": t.get("rsToBenchmark"),
            "CorrDXY": t.get("correlationDXY"),
            "CorrRealRate": t.get("correlationRealRate"),
            "CorrSPX": t.get("correlationSPX"),
        })
    else:
        st.write("No technical data.")

    st.subheader("Price History")
    series = price_history.get(selected, []) if price_history else []
    if series:
        import pandas as pd

        df = pd.DataFrame(series)
        if "date" in df.columns and "close" in df.columns:
            df = df.sort_values("date")
            st.line_chart(df.set_index("date")["close"])
        else:
            st.write("Price history format not supported.")
    else:
        st.info("No price history available in dashboard.json.")

    st.subheader("Action & Reasons")
    st.write(f"Action: {signal.get('action', '-')}")
    st.write(f"Suggested Max Weight: {signal.get('suggestedMaxWeight', '-')}")
    if signal.get("reasonCodes"):
        st.write("Reasons:", ", ".join(signal.get("reasonCodes")))
    if signal.get("notes"):
        st.write("Notes:", signal.get("notes"))


def render_weekly(weekly: dict) -> None:
    st.header("Weekly Kondratieff")
    if not weekly:
        st.write("No weekly data.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date", weekly.get("date", "-"))
    c2.metric("ADI", weekly.get("aiDiffusionIndex", "-"))
    c3.metric("CI", weekly.get("constraintIndex", "-"))
    c4.metric("Phase", weekly.get("phase", "-"))

    st.write("**Strategy:**", weekly.get("strategy", "-"))
    if weekly.get("chainInputMissing"):
        st.warning(f"Chain input missing: {weekly.get('chainInputMissing')}")

    comps = weekly.get("components") or {}
    if comps:
        import pandas as pd

        comp_df = pd.DataFrame([{"Component": k, "Value": v} for k, v in comps.items()])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        comp_chart = pd.DataFrame(
            {
                "name": ["ADI", "CI"],
                "value": [weekly.get("aiDiffusionIndex"), weekly.get("constraintIndex")],
            }
        )
        st.bar_chart(comp_chart.set_index("name"))


def main() -> None:
    st.set_page_config(page_title="Investment Decision Dashboard", layout="wide")
    st.title("Investment Decision Dashboard")
    st.caption("Data source: dashboard.json")

    data = load_dashboard()
    if not data:
        st.warning("dashboard.json not found.")
        st.info(
            "Set `DASHBOARD_JSON_URL` in Streamlit Secrets to your backend JSON endpoint, "
            "or commit `dashboard_frontend/app/public/data/dashboard.json` to the repo."
        )
        return

    daily = data.get("dailySignal") or {}
    macros = data.get("macroSwitches") or []
    macro_status = data.get("macroDataStatus") or {}
    assets = data.get("assets") or []
    signals = data.get("assetSignals") or []
    weekly = data.get("weeklyKondratieff") or {}
    tech = data.get("technicalData") or {}
    price_history = data.get("priceHistory") or {}

    page = st.sidebar.radio("View", ["Daily", "Asset Detail", "Weekly"])
    if page == "Daily":
        render_daily(daily, macros, macro_status, assets, signals)
    elif page == "Asset Detail":
        render_asset_detail(assets, signals, tech, price_history)
    else:
        render_weekly(weekly)

    st.divider()
    st.caption(f"Generated at: {data.get('generatedAt', '-')}")


if __name__ == "__main__":
    main()
