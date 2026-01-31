# Streamlit 云部署步骤

把仪表盘部署到 **Streamlit Community Cloud**（免费、无需买服务器）。

---

## 一、前置条件

1. **代码在 GitHub 上**  
   本仓库已推送到 GitHub（公开或私有均可；私有需在 Streamlit 授权）。

2. **数据二选一**  
   - **方式 A**：在 Streamlit 的 **Secrets** 里配置 `DASHBOARD_JSON_URL`，指向一份可公网访问的 dashboard JSON（例如你的后端 API：`https://你的域名/api/dashboard`）。  
   - **方式 B**：在仓库里**提交**一份 `dashboard_frontend/app/public/data/dashboard.json`（本地运行 `python tools/generate_dashboard_json.py` 生成后 commit），部署后 App 会直接读这份文件。

---

## 二、部署操作

1. 打开 **[share.streamlit.io](https://share.streamlit.io)**，用 **GitHub** 登录。

2. 点击 **"New app"**：
   - **Repository**：选你的 GitHub 仓库（如 `你的用户名/康波周期`）。
   - **Branch**：选分支（如 `main`）。
   - **Main file path**：填 **`streamlit_app.py`**（仓库根目录下的入口文件）。
   - **App URL**：可自定义子路径（如 `xxx-dashboard`），或使用默认。

3. （可选）点击 **"Advanced settings"**：
   - **Requirements file**：留空则使用仓库根目录的 **`requirements.txt`**（已包含 streamlit、pandas）；若你改用其他文件名，可在此填写。

4. 若使用 **方式 A（URL 拉数据）**，在 **"Secrets"** 里填：
   ```toml
   DASHBOARD_JSON_URL = "https://你的后端域名/api/dashboard"
   ```
   保存后重新部署/刷新 App。

5. 点击 **"Deploy!"**，等待构建完成。

6. 部署完成后，打开生成的 **`xxx.streamlit.app`** 链接即可使用。

---

## 三、数据更新方式

- **用 URL（方式 A）**：在后端或任意服务上更新 dashboard JSON，Streamlit 每次打开/刷新都会请求该 URL，无需改仓库。
- **用仓库内文件（方式 B）**：在本地或 CI 里运行 `python tools/generate_dashboard_json.py`，把新生成的 `dashboard.json` 提交并推送到 GitHub，再在 Streamlit Cloud 里点 **"Reboot app"** 或等待下次访问时自动用最新文件。

---

## 四、小结

| 项目       | 说明 |
|------------|------|
| 入口文件   | 仓库根目录 **`streamlit_app.py`** |
| 依赖       | 根目录 **`requirements.txt`**（streamlit + pandas） |
| 数据来源   | 优先读环境变量 **`DASHBOARD_JSON_URL`**；未配置则读仓库内 `dashboard_frontend/app/public/data/dashboard.json` |
| 费用       | Streamlit Community Cloud 免费使用 |

按上述步骤即可完成 **云部署用 Streamlit**。
