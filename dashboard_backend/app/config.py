from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Backend configuration."""

    # Path to agent-generated dashboard payload JSON
    dashboard_json_path: Path

    # Serve built frontend (dist) from backend
    serve_frontend: bool
    frontend_dist_dir: Path

    # CORS allowed origins (comma-separated)
    cors_allow_origins: list[str]


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    """Load settings from environment.

    Environment variables:
      - DASHBOARD_JSON_PATH: absolute or relative path to dashboard.json
      - SERVE_FRONTEND: true/false, whether to serve frontend dist
      - FRONTEND_DIST_DIR: path to the built frontend (default: ../dashboard_frontend/app/dist)
      - CORS_ALLOW_ORIGINS: comma-separated list, default: http://localhost:5173
    """

    default_dashboard_paths = [
        Path(os.getenv("DASHBOARD_JSON_PATH", "")) if os.getenv("DASHBOARD_JSON_PATH") else None,
        Path("../dashboard_frontend/app/public/data/dashboard.json"),
        Path("./data/dashboard.json"),
    ]

    dashboard_json_path = None
    env_path = os.getenv("DASHBOARD_JSON_PATH")
    if env_path:
        dashboard_json_path = Path(env_path).resolve()
    if dashboard_json_path is None:
        for p in default_dashboard_paths:
            if not p:
                continue
            cand = p.resolve()
            if cand.parent.exists() or cand.exists():
                dashboard_json_path = cand
                break
    if dashboard_json_path is None:
        p = Path("../dashboard_frontend/app/public/data/dashboard.json").resolve()
        dashboard_json_path = p

    serve_frontend = _bool_env("SERVE_FRONTEND", False)

    default_dist = Path(os.getenv("FRONTEND_DIST_DIR", "../dashboard_frontend/app/dist"))
    frontend_dist_dir = default_dist.resolve()

    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173")
    cors_allow_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

    return Settings(
        dashboard_json_path=dashboard_json_path,
        serve_frontend=serve_frontend,
        frontend_dist_dir=frontend_dist_dir,
        cors_allow_origins=cors_allow_origins,
    )
