#!/usr/bin/env python3
"""
Generate dashboard.json from live/cached data.
Usage: python tools/generate_dashboard_json.py [--output <path>]
Default output: ../dashboard_frontend/app/public/data/dashboard.json (relative to repo root).
Atomic write: write to .tmp then replace.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Repo root = parent of tools/
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Load env before imports that use it
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.local")

from src.providers.fred_provider import (
    FRED_SERIES,
    get_latest_and_changes,
    get_core_cpi_yoy,
    get_pmi_from_amtmno,
    get_dxy_from_fred,
)
from src.providers.yfinance_provider import fetch_ohlcv
from src.providers.pmi_provider import get_pmi
from src.providers.price_provider import download_price_map
from src.export_json import build_payload, ASSET_DEFS
from src import features


DEFAULT_OUTPUT = REPO_ROOT / "dashboard_frontend" / "app" / "public" / "data" / "dashboard.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate dashboard.json")
    ap.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path")
    args = ap.parse_args()
    out_path = args.output.resolve()

    def log(msg: str) -> None:
        print(msg, file=sys.stderr, flush=True)

    log("数据管道启动...")
    fred_key = os.environ.get("FRED_API_KEY")

    # 1) Macro: FRED (HY, 10Y real); Core CPI as YoY %; DXY from FRED DTWEXBGS, yf fallback
    log("拉取 FRED 宏观数据...")
    hy = get_latest_and_changes(FRED_SERIES["HY_OAS"])
    real10y = get_latest_and_changes(FRED_SERIES["REAL10Y"])
    core_cpi = get_core_cpi_yoy(fred_key)
    if not hy.get("value"):
        hy = hy or {}
        hy.setdefault("value", 4.5)
        hy.setdefault("change7d", 0)
        hy.setdefault("change1m", -0.2)
        hy.setdefault("freshness_days", 999)
    if not real10y.get("value"):
        real10y = real10y or {}
        real10y.setdefault("value", 1.5)
        real10y.setdefault("change7d", 0)
        real10y.setdefault("change1m", -0.1)
        real10y.setdefault("freshness_days", 999)
    if core_cpi.get("value") is None:
        core_cpi.setdefault("value", 3.2)
        core_cpi.setdefault("change1m", -0.1)
        core_cpi.setdefault("freshness_days", 999)

    # DXY: primary FRED DTWEXBGS, fallback yfinance DX-Y.NYB
    dxy = get_dxy_from_fred(fred_key)
    dxy["price"] = dxy.get("value")
    dxy.setdefault("change7d", dxy.get("change7d"))
    dxy.setdefault("change30d", dxy.get("change1m"))

    log("拉取行情数据 (多级降级: yfinance→stooq→marketwatch→twelvedata→binance)...")
    ohlcv, data_status = download_price_map(days=400, fred_api_key=fred_key)

    # DXY fallback from yfinance if FRED had no value
    if dxy.get("price") is None:
        dxy_series = ohlcv.get("DX-Y.NYB") or []
        if dxy_series:
            dxy_series = sorted(dxy_series, key=lambda x: x["date"])
            dxy["price"] = dxy_series[-1]["close"]
            for r in reversed(dxy_series[:-1]):
                days_ago = __date_diff(dxy_series[-1]["date"], r["date"])
                pct = (dxy["price"] - r["close"]) / r["close"] * 100 if r["close"] else None
                if pct is not None:
                    if dxy.get("change7d") is None and days_ago >= 5:
                        dxy["change7d"] = pct
                    if dxy.get("change30d") is None and days_ago >= 25:
                        dxy["change30d"] = pct
                if dxy.get("change7d") is not None and dxy.get("change30d") is not None:
                    break
        dxy.setdefault("freshness_days", 1 if dxy.get("price") else 999)

    # 2) PMI: FRED AMTMNO → PMI-like (API then CSV fallback); adaptive window; fallback 50 + PMI_FALLBACK
    log("读取 PMI (New Orders 代理)...")
    pmi = get_pmi_from_amtmno(fred_key)
    if pmi.get("value") is None:
        pmi = get_pmi()
        if pmi.get("value") is None:
            pmi = {"value": 50.0, "change7d": None, "change1m": None, "freshness_days": 999, "reason": "PMI_FALLBACK"}

    # 3) Technical features per asset
    log("计算技术指标...")
    tech_by_id = {}
    for defn in ASSET_DEFS:
        aid = defn["id"]
        ticker = defn["ticker"]
        series = ohlcv.get(ticker) or []
        if not series:
            tech_by_id[aid] = {"assetId": aid, "ma20": 0, "ma60": 0, "ma200": 0, "mom12w": 0, "rsToBenchmark": 1, "vol20Ann": 0, "mdd60": 0, "mdd120": 0, "volPercentile1y": 50, "ddPercentile1y": 50, "correlationDXY": 0, "correlationRealRate": 0, "correlationSPX": 0}
            continue
        tech = features.compute_all(series)
        tech["assetId"] = aid
        tech_by_id[aid] = tech

    # 4) Weekly Kondratieff: COPPER=CPER, OIL=USO
    weekly_components = __compute_weekly_chain(ohlcv)

    # 5) Build payload (dataStatus + no 0 for missing price)
    log("生成 dashboard 数据...")
    payload = build_payload(hy, real10y, dxy, pmi, core_cpi, ohlcv, tech_by_id, weekly_components=weekly_components, data_status=data_status)

    # 6) Atomic write (fallback on Windows when target is open)
    log("写入 JSON...")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    try:
        os.replace(tmp_path, out_path)
    except (OSError, PermissionError) as e:
        if getattr(e, "winerror", None) == 5:  # WinError 5 = 拒绝访问（文件被占用）
            try:
                content = tmp_path.read_text(encoding="utf-8")
                out_path.write_text(content, encoding="utf-8")
                tmp_path.unlink(missing_ok=True)
            except Exception:
                print("无法覆盖目标文件：请关闭正在使用 dashboard.json 的程序（前端开发服务器、浏览器或编辑器）后重试。", file=sys.stderr)
                return 1
        else:
            raise
    log(f"完成: {out_path}")
    return 0


def __date_diff(end: str, start: str) -> int:
    from datetime import datetime
    e = datetime.strptime(end, "%Y-%m-%d")
    s = datetime.strptime(start, "%Y-%m-%d")
    return (e - s).days


def __compute_weekly_chain(ohlcv: dict) -> dict:
    """WEEKLY_TICKERS: COPPER=CPER, OIL=USO. Returns components.copperMomentum, energyPrice."""
    copper_series = ohlcv.get("CPER") or ohlcv.get("HG=F") or []
    oil_series = ohlcv.get("USO") or []
    copper_series = sorted(copper_series, key=lambda x: x["date"]) if copper_series else []
    oil_series = sorted(oil_series, key=lambda x: x["date"]) if oil_series else []
    copper_momentum = 0.0
    energy_price = 0.0
    if len(copper_series) >= 25:
        cur = copper_series[-1]["close"]
        prev = copper_series[-25]["close"]
        if prev and prev != 0:
            copper_momentum = round((cur / prev - 1) * 100, 4)
    if oil_series:
        energy_price = round(oil_series[-1]["close"], 2)
    return {"copperMomentum": copper_momentum, "energyPrice": energy_price}


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
