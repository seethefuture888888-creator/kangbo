#!/usr/bin/env python3
"""
检查 dashboard 数据抓取状态：列出仍拿不到的数据及原因。
用法：python tools/check_data_status.py [dashboard.json 路径]
若不传路径则先运行一次生成再检查。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = REPO_ROOT / "dashboard_frontend" / "app" / "public" / "data" / "dashboard.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    if not path.exists():
        print("未找到 dashboard.json，正在运行一次生成...", file=sys.stderr)
        sys.path.insert(0, str(REPO_ROOT))
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
        load_dotenv(REPO_ROOT / ".env.local")
        from tools.generate_dashboard_json import main as run_gen
        rc = run_gen()
        if rc != 0:
            print("生成失败", file=sys.stderr)
            return rc
        if not path.exists():
            print("生成后仍无文件", file=sys.stderr)
            return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    data_status = data.get("dataStatus") or {}
    macro_status = data.get("macroDataStatus") or {}
    assets = {a["ticker"]: a for a in data.get("assets") or []}

    missing = []
    ok_list = []

    # 行情
    for ticker, st in data_status.items():
        ok = st.get("ok", False)
        provider = st.get("provider", "?")
        row_count = st.get("row_count", 0)
        err = st.get("error_reason")
        note = st.get("note")
        price = (assets.get(ticker) or {}).get("price")
        if not ok or price is None:
            missing.append(("行情", ticker, provider, row_count, err or note or "无数据"))
        else:
            ok_list.append(("行情", ticker, provider, row_count))

    # 宏观
    for mid, st in macro_status.items():
        ok = st.get("ok", False)
        if not ok:
            missing.append(("宏观", mid, st.get("provider", "?"), None, st.get("note") or "missing_observation"))
        else:
            ok_list.append(("宏观", mid, st.get("provider", "?"), None))

    print("=== 已拿到的数据 ===")
    for kind, key, prov, rc in ok_list:
        rc_str = f", row_count={rc}" if rc is not None else ""
        print(f"  {kind} {key}: provider={prov}{rc_str}")
    print()
    print("=== 仍拿不到的数据 ===")
    if not missing:
        print("  无")
        return 0
    for kind, key, prov, rc, reason in missing:
        rc_str = f", row_count={rc}" if rc is not None else ""
        print(f"  {kind} {key}: provider={prov}{rc_str}, reason={reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
