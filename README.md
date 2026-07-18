# Capcom Stock Monitor

自動監察 e-capcom.com 商品有貨,即刻推送通知去 iPhone (via ntfy)。

## Setup

1. **iPhone 裝 ntfy app** — App Store 搵綠色 icon 嘅 [ntfy](https://apps.apple.com/app/ntfy/id1625396347),subscribe 一個你自己諗嘅 topic(例如 `capcom-jamie-x8k2q9`)。

2. **建 GitHub repo:**
   ```bash
   cd ~/Desktop/capcom-stock-monitor
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create capcom-stock-monitor --private --source=. --push
   ```
   或者去 [github.com/new](https://github.com/new) 手動建 repo 再 push。

3. **加 GitHub Secret:**
   `Settings → Secrets and variables → Actions → New repository secret`
   - Name: `NTFY_TOPIC`
   - Value: 你 ntfy topic 名 (例如 `capcom-jamie-x8k2q9`)

4. **(選項) 加 GitHub Variables 監察其他商品:**
   `Settings → Secrets and variables → Actions → Variables tab → New`
   - `PRODUCT_URL` = 商品 URL
   - `PRODUCT_NAME` = 通知標題用嘅名

5. **Enable Actions:**
   `Actions` tab → 見到 Workflow → `Run workflow` 手動 trigger 一次測試

## 點 work

- GitHub Actions 每 5 分鐘 run 一次 `check_stock.py`
- Script fetch 商品頁面,分析 HTML markers:
  - `在庫：×` 或 `color_Selected_ color_DisableStock_` → 缺貨
  - `在庫：○/△` 或 `color_Selected_ color_EnableStock_` → 有貨
- 對比 `state.json` 上次狀態
- 只喺**缺貨 → 有貨**轉變嗰刻 push ntfy(避免 spam)
- 更新 `state.json` commit 返 repo

## 監察其他 e-capcom 商品

換 `PRODUCT_URL` GitHub Variable 就得。呢個 script 對成個 e-capcom 網站 layout 都通用。

## 費用

- GitHub Actions: 免費 tier 2000 min/月,每次 run 只用 ~5 秒 → 完全夠 24/7 5-min interval
- ntfy.sh: 完全免費
- **總成本: $0**
