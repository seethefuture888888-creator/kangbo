# 数据风险清单与 dashboard.json 识别方式

> **原则：任何时候宁可显示 `null + 原因`，也不要显示 `0 + 正常灯号`。**

---

## 一、宏观数据：可能抓不到/不可信

| 风险点 | 原因 | dashboard.json 如何识别 | 最佳实践 |
|--------|------|-------------------------|----------|
| FRED 返回 `.`/空值 | 发布延迟、周末/节假日、历史空洞 | `macroDataStatus[indicator].ok=false` 或 `note=missing_observation`；drivers 含 `MACRO_MISSING_OBS` | 不写 0，写 null；灯号黄 |
| 频率不匹配 | Core CPI 为月度，freshness=61 天可能正常 | `macroDataStatus[indicator].freq="M"`，结合发布日期判断 | 不误标 fallback |
| DXY 口径 | 现用 DTWEXBGS（贸易加权广义），非 ICE DXY | `macroDataStatus["DXY"].provider="fred_dtwexbgs"` | 不写成 dxy_ice |

---

## 二、行情数据：抓不到 + 抓到了也可能不对

| 风险点 | 原因 | dashboard.json 如何识别 | 最佳实践 |
|--------|------|-------------------------|----------|
| 交易日/时区错位 | BTC 24/7，港股/美股休市；按自然日算 24h 可能错位 | `dataStatus[ticker].last_obs_date` 与 `asof_ts`；若沿用旧 bar 算 24h 变化，driver 写 `STALE_BAR_USED` | 标注 last_obs_date |
| 港股 ticker 映射 | 0700.HK vs 700.hk 前导 0、后缀不同 | `dataStatus["0700.HK"].mapped_symbol="700.hk"`，`note` 含 `symbol_mapped_to=700.hk` | 映射失败时 error_reason 才有意义 |
| 代理品种口径漂移 | 铜用 CPER 代 HG，黄金用 xauusd/GLD 代 GC=F | `dataStatus["HG=F"].provider="proxy:cper.us"`，`is_proxy=true`，`proxy_for="cper.us"`；assetSignals.reasonCodes 含 `PROXY_USED` | 明确标 proxy |
| 历史长度不足 | row_count<220，MA200/分位失真 | `dataStatus[ticker].row_count`；row_count<220 时 reasonCodes 含 `INSUFFICIENT_HISTORY`，trend/risk 灯降级为黄 | 不硬判红/绿 |
| 拆股/复权 | 个股（如 TSLA）不同源复权不一致 | `dataStatus[ticker].price_adjusted=true/false` | 计算时尽量用 adjusted close |
| 限流 | 429 或空内容 | `error_reason="rate_limited"`；driver 含 `RATE_LIMITED` | 可加 retry_count |

---

## 三、dataStatus 字段（排障用）

`dataStatus[ticker]` / `macroDataStatus[indicator]` 建议包含：

| 字段 | 含义 |
|------|------|
| `mapped_symbol` | 实际请求的符号，如 0700.HK→700.hk |
| `row_count` | K 线/观测条数 |
| `last_obs_date` / `last_bar_date` | 最后一条数据日期 |
| `asof_ts` | 本次抓取完成时间（UTC） |
| `is_proxy` + `proxy_for` | 是否代理、代理的是谁（如 HG=F→CPER） |
| `stale_policy` | 是否沿用缓存，如 `cache_last_good` |

---

## 四、计算层：数据拿到了但结论可能不可靠

| 风险点 | 建议 | dashboard.json 识别 |
|--------|------|---------------------|
| Regime/RiskScore 在宏观缺失时“看起来合理” | RiskScore 输出 `riskScoreConfidence`（0~1）：缺 1 个宏观→0.8，缺 2→0.6，缺 3→0.4 | `dailySignal.riskScoreConfidence`；drivers 含 `CONFIDENCE_LOW_DUE_TO_PMI` 等 |
| ADI/CI 关键资产缺失时硬算 | 缺关键输入时 ADI/CI 置 null，reason `CHAIN_INPUT_MISSING` | `weeklyKondratieff.aiDiffusionIndex`/`constraintIndex` 为 null；`chainInputMissing="CHAIN_INPUT_MISSING"` |

