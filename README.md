# 芯彤的小角落｜正式版

芯彤美學 Heart studio 的會員網站：LINE 登入、每日任務、芯幣與小魚乾、塔羅指引、幸運轉盤、折價券、邀請好友，以及店家核銷頁。

## 架構

| 部分 | 用什麼 | 位置 |
|---|---|---|
| 網頁 | 純 HTML（不需要打包） | `public/` |
| 伺服器程式 | Netlify Functions | `netlify/functions/api.mjs` |
| 資料庫 | Supabase（PostgreSQL） | `supabase/schema.sql` |
| 登入 | LINE Login | — |

- 芯幣、小魚乾、任務、轉盤、票券、邀請紀錄：存在 Supabase，所有計算都在伺服器完成，客人無法竄改
- 心情日記、喝水、翻牌、抽牌紀錄：只存在客人自己的手機，不會上傳

## 頁面

| 網址 | 用途 |
|---|---|
| `/` | 客人用的小角落 |
| `/staff.html` | 店家核銷頁（要輸入店家密碼） |
| `/privacy.html` | 隱私權政策 |
| `/?ref=邀請碼` | 邀請連結 |

## 第一次上線步驟

### 1. Supabase
1. 到 supabase.com 建立專案（地區選 Tokyo 或 Singapore）
2. 左側 **SQL Editor** → 貼上 `supabase/schema.sql` 全部內容 → **Run**
3. 左側 **Project Settings → API**，記下：
   - Project URL
   - `service_role` 金鑰（**不能公開**）

### 2. LINE Developers
1. 到 developers.line.biz，選 LINE 官方帳號所在的 Provider
2. 建立 **LINE Login** 頻道（App type 勾 Web app）
3. 記下 **Channel ID** 和 **Channel secret**（**不能公開**）
4. 在 **LINE Login** 分頁的 **Callback URL** 填：`https://你的網址/api/callback`
5. 頻道狀態從 Developing 改成 **Published**，客人才能登入

### 3. Netlify
1. Add new site → Import from GitHub → 選這個 repo
2. Build command 留空，Publish directory 會自動讀 `netlify.toml`
3. **Site configuration → Environment variables** 新增：

| 名稱 | 內容 |
|---|---|
| `SUPABASE_URL` | Supabase 的 Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 的 service_role 金鑰 |
| `LINE_CHANNEL_ID` | LINE Login 的 Channel ID |
| `LINE_CHANNEL_SECRET` | LINE Login 的 Channel secret |
| `SESSION_SECRET` | 隨機的一長串英數字（至少 32 字） |
| `SITE_URL` | 網站網址，例如 `https://corner.heartstudio.tw`（結尾不要加 /） |
| `STAFF_PIN` | 店家核銷頁的密碼 |

4. 重新部署一次（Deploys → Trigger deploy）

## 調整規則
芯幣價值、轉盤機率、任務獎勵、折價券門檻等數字，都在 `netlify/functions/api.mjs` 最上面的 `RULES`。
網頁上顯示的同一組數字在 `public/index.html` 的 `CONFIG` 與 `WHEEL`，兩邊要一起改。
