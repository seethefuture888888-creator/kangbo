# 云端部署指南

## 一、部署方式概览

| 方式 | 适用 | 说明 |
|------|------|------|
| **A) 单机 Docker** | 一台云服务器 | 前端 + 后端 + 定时生成 JSON，全部在一台机 |
| **B) 前端静态 + 后端分离** | 省成本 | 前端丢 Vercel/Netlify，后端 + 定时任务放小机或云函数 |
| **C) Streamlit Cloud** | 零服务器 | 用 Streamlit 版仪表盘，部署到 share.streamlit.io |

推荐先用 **A)**，一台 1核2G 云服务器即可跑满。想零服务器可选用 **C)**。

---

## 二、方式 A：单机 Docker 部署（推荐）

### 1. 准备云服务器

- 系统：Linux（Ubuntu 22.04 / Debian 12 等）
- 安装 Docker 与 Docker Compose
- 开放端口：**80**（前端）、**8000**（后端 API，可选）

```bash
# 安装 Docker（Ubuntu 示例）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 安装 Docker Compose 插件
sudo apt-get update && sudo apt-get install -y docker-compose-plugin
```

### 2. 上传代码

把本仓库上传到服务器，例如 `/home/ubuntu/dashboard/`：

- 包含 `docker-compose.yml`、`dashboard_frontend/`、`dashboard_backend/`、`tools/`、`src/` 等

### 3. 配置环境变量

在服务器上创建 `.env`（与 `docker-compose.yml` 同目录）：

```bash
cd /home/ubuntu/dashboard
nano .env
```

写入（按需修改）：

```env
FRED_API_KEY=你的FRED密钥
```

### 4. 首次生成 dashboard.json

在服务器上先跑一次数据管道，生成 `dashboard_frontend/app/public/data/dashboard.json`：

```bash
cd /home/ubuntu/dashboard
python3 -m venv .venv
source .venv/bin/activate   # Windows 用 .venv\Scripts\activate
pip install -r requirements-data.txt
python tools/generate_dashboard_json.py
```

没有 Python 时可用 Docker 跑（需先做一个小镜像或挂载代码进容器），或在本机生成后把 `dashboard.json` 上传到服务器 `dashboard_frontend/app/public/data/`。

### 5. 启动服务

```bash
cd /home/ubuntu/dashboard
docker compose up -d --build
```

- 前端：**http://你的服务器IP**（端口 80）
- 后端：**http://你的服务器IP:8000**（/api/health, /api/dashboard）

### 6. 定时更新数据（每天生成一次 JSON）

在服务器上配置 crontab，每天固定时间跑一次生成脚本，例如每天 8 点：

```bash
crontab -e
```

加入一行（路径按你实际目录改）：

```cron
0 8 * * * cd /home/ubuntu/dashboard && .venv/bin/python tools/generate_dashboard_json.py
```

这样每天会更新 `dashboard.json`，前端刷新即可看到新数据。

---

## 三、方式 B：前端静态托管 + 后端分离

### 前端（Vercel / Netlify）

1. 把仓库推到 GitHub，在 Vercel/Netlify 里导入该仓库。
2. 构建配置：
   - **Root Directory**: `dashboard_frontend/app`
   - **Build Command**: `npm run build`
   - **Output / Publish Directory**: `dist`
3. 部署后前端是静态站，默认读的是构建时打包的 `/data/dashboard.json`，**不会自动更新**。
4. 若要“每天更新数据”，有两种做法：
   - 每天在你本机或一台小机上跑 `python tools/generate_dashboard_json.py`，把生成的 `dashboard.json` 上传到对象存储（如 OSS/S3），前端通过接口或静态 URL 读这个 JSON；或
   - 用 Vercel/Netlify 的 **Scheduled Function** 调你自家的“生成接口”（需要你先在一台服务器上部署后端 + 生成脚本并暴露一个 HTTP 接口）。

### 后端（可选）

- 若希望前端通过 API 拉取最新 JSON，可在云服务器上只跑后端：
  - 只启动 `dashboard_backend` 容器，或单独 `uvicorn` 跑 FastAPI。
  - 前端配置 `VITE_DASHBOARD_URL=http://你的后端域名/api/dashboard`，重新构建并部署前端。

---

## 四、安全检查

- 云服务器防火墙/安全组只开放 **80、443、8000（若需要）**，其余端口不对外开放。
- `.env` 不要提交到 Git，只在服务器本地保留，且 `FRED_API_KEY` 不要写进前端代码。
- 若用 Nginx 做反代，建议给后端加 HTTPS 和简单限流。

---

## 五、方式 C：部署到 Streamlit Cloud

