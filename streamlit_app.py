"""
Streamlit 版仪表盘：读取 dashboard.json 展示 Regime、宏观、资产与信号。
本地运行: streamlit run streamlit_app.py
云部署: 推送到 GitHub 后在 share.streamlit.io 新建 App，Main file 填 streamlit_app.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

# 默认 JSON 路径（相对仓库根）
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
    st.caption("基于康波周期框架 · 数据来自 dashboard.json")

    data = load_dashboard()
    if not data:
        st.warning("未找到 dashboard.json。")
        st.info(
            "**云部署时**：在 App 的 Secrets 里配置 `DASHBOARD_JSON_URL` = 你的 dashboard JSON 地址（如后端 `https://xxx/api/dashboard`），"
            "或在本仓库中提交一份 `dashboard_frontend/app/public/data/dashboard.json`。"
        )
        return

    daily = data.get("dailySignal") or {}
    macros = data.get("macroSwitches") or []
    assets = data.get("assets") or []
    signals = data.get("assetSignals") or []

    # 当日信号
    st.header("当日信号")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("日期", daily.get("date", "-"))
    c2.metric("Regime", daily.get("regime", "-"))
    c3.metric("RiskScore", daily.get("riskScore", "-"))
    c4.metric("组合建议", daily.get("portfolioAction", "-"))
    st.write("**驱动因素:**", ", ".join(daily.get("drivers") or []))
    st.caption(daily.get("dataAsOf", ""))

    # 宏观
    st.header("宏观指标")
    n = len(macros)
    cols = st.columns(min(n, 5))
    for i, m in enumerate(macros):
        col = cols[i % len(cols)]
        val = m.get("currentValue")
        ch = m.get("change1m")
        delta = f"{ch:+.2f}" if ch is not None and val is not None else None
        col.metric(m.get("name", m.get("id")), f"{val}" if val is not None else "-", delta=delta)

    # 资产与信号
    st.header("资产与信号")
    if assets:
        import pandas as pd
        rows = []
        for a in assets:
            sig = next((s for s in signals if s.get("assetId") == a.get("id")), {})
            rows.append({
                "资产": a.get("name"),
                "ticker": a.get("ticker"),
                "价格": a.get("price"),
                "24h%": a.get("priceChange24h"),
                "7d%": a.get("priceChange7d"),
                "30d%": a.get("priceChange30d"),
                "建议上限": a.get("suggestedMaxWeight"),
                "趋势": sig.get("trendLight"),
                "风险": sig.get("riskLight"),
                "催化": sig.get("catalystLight"),
                "操作": sig.get("action"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("暂无资产数据。")

    st.divider()
    st.caption(f"生成时间: {data.get('generatedAt', '-')}")


if __name__ == "__main__":
    main()
