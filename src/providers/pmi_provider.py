"""
PMI provider: pluggable interface.
Default: fallback from local cache / manual value.
TODO: On ISM release days, optionally scrape ISM Manufacturing PMI (not blocking).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Optional: cache file for manual/third-party PMI
PMI_CACHE_FILE = os.environ.get("PMI_CACHE_FILE") or str(
    Path(__file__).resolve().parents[2] / "data" / "pmi_cache.json"
)


def get_pmi() -> dict[str, Any]:
    """
    Return PMI data: value, change7d, change1m, freshness_days, source.
    Default: read from cache or use fallback constant; source/reasonCodes should note "manual/cache" or "proxy".
    """
    import json
    cache_path = Path(PMI_CACHE_FILE)
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return {
                "value": data.get("value"),
                "change7d": data.get("change7d"),
                "change1m": data.get("change1m"),
                "freshness_days": data.get("freshness_days"),
                "source": "cache",
                "reason": "PMI from local cache",
            }
        except Exception:
            pass
    # Fallback: no PMI API by default; driver/reasonCodes will note "PMI_MANUAL" or use proxy
    return {
        "value": None,
        "change7d": None,
        "change1m": None,
        "freshness_days": None,
        "source": "fallback",
        "reason": "PMI_MANUAL: use cache or third-party; ISM scrape TODO",
    }


# TODO: On ISM release day, scrape ISM Manufacturing PMI from official/trusted source
# def fetch_ism_pmi() -> dict[str, Any]: ...