项目里已包含 **Streamlit 版仪表盘**（`streamlit_app.py`），只读同一份 `dashboard.json` 做展示，可部署到 [Streamlit Community Cloud](https://share.streamlit.io)。

### 1. 本地先跑通

```bash
cd 项目根目录
pip install -r requirements-streamlit.txt
# 确保已有 dashboard.json（运行过 generate_dashboard_json.py）
streamlit run streamlit_app.py
```

浏览器会打开 `http://localhost:8501`。

### 2. 部署到 Streamlit Cloud

1. 把本仓库推到 **GitHub**（公开或私有均可，私有需在 Streamlit Cloud 连 GitHub 授权）。
2. 打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登录。
3. 点击 **New app**：
   - **Repository**：选你的仓库（如 `你的用户名/康波周期`）。
   - **Branch**：`main` 或你用的分支。
   - **Main file path**：填 `streamlit_app.py`。
   - **App URL**：可自定义子路径（如 `xxx-dashboard`）。
4. 点击 **Advanced settings**：
   - 如需在云端**自动生成** `dashboard.json`，可把 `requirements-streamlit.txt` 改为依赖 `requirements-data.txt`，并在 `streamlit_app.py` 里增加“一键生成”逻辑（会拉 FRED/yfinance 等）；多数情况下建议**在本地或 cron 生成好 JSON，再提交到仓库**，这样 Streamlit 只做展示、启动快且稳定。
5. **Secrets**（可选）：若在 Streamlit 里跑生成脚本，可在 Secrets 里配置 `FRED_API_KEY`。
6. 部署完成后，打开生成的 URL 即可查看 Streamlit 版仪表盘。

### 3. 数据如何更新

- **方式一**：本地或服务器定时跑 `python tools/generate_dashboard_json.py`，把新生成的 `dashboard_frontend/app/public/data/dashboard.json` 提交到 GitHub，Streamlit 下次刷新或重新部署会读到最新数据。
- **方式二**：在 Streamlit 应用里加“从 URL 拉取 JSON”的入口（例如你的后端 `/api/dashboard`），这样无需改仓库即可更新数据。

---

## 六、打开时立即更新（Live 接口）

若希望**每次打开页面都先重新拉取/生成最新数据再展示**，可用后端 **Live 接口**：

1. **后端**：已提供 `GET /api/dashboard/live`。每次请求会先执行一次 `build_dashboard_job()` 生成最新 `dashboard.json`，再返回该 JSON。
2. **前端**：配置环境变量后，打开页面或点「刷新」时会请求该接口，实现「打开即更新」。

### 配置方式

在前端项目（`dashboard_frontend/app`）下：

- 若前端通过同一域名访问后端（例如 Nginx 反代到 `/api`），只需在 `.env` 或构建环境里设：
  - `VITE_DASHBOARD_URL=/data/dashboard.json`（或你的后端根 URL）
  - `VITE_USE_LIVE_REFRESH=true`
- 若前端单独部署、跨域访问后端，设：
  - `VITE_DASHBOARD_URL=http://你的后端域名/data/dashboard.json`
  - `VITE_USE_LIVE_REFRESH=true`

前端会优先请求 `{同源或 VITE_DASHBOARD_URL 的 origin}/api/dashboard/live`，从而在打开时触发一次重新生成并拿到最新数据。

**注意**：Live 接口每次都会跑一遍 FRED + 行情拉取与计算，响应约几秒到十几秒，适合「不介意多等几秒、希望数据尽量新」的场景；若不想每次打开都等，可继续用定时任务更新 JSON，前端只读静态 `/data/dashboard.json`。

---

## 七、仍可能抓不到的数据与排查

| 数据 | 可能抓不到的原因 | 如何确认 |
|------|------------------|----------|
| **PMI（AMTMNO）** | FRED API 限流/失败、CSV 兜底也失败、历史不足 | 看 `macroSwitches` 里 PMI 的 `freshness` 或 drivers 是否含 `PMI_FALLBACK`；兜底时值为 50 |
| **港股 0700/9988** | yfinance/stooq 地区或网络问题，MarketWatch 需解析 HTML | 看 `dataStatus["0700.HK"]` / `dataStatus["9988.HK"]` 的 `provider`、`ok`、`error_reason` |
| **黄金/白银（GC=F/SI=F）** | 期货接口失败时用 xauusd/xagusd 或 GLD/SLV | 看 `dataStatus["GC=F"]`、`dataStatus["SI=F"]` 的 `provider` 与 `ok` |
| **铜（HG=F）** | 期货失败时用 CPER 代理 | 看 `dataStatus["HG=F"]` |
| **美股 TSLA/SMH** | yfinance/stooq 网络或限流 | 看 `dataStatus["TSLA"]`、`dataStatus["SMH"]` |
| **BTC** | Binance 主/备 API 均不可达 | 看 `dataStatus["BTC-USD"]` |

当某 ticker **所有数据源都失败**时，该资产在 `assets` 里 **price 为 null**（不会写 0），`dataStatus[ticker].ok === false`，`note === "stale/fallback"`。排查时可直接打开返回的 `dashboard.json` 查看 `dataStatus` 各 ticker 的 `provider`、`freshness_days`、`ok`、`error_reason`。

---

## 八、小结

- **“周金涛”三字**：已从前端页脚文案中移除，页面上不会再出现。
- **打开时立即更新**：后端提供 `GET /api/dashboard/live`，前端设 `VITE_USE_LIVE_REFRESH=true` 即可在打开/刷新时先重新生成再展示（见第六节）。
- **仍可能抓不到的数据**：PMI、港股、贵金属、铜、美股、BTC 等可能因网络/限流/地区导致某次抓取失败，通过 `dashboard.json` 里的 `dataStatus` 可查看每个 ticker 的 `provider`、`ok`、`error_reason`（见第七节）。
- **部署到云**：推荐在 **一台云服务器** 上用 **Docker Compose** 跑前端 + 后端，用 **crontab 每天跑一次** `python tools/generate_dashboard_json.py` 更新 `dashboard.json`；若你更熟悉 Vercel/Netlify，可按方式 B 做前端静态部署；**零服务器**可选 **Streamlit Cloud**，用 `streamlit run streamlit_app.py` 部署（见方式 C）。