---

## 五、“抓不到时怎么确认”表（含口径与历史门槛）

| 数据 | 可能抓不到原因 | 数据口径 | 历史长度门槛 | 如何确认 |
|------|----------------|----------|--------------|----------|
| PMI | FRED/CSV 失败、历史不足 | AMTMNO 代理 | 至少 37 月 orders_yoy | drivers 含 `PMI_FALLBACK`；freshness=999 |
| 港股 0700/9988 | 地区/网络、映射错误 | 原品种；Stooq 用 700.hk/9988.hk | MA200 需 ≥220 根日线 | `dataStatus["0700.HK"].mapped_symbol`，`ok`，`error_reason` |
| 黄金/白银 | 期货失败用 xauusd/xagusd 或 GLD/SLV | 代理时 `is_proxy`，`proxy_for` | ≥220 | `dataStatus["GC=F"]`，`provider`，`is_proxy` |
| 铜 | 期货失败用 CPER | 代理 CPER | ≥220 | `dataStatus["HG=F"].proxy_for="cper.us"` |
| 美股 TSLA/SMH | 限流/网络 | 原品种 | ≥220；分位建议 ≥252 | `dataStatus`，`row_count` |
| BTC | Binance 主/备均不可达 | 原品种 | ≥220 | `dataStatus["BTC-USD"]` |

---

## 六、黄金规则（不误导）

1. **价格**：抓不到时 `price=null`，不写 0；`dataStatus.note` 标 stale/fallback。
2. **宏观**：缺值时 `currentValue=null`，不写 0；`macroDataStatus.ok=false`，`note=missing_observation`。
3. **技术指标/分位**：历史不足（row_count<220）时 trend/risk 灯降为黄，reasonCodes 含 `INSUFFICIENT_HISTORY`；不硬判红/绿。
4. **ADI/CI**：关键链输入缺失时 `aiDiffusionIndex`/`constraintIndex` 为 null，`chainInputMissing` 标注原因。
5. **RiskScore**：输出 `riskScoreConfidence`；缺宏观时 drivers 写清 `CONFIDENCE_LOW_DUE_TO_*`。

已实现：price=null、dataStatus/driver 可追溯、macroDataStatus、riskScoreConfidence、INSUFFICIENT_HISTORY/PROXY_USED、weeklyKondratieff 缺链置 null。

---

## 七、更有效数据抓取（可选）

| 数据源 | 用途 | 配置 | 说明 |
|--------|------|------|------|
| **Alpha Vantage** | 美股/港股/ETF 兜底（TSLA、SMH、0700.HK、9988.HK、GLD/SLV/CPER） | `ALPHAVANTAGE_API_KEY` | 免费约 25 次/天，仅在其他源失败时调用以省配额 |
| **TwelveData** | 股票/外汇/商品兜底 | `TWELVEDATA_API_KEY` | 免费 tier 有限额 |
| **Stooq** | 已加强：双 UA 重试、多列名解析、20s 超时 | 无 | 提高在部分网络下的成功率 |
| **Binance** | 主/备双 URL，根目录脚本带 2s 延迟重试 | 可选 `BINANCE_BASE_URL` | 主用 data-api.binance.vision |
| **商品 ETF** | GC=F/SI=F/HG=F 失败后用 GLD/SLV/CPER | 无 | 多一层兜底 |

配置方式：在项目根目录或 `dashboard_backend` 下 `.env` 中设置 `ALPHAVANTAGE_API_KEY`、`TWELVEDATA_API_KEY`（可选）。抓取链顺序：yfinance → stooq → **Alpha Vantage** → MarketWatch(HK) → TwelveData → Binance → 商品 ETF 兜底。
