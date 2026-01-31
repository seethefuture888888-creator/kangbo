"""
APScheduler: every 60 min run build_dashboard_job().
build_dashboard_job() calls builder.build_payload() then write to DASHBOARD_JSON_PATH.
"""
from __future__ import annotations

from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from ..config import load_settings
from ..compute.builder import build_payload
from ..io.write_json import write_dashboard_json

_scheduler: BackgroundScheduler | None = None


def build_dashboard_job() -> None:
    settings = load_settings()
    path = settings.dashboard_json_path
    try:
        payload = build_payload()
        write_dashboard_json(path, payload)
    except Exception:
        pass


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(build_dashboard_job, "interval", minutes=60, id="build_dashboard")
    _scheduler.start()
    build_dashboard_job()


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
