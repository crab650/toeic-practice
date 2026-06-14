# Smart English Trainer 技術文件

## 1. 專案定位

Smart English Trainer 是一個本機執行的英語訓練工具，主要用於：

- 英文句子拼寫訓練
- 英文句子拆句重組訓練
- TOEIC Part 5 文法/字彙選擇題練習
- TOEIC Part 2 聽力應答練習
- 使用 Gemini API 產生題目翻譯與解析
- 使用 edge-tts 產生 TOEIC Part 2 聽力音檔

目前設計偏向單機個人使用，後端使用 Flask，前端為原生 HTML/CSS/JavaScript，資料儲存在 SQLite。

## 2. 技術棧

| 類別 | 技術 |
| --- | --- |
| 後端 | Python, Flask |
| 前端 | HTML, CSS, Vanilla JavaScript |
| 資料庫 | SQLite |
| AI 解析 | Google Gemini API |
| TTS | edge-tts |
| 啟動方式 | Windows batch file |
| 本機服務 | `http://127.0.0.1:8000` |

## 3. 專案檔案結構

```text
.
├── app.py                    # Flask 啟動入口
├── backend/                  # 後端 package
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # 路徑、環境變數、模型設定
│   ├── db.py                 # SQLite 連線與資料表初始化
│   ├── classifier.py         # TOEIC Part 5 題型分類
│   ├── seed_data.py          # 空資料庫預設句庫
│   ├── routes/               # Web 與 API routes
│   └── services/             # Gemini 與 TTS service
├── app.js                    # 前端主邏輯與互動流程
├── index.html                # 前端頁面結構
├── style.css                 # 前端樣式
├── trainer.db                # SQLite 題庫與學習狀態
├── run.bat                   # Windows 啟動腳本
├── requirements.txt          # Python 依賴
├── config.json               # 本機設定檔，目前不建議存 API key
├── .env.example              # 環境變數範例
├── .gitignore                # Git 忽略規則
├── import_toeic.py           # 匯入 TOEIC Part 5 題庫
├── import_part2.py           # 產生/匯入 TOEIC Part 2 題庫
├── import_sentences.py       # 匯入句子訓練資料
├── AI_Prompt_Template.md     # AI 產生句子資料的提示詞模板
├── audio_cache/              # Part 2 mp3 音檔快取
└── pic/                      # 圖片資源
```

## 4. 目前程式架構

### 4.1 後端架構

後端已從單檔 `app.py` 拆成 Flask package。`app.py` 目前只負責建立 app 與啟動 server，實際功能依責任拆到 `backend/`。

目前後端結構：

```text
app.py
backend/
├── __init__.py
├── config.py
├── db.py
├── classifier.py
├── seed_data.py
├── routes/
│   ├── units.py
│   ├── toeic_part5.py
│   ├── toeic_part2.py
│   └── settings.py
└── services/
    ├── gemini.py
    └── tts.py
```

主要責任分工：

- `backend/config.py`：集中管理專案路徑、`GEMINI_API_KEY`、`GEMINI_MODEL`、server 預設設定。
- `backend/db.py`：SQLite 連線、資料表建立、舊資料表欄位補齊、空資料庫 seed。
- `backend/routes/units.py`：句子單元、句子狀態與句子匯入 API。
- `backend/routes/toeic_part5.py`：TOEIC Part 5 查詢、狀態更新與 AI 解析 API。
- `backend/routes/toeic_part2.py`：TOEIC Part 2 查詢、狀態更新、AI 解析與音檔 API。
- `backend/routes/settings.py`：Gemini key/model 設定 API。
- `backend/services/gemini.py`：Gemini API 呼叫與 prompt 組裝。
- `backend/services/tts.py`：edge-tts 音檔產生。

### 4.2 前端架構

`app.js` 目前負責所有前端狀態與互動：

- 模式切換：句子訓練、TOEIC Part 5、TOEIC Part 2
- 題目載入與分頁
- 拼寫輸入檢查
- 拆句模式邏輯
- TOEIC 選項判斷
- 狀態標記：`new`、`mastered`、`review`
- TTS 播放
- Gemini 解析觸發
- localStorage 設定儲存

目前是單一大型 JS 檔。若繼續擴充，建議拆成模組。

建議未來前端拆分方向：

