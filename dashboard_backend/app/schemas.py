from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class DashboardPayload(BaseModel):
    """Minimal validation for the dashboard payload.

    We allow extra fields to keep the backend compatible with future expansions.
    """

    model_config = ConfigDict(extra="allow")

    dailySignal: Dict[str, Any]
    macroSwitches: List[Dict[str, Any]]
    assets: List[Dict[str, Any]]
    assetSignals: List[Dict[str, Any]]

    weeklyKondratieff: Optional[Dict[str, Any]] = None
    technicalData: Optional[Dict[str, Any]] = None
    priceHistory: Optional[Dict[str, Any]] = None
