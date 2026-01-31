# Dashboard Backend (FastAPI)

A minimal backend to serve your agent-generated `dashboard.json` to the frontend.

## Endpoints

- `GET /api/health` – health check and active `dashboard.json` path
- `GET /api/dashboard` – returns the full dashboard payload JSON
- `GET /data/dashboard.json` – serves the JSON file (compatible with the frontend default)

Optionally, the backend can serve the built frontend (Vite `dist`) when `SERVE_FRONTEND=true`.

## Run locally

```bash
cd dashboard_backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Default tries: ../dashboard_frontend/app/public/data/dashboard.json
uvicorn app.main:app --reload --port 8000
```

## Environment variables

- `DASHBOARD_JSON_PATH` (optional): path to dashboard.json
- `SERVE_FRONTEND` (optional): true/false
- `FRONTEND_DIST_DIR` (optional): path to frontend dist (default: ../dashboard_frontend/app/dist)
- `CORS_ALLOW_ORIGINS` (optional): comma-separated, default: http://localhost:5173

## Production (serve frontend from backend)

1) Build frontend:

```bash
cd ../dashboard_frontend/app
npm install
npm run build
```

2) Start backend:

```bash
cd ../../dashboard_backend
SERVE_FRONTEND=true uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Now open `http://localhost:8000`.