```text
frontend/
├── api.js
├── state.js
├── sentence_mode.js
├── scramble_mode.js
├── toeic_part5.js
├── toeic_part2.js
├── speech.js
├── settings.js
└── main.js
```

## 5. 資料庫架構

目前 SQLite 資料庫為 `trainer.db`。

### 5.1 units

儲存句子訓練單元。

| 欄位 | 說明 |
| --- | --- |
| id | 單元 ID |
| name | 單元名稱 |

### 5.2 sentences

儲存英中句子與學習狀態。

| 欄位 | 說明 |
| --- | --- |
| id | 句子 ID |
| unit_id | 所屬單元 |
| english | 英文句子 |
| chinese | 中文翻譯 |
| status | `new`、`mastered`、`review` |

### 5.3 toeic_questions

儲存 TOEIC Part 5 題目。

| 欄位 | 說明 |
| --- | --- |
| id | 題目 ID |
| question | 題幹 |
| option_a | A 選項 |
| option_b | B 選項 |
| option_c | C 選項 |
| option_d | D 選項 |
| answer | 正確答案 |
| chinese | AI 翻譯 |
| explanation | AI 解析 |
| status | `new`、`mastered`、`review` |
| category | `grammar` 或 `vocabulary` |

### 5.4 toeic_part2_questions

儲存 TOEIC Part 2 聽力應答題。

| 欄位 | 說明 |
| --- | --- |
| id | 題目 ID |
| question | 問句或敘述 |
| option_a | A 回答 |
| option_b | B 回答 |
| option_c | C 回答 |
| answer | 正確答案 |
| status | `new`、`mastered`、`review` |
| chinese | AI 翻譯 |
| explanation | AI 解析 |

## 6. API 架構

### 6.1 單元與句子

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/api/units` | 取得所有句子單元 |
| GET | `/api/units/<unit_id>/sentences` | 取得指定單元句子 |
| POST | `/api/sentences/<sentence_id>/status` | 更新句子狀態 |
| POST | `/api/import` | 匯入自訂句子單元 |

### 6.2 設定

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/api/settings/config` | 查詢 Gemini key 是否已設定 |
| POST | `/api/settings/config` | 儲存 Gemini key |

目前後端會優先讀取環境變數 `GEMINI_API_KEY`。若有設定環境變數，會覆蓋 `config.json` 內的值。

AI 模型預設使用 `gemini-3.1-flash-lite`，定位是平常英文翻譯與解析時優先省額度。可透過設定視窗切換，或用環境變數 `GEMINI_MODEL` 覆蓋。

### 6.3 TOEIC Part 5

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/api/toeic/questions` | 分頁取得 Part 5 題目 |
| POST | `/api/toeic/questions/<question_id>/status` | 更新題目狀態 |
| POST | `/api/toeic/questions/<question_id>/ai-explain` | 產生或更新 AI 解析 |

### 6.4 TOEIC Part 2

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/api/toeic/part2/questions` | 分頁取得 Part 2 題目 |
| POST | `/api/toeic/part2/questions/<question_id>/status` | 更新題目狀態 |
| POST | `/api/toeic/part2/questions/<question_id>/ai-explain` | 產生或更新 AI 解析 |
| GET | `/api/toeic/part2/questions/<question_id>/audio` | 取得或產生聽力音檔 |

## 7. 啟動與設定

### 7.1 安裝依賴

```powershell
pip install -r requirements.txt
```

### 7.2 設定 Gemini API key

建議使用環境變數，不要把 key 寫入專案檔。

```powershell
$env:GEMINI_API_KEY="your_new_api_key"
$env:GEMINI_MODEL="gemini-3.1-flash-lite"
```

### 7.3 啟動

```powershell
.\run.bat
```

預設服務位置：

```text
http://127.0.0.1:8000
```

可用環境變數覆蓋：

```powershell
$env:APP_HOST="127.0.0.1"
$env:APP_PORT="8000"
$env:FLASK_DEBUG="0"
```

## 8. 目前資料流

### 8.1 句子訓練

```text
使用者選擇單元
→ app.js 呼叫 /api/units/<id>/sentences
→ Flask 從 SQLite 讀取 sentences
→ 前端產生拼寫輸入或拆句卡片
→ 使用者作答
→ 前端判斷答案
→ 使用者標記 mastered/review
→ POST 狀態回 SQLite
```

### 8.2 TOEIC Part 5

