"""
Atomic write: write to xxx.tmp then replace to dashboard.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_dashboard_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
