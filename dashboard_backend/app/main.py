from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import load_settings
from .schemas import DashboardPayload
from .jobs.scheduler import start_scheduler, shutdown_scheduler, build_dashboard_job

settings = load_settings()

app = FastAPI(
    title="Macro x Asset Dashboard Backend",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    shutdown_scheduler()

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_dashboard_json(path: Path) -> Dict[str, Any]:
    try:
        txt = path.read_text(encoding="utf-8")
        data = json.loads(txt)
        # Light validation
        DashboardPayload.model_validate(data)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"dashboard.json not found at {path}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "dashboard_json_path": str(settings.dashboard_json_path),
    }


@app.get("/api/dashboard")
def get_dashboard():
    data = _read_dashboard_json(settings.dashboard_json_path)
    return JSONResponse(content=data)


@app.get("/api/dashboard/live")
def get_dashboard_live():
    """立即重新生成 dashboard 并返回最新 JSON，用于「打开时立即更新」."""
    try:
        build_dashboard_job()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generate failed: {e}")
    data = _read_dashboard_json(settings.dashboard_json_path)
    return JSONResponse(content=data)


# Compatibility route: serve the JSON at /data/dashboard.json
@app.get("/data/dashboard.json")
def get_dashboard_json_file():
    if not settings.dashboard_json_path.exists():
        raise HTTPException(status_code=404, detail=f"dashboard.json not found at {settings.dashboard_json_path}")
    return FileResponse(
        path=str(settings.dashboard_json_path),
        media_type="application/json",
        filename="dashboard.json",
    )


# Optionally mount the parent directory as /data for other artifacts (e.g., price histories)
try:
    data_dir = settings.dashboard_json_path.parent
    if data_dir.exists():
        app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")
except Exception:
    pass


# Optional: serve built frontend (dist) from backend
if settings.serve_frontend and settings.frontend_dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(settings.frontend_dist_dir), html=True), name="frontend")