```text
前端依 filter/category 請求題目
→ Flask 查詢 toeic_questions
→ 前端顯示題幹與選項
→ 使用者選答案
→ 前端顯示正誤
→ 可呼叫 Gemini 解析
→ 後端把解析寫回 DB
```

### 8.3 TOEIC Part 2

```text
前端載入 Part 2 題目
→ 使用者播放音檔
→ 若 audio_cache 無 mp3，後端用 edge-tts 產生
→ 前端播放音檔
→ 使用者選 A/B/C
→ 前端揭露文字稿與解析區
```

## 9. 目前風險與技術債

### 9.1 API key 管理

目前已移除 `config.json` 內的明文 key，也加入 `.gitignore`。未來建議完全改成 `.env` 或系統環境變數，不再透過前端設定頁寫入 `config.json`。

### 9.1.1 AI 免費額度策略

目前 AI 解析採「免費額度優先」策略：

- 預設模型：`gemini-3.1-flash-lite`
- 進階模型：`gemini-3.5-flash`
- 環境變數覆蓋：`GEMINI_MODEL`
- 超過免費額度或速率限制時，後端會回傳 quota/rate limit 相關錯誤

這個專案的 AI 用途主要是英文題目翻譯與解析，通常不需要使用高成本模型。若未來要做長篇作文批改、口說評分或複雜學習分析，再考慮切換更強模型。

### 9.2 單檔過大

`app.py` 已拆分成後端 package；目前主要剩下 `app.js` 承擔較多前端責任。若繼續擴充，下一步建議拆分前端狀態、API client、句子模式、TOEIC Part 5、TOEIC Part 2 與語音設定模組。

### 9.3 缺少測試

目前只有人工 smoke test。建議補：

- API endpoint 測試
- DB 初始化測試
- 匯入腳本測試
- 題目狀態更新測試
- Gemini 回傳格式處理測試

### 9.4 資料庫版本管理

目前資料表由 `backend/db.py` 內的 `CREATE TABLE` 和 `ALTER TABLE` 管理。未來欄位增加時，建議導入簡單 migration 機制。

### 9.5 前端安全

部分位置使用 `innerHTML` 顯示題目或 AI 解析。若資料來源未來包含外部輸入，應改成安全渲染或 HTML escape。

### 9.6 離線能力

前端使用 Google Fonts 與 Font Awesome CDN。若要完全離線使用，建議改成本地字型與本地 icon。

## 10. 未來擴充規劃

### Phase 1：穩定化

- 補 README
- 補正式測試
- 補資料庫備份/還原工具
- 將 `app.js` 拆成多個功能模組
- 完全移除前端寫入 API key 到 `config.json` 的流程

### Phase 2：學習體驗強化

- 加入每日學習目標
- 加入錯題本
- 加入間隔複習排程
- 加入答題歷史紀錄
- 加入每單元正確率統計
- 加入 TOEIC Part 5 題型分析
- 加入 Part 2 聽力重播次數統計

### Phase 3：內容管理

- 建立題庫管理頁
- 支援匯入 CSV/JSON/Excel
- 支援題目編輯與刪除
- 支援單元排序與分類
- 支援批次產生 AI 翻譯與解析
- 支援資料庫匯出備份

### Phase 4：技術升級

- 將後端拆成 package 結構
- 導入 migration 工具
- 導入 pytest
- 導入前端 build 工具或輕量框架
- 加入本機登入或使用者 profile
- 支援 Docker 啟動
- 支援 PWA 離線使用

### Phase 5：多使用者或雲端版

若未來要從本機工具變成多人使用系統，需要新增：

- 使用者帳號
- 權限管理
- 後端正式部署設定
- PostgreSQL 或其他 server database
- API rate limit
- AI key server-side 管理
- HTTPS
- 備份策略

## 11. 建議的下一步

短期最值得做的順序：

1. 建立初始 Git commit
2. 決定 `trainer.db` 是否納入版本控制
3. 補 README.md，讓使用者知道怎麼啟動
4. 補最小 API 測試
5. 拆分 `app.js` 的模式邏輯

## 12. Commit 建議

若要建立第一個 commit，建議先確認是否追蹤 `trainer.db`。

若要把題庫也放進 Git：

```powershell
git add .
git commit -m "Initial Smart English Trainer project"
```

若不想把題庫放進 Git，先把 `trainer.db` 加入 `.gitignore`，再 commit。
