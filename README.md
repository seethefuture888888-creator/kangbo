# Macro x Asset Dashboard (Frontend + Backend)

This bundle contains:

- `dashboard_frontend/` – Vite + React UI (reads `/data/dashboard.json` by default)
- `dashboard_backend/` – FastAPI backend (serves `/api/dashboard` and `/data/dashboard.json`)

## How data flows

Your agent generates a single JSON payload (DashboardPayload) and writes it to:

- `dashboard_frontend/app/public/data/dashboard.json`

The frontend automatically reads it from `/data/dashboard.json`. The backend can also serve the same file.

## Quick start (local dev)

### 1) Run frontend

```bash
cd dashboard_frontend/app
npm install
npm run dev
```

### 2) Run backend

```bash
cd ../../dashboard_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Now:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000` (`/api/health`, `/api/dashboard`, `/data/dashboard.json`)

## Option A: Point frontend to backend API

Create `dashboard_frontend/app/.env.local`:

```bash
VITE_DASHBOARD_URL=http://localhost:8000/api/dashboard
```

Restart `npm run dev`.

## Option B: Docker

```bash
docker compose up --build
```

Backend will be at `http://localhost:8000`.

---

## Data pipeline (真实数据驱动)

仪表盘可从 **mock/静态数据** 升级为 **真实数据驱动**。每天运行一次数据管道，生成 `dashboard.json` 写入 `dashboard_frontend/app/public/data/dashboard.json`，前端会自动读取 `/data/dashboard.json`。

### 管道组成

- **宏观**: FRED（HY 利差、10Y 实际利率、核心 CPI）+ DXY 代理（yfinance `DX-Y.NYB`）
- **PMI**: 可插拔接口，默认本地缓存/手工；ISM 发布日抓取留 TODO
- **行情**: yfinance 拉 BTC、美股、港股、黄金白银铜；可选 ccxt 拉 BTC 更高频
- **规则**: RiskScore(0–100)、Regime(A/B/C/D)、资产三灯（Trend/Risk/Catalyst）、suggestedMaxWeight、action(ADD/REDUCE/HOLD)
- **输出**: 原子写入（先写 `.tmp` 再 replace），避免前端读到半截文件

### 运行数据管道

1. 安装依赖（建议独立 venv）：

```bash
cd <repo_root>
python -m venv .venv-data
.venv-data\Scripts\activate   # Windows
# source .venv-data/bin/activate   # Linux/macOS
pip install -r requirements-data.txt
```

2. 配置环境变量（复制并编辑）：

```bash
copy .env.example .env
# 填写 FRED_API_KEY（见 https://fred.stlouisfed.org/docs/api/api_key.html）
```

3. 生成 dashboard.json：

```bash
python tools/generate_dashboard_json.py --output dashboard_frontend/app/public/data/dashboard.json
```

默认 `--output` 即为 `dashboard_frontend/app/public/data/dashboard.json`（相对仓库根目录）。

### 验收标准

1. **运行成功并生成 JSON**  
   `python tools/generate_dashboard_json.py --output ../dashboard_frontend/app/public/data/dashboard.json` 在仓库根目录下执行成功，并在目标路径生成 `dashboard.json`。

2. **JSON 内容**  
   生成文件内需包含：`regime`、`riskScore`、`drivers`、`macroSwitches`、`assetSignals`（含三灯与 `action`）。

3. **前端显示真实数据**  
   前端刷新页面后，能显示真实数据（至少价格与日期会随管道运行而变化）。

若某数据源不可用：允许 fallback 使用最近一次缓存并标注 `freshness_days`；允许用替代指标（如 PMI 用 “Manufacturers’ New Orders” 等代理），但需在输出 `driver`/`reasonCodes` 中注明替代来源。
