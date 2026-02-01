"""
Streamlit 仪表盘：读取 dashboard.json 并展示 Daily / Asset / Weekly 视图。
本地运行：streamlit run streamlit_app.py
部署：在 Streamlit Secrets 里设置 DASHBOARD_JSON_URL，或提交 dashboard.json。
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
        return "\U0001F7E2 绿"
    if status == "yellow":
        return "\U0001F7E1 黄"
    if status == "red":
        return "\U0001F534 红"
    return "\u26AA 未知"


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
    top = "；".join(drivers[:3]) if drivers else "-"
    action = daily.get("portfolioAction", "-")
    regime = daily.get("regime", "-")
    risk = daily.get("riskScore", "-")
    return f"象限 {regime}，RiskScore {risk}。驱动：{top}。动作：{action}。"


def render_daily(daily: dict, macros: list[dict], macro_status: dict, assets: list[dict], signals: list[dict]) -> None:
    st.header("今日总览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("日期", daily.get("date", "-"))
    c2.metric("Regime", daily.get("regime", "-"))
    c3.metric("RiskScore", daily.get("riskScore", "-"))
    c4.metric("组合动作", daily.get("portfolioAction", "-"))

    st.write("**风险模式：**", daily.get("riskMode", "-"))
    st.write("**主要驱动：**", "，".join(daily.get("drivers") or []))
    if daily.get("commentSummary"):
        st.info(daily.get("commentSummary"))
    st.caption(daily.get("dataAsOf", ""))

    st.subheader("宏观四开关")
    if macros:
        cols = st.columns(min(len(macros), 5))
        for i, m in enumerate(macros):
            col = cols[i % len(cols)]
            mid = m.get("id")
            stat = macro_status.get(mid, {})
            col.markdown(f"**{m.get('name', mid)}**")
            col.write(f"灯号：{light_badge(m.get('light'))}")
            col.write(f"当前值：{fmt_num(m.get('currentValue'))}")
            col.write(f"7日变化：{fmt_num(m.get('change7d'))}")
            col.write(f"1月变化：{fmt_num(m.get('change1m'))}")
            col.write(f"分位：{fmt_num(m.get('percentile'), 1)}")
            col.write(f"新鲜度(天)：{m.get('freshness', '-')}")
            if stat:
                col.write(f"状态OK：{stat.get('ok')}")
    else:
        st.write("暂无宏观数据。")

    st.subheader("仓位建议条")
    current_total = sum((a.get("currentWeight") or 0) for a in assets)
    max_total = sum((a.get("suggestedMaxWeight") or 0) for a in assets)
    st.metric("当前总仓位", round(current_total, 4))
    st.metric("建议上限总和", round(max_total, 4))
    st.progress(min(1.0, current_total / max_total) if max_total else 0.0)
    if max_total:
        gap = max_total - current_total
        if gap > 0:
            st.success(f"可加仓空间：{gap:.2%}")
        else:
            st.warning(f"需要减仓：{abs(gap):.2%}")

    st.subheader("资产热力表")
    if assets:
        import pandas as pd

        rows = []
        for a in assets:
            sig = next((s for s in signals if s.get("assetId") == a.get("id")), {})
            rows.append({
                "资产": a.get("name"),
                "Ticker": a.get("ticker"),
                "趋势": light_badge(sig.get("trendLight")),
                "风险": light_badge(sig.get("riskLight")),
                "催化": light_badge(sig.get("catalystLight")),
                "建议上限": a.get("suggestedMaxWeight"),
                "动作": sig.get("action"),
                "备注": sig.get("notes"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("暂无资产数据。")

    st.subheader("每日一句话")
    st.write(daily_narrative(daily, assets, signals))


def render_asset_detail(assets: list[dict], signals: list[dict], tech: dict, price_history: dict) -> None:
    st.header("资产详情（全部资产）")
    if not assets:
        st.write("暂无资产数据。")
        return

    st.caption("本页展示全部资产，无需下拉选择。可按需勾选显示的指标模块。")
    c1, c2, c3, c4 = st.columns(4)
    show_price = c1.checkbox("显示价格走势", value=True)
    show_tech = c2.checkbox("显示技术指标", value=True)
    show_corr = c3.checkbox("显示相关性", value=True)
    show_action = c4.checkbox("显示动作与原因", value=True)

    for idx, asset in enumerate(assets):
        aid = asset.get("id")
        signal = next((s for s in signals if s.get("assetId") == aid), {})
        t = tech.get(aid, {})
        series = price_history.get(aid, []) if price_history else []

        with st.expander(f"{asset.get('name', aid)}（{asset.get('ticker', '-') }）", expanded=(idx == 0)):
            c1, c2, c3 = st.columns(3)
            c1.metric("资产", asset.get("name", "-"))
            c2.metric("Ticker", asset.get("ticker", "-"))
            c3.metric("价格", fmt_num(asset.get("price")))

            st.subheader("三灯")
            c1, c2, c3 = st.columns(3)
            c1.write(f"趋势：{light_badge(signal.get('trendLight'))}")
            c2.write(f"风险：{light_badge(signal.get('riskLight'))}")
            c3.write(f"催化：{light_badge(signal.get('catalystLight'))}")

            if show_tech:
                st.subheader("技术指标")
                if t:
                    tech_block = {
                        "MA20": t.get("ma20"),
                        "MA60": t.get("ma60"),
                        "MA200": t.get("ma200"),
                        "12周动量": t.get("mom12w"),
                        "20日年化波动": t.get("vol20Ann"),
                        "60日最大回撤": t.get("mdd60"),
                        "120日最大回撤": t.get("mdd120"),
                        "波动分位(1年)": t.get("volPercentile1y"),
                        "回撤分位(1年)": t.get("ddPercentile1y"),
                        "相对强弱": t.get("rsToBenchmark"),
                    }
                    if show_corr:
                        tech_block.update({
                            "相关性DXY": t.get("correlationDXY"),
                            "相关性实际利率": t.get("correlationRealRate"),
                            "相关性SPX": t.get("correlationSPX"),
                        })
                    st.write(tech_block)
                else:
                    st.write("暂无技术指标数据。")

            if show_price:
                st.subheader("价格走势")
                if series:
                    import pandas as pd

                    df = pd.DataFrame(series)
                    if "date" in df.columns and "close" in df.columns:
                        df = df.sort_values("date")
                        st.line_chart(df.set_index("date")["close"])
                    else:
                        st.write("价格历史格式不支持。")
                else:
                    st.info("dashboard.json 未提供价格历史。")

            if show_action:
                st.subheader("动作与原因")
                st.write(f"动作：{signal.get('action', '-')}")
                st.write(f"建议上限：{signal.get('suggestedMaxWeight', '-')}")
                if signal.get("reasonCodes"):
                    st.write("原因：", "，".join(signal.get("reasonCodes")))
                if signal.get("notes"):
                    st.write("备注：", signal.get("notes"))


def render_weekly(weekly: dict) -> None:
    st.header("Weekly 康波链条")
    if not weekly:
        st.write("暂无周度数据。")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("日期", weekly.get("date", "-"))
    c2.metric("AI扩散指数", weekly.get("aiDiffusionIndex", "-"))
    c3.metric("资源约束指数", weekly.get("constraintIndex", "-"))
    c4.metric("阶段", weekly.get("phase", "-"))

    st.write("**策略：**", weekly.get("strategy", "-"))
    if weekly.get("chainInputMissing"):
        st.warning(f"链条输入缺失：{weekly.get('chainInputMissing')}")

    comps = weekly.get("components") or {}
    if comps:
        import pandas as pd

        comp_df = pd.DataFrame([{"组件": k, "数值": v} for k, v in comps.items()])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        comp_chart = pd.DataFrame(
            {
                "名称": ["ADI", "CI"],
                "数值": [weekly.get("aiDiffusionIndex"), weekly.get("constraintIndex")],
            }
        )
        st.bar_chart(comp_chart.set_index("名称"))


def main() -> None:
    st.set_page_config(page_title="Investment Decision Dashboard", layout="wide")
    st.title("Investment Decision Dashboard")
    st.caption("数据来源：dashboard.json")

    data = load_dashboard()
    if not data:
        st.warning("找不到 dashboard.json。")
        st.info(
            "请在 Streamlit Secrets 中设置 `DASHBOARD_JSON_URL` 指向后端 JSON，"
            "或在仓库提交 `dashboard_frontend/app/public/data/dashboard.json`。"
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

    page = st.sidebar.radio("视图", ["今日总览", "资产详情", "Weekly 康波"])
    if page == "今日总览":
        render_daily(daily, macros, macro_status, assets, signals)
    elif page == "资产详情":
        render_asset_detail(assets, signals, tech, price_history)
    else:
        render_weekly(weekly)

    st.divider()
    st.caption(f"生成时间：{data.get('generatedAt', '-')}")


if __name__ == "__main__":
    main()
