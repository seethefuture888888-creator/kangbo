"""
Streamlit dashboard: read dashboard.json and render Daily / Asset / Weekly views.
Run locally: streamlit run streamlit_app.py
Deploy: set DASHBOARD_JSON_URL in Streamlit Secrets, or commit dashboard.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

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
    data_status = data.get("dataStatus") or {}

    st.header("Daily Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date", daily.get("date", "-"))
    c2.metric("Regime", daily.get("regime", "-"))
    c3.metric("RiskScore", daily.get("riskScore", "-"))
    c4.metric("Portfolio Action", daily.get("portfolioAction", "-"))
    st.write("**Drivers:**", ", ".join(daily.get("drivers") or []))
    st.write("**Risk Mode:**", daily.get("riskMode", "-"))
    st.caption(daily.get("dataAsOf", ""))

    st.header("Macro Switches")
    if macros:
        import pandas as pd
        macro_rows = []
        for m in macros:
            mid = m.get("id")
            stat = macro_status.get(mid, {})
            macro_rows.append({
                "Indicator": m.get("name", mid),
                "Value": m.get("currentValue"),
                "Change 7d": m.get("change7d"),
                "Change 1m": m.get("change1m"),
                "Percentile": m.get("percentile"),
                "Light": m.get("light"),
                "Freshness(days)": m.get("freshness"),
                "Status OK": stat.get("ok"),
            })
        st.dataframe(pd.DataFrame(macro_rows), use_container_width=True, hide_index=True)
    else:
        st.write("No macro data.")

    st.header("Assets & Signals")
    if assets:
        import pandas as pd
        rows = []
        for a in assets:
            sig = next((s for s in signals if s.get("assetId") == a.get("id")), {})
            st_meta = data_status.get(a.get("ticker"), {})
            rows.append({
                "Asset": a.get("name"),
                "Ticker": a.get("ticker"),
                "Price": a.get("price"),
                "24h%": a.get("priceChange24h"),
                "7d%": a.get("priceChange7d"),
                "30d%": a.get("priceChange30d"),
                "Max Weight": a.get("suggestedMaxWeight"),
                "Trend": sig.get("trendLight"),
                "Risk": sig.get("riskLight"),
                "Catalyst": sig.get("catalystLight"),
                "Action": sig.get("action"),
                "Reason": ", ".join(sig.get("reasonCodes") or []),
                "Data Provider": st_meta.get("provider"),
                "Data Freshness": st_meta.get("freshness_days"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("No asset data.")

    st.header("Portfolio Summary")
    if assets:
        current_total = sum((a.get("currentWeight") or 0) for a in assets)
        max_total = sum((a.get("suggestedMaxWeight") or 0) for a in assets)
        st.metric("Current Total Weight", round(current_total, 4))
        st.metric("Suggested Total Max", round(max_total, 4))
        st.progress(min(1.0, current_total / max_total) if max_total else 0.0)

    st.header("Weekly Kondratieff")
    if weekly:
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
            st.dataframe(
                pd.DataFrame([{"Component": k, "Value": v} for k, v in comps.items()]),
                use_container_width=True,
                hide_index=True,
            )

    st.header("Technical Snapshot")
    if tech:
        import pandas as pd
        tech_rows = []
        for aid, t in tech.items():
            tech_rows.append({
                "AssetId": aid,
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
        st.dataframe(pd.DataFrame(tech_rows), use_container_width=True, hide_index=True)

    st.divider()
    st.caption(f"Generated at: {data.get('generatedAt', '-')}")


if __name__ == "__main__":
    main()
