# Mobile Interface Plan

## 1. 目標

未來希望 Smart English Trainer 可以同時支援 PC 與手機使用。

PC 版保留目前完整功能與較密集的操作介面；手機版則新增獨立入口，針對直式螢幕、觸控操作與零碎時間練習重新設計。

建議手機版入口：

```text
/mobile
```

PC 與手機共用同一套 Flask 後端 API、SQLite 題庫與學習狀態。

## 2. 為什麼採用獨立手機版

目前 PC 版功能較多，包含：

- 句子訓練
- 拆句模式
- TOEIC Part 5
- TOEIC Part 2
- AI 解析
- TTS 設定
- 匯入功能
- 篩選器
- 快捷鍵提示

如果直接把現有 PC 版改成 RWD，容易讓 CSS 和 JS 變複雜，也可能影響目前已經能用的桌面操作。

因此建議新增獨立手機頁面：

- PC：`/`
- Mobile：`/mobile`

兩者共用 API，但前端 UI 分開維護。

## 3. 手機版優先功能

第一版手機版不需要完整複製 PC 功能，建議先做最常用的練習流程。

### Phase 1：核心練習

- 句子練習
- TOEIC Part 5 作答
- TOEIC Part 2 聽力播放與作答
- 下一題 / 上一題
- 標記掌握
- 標記複習
- 顯示正確答案
- 顯示中文翻譯與解析

### Phase 2：學習狀態與篩選

- 題目狀態篩選：全部 / 新題 / 複習 / 已掌握
- TOEIC Part 5 題型篩選：全部 / 文法 / 字彙
- 單元切換
- 顯示進度
- 顯示今日練習數

### Phase 3：設定與進階功能

- 語音速度設定
- 自動播放設定
- AI 模型選擇
- API key 設定
- 匯入句子
- 學習統計

## 4. 手機版 UI 原則

手機版應該以「快速練習」為核心，不要把桌面版工具列完整搬過去。

設計原則：

- 單欄版面
- 大字體題目
- 大按鈕選項
- 底部固定操作列
- 避免小下拉選單過多
- 避免需要鍵盤快捷鍵
- 聽力播放按鈕放在明顯位置
- 題目、選項、結果不要互相擠壓
- 答題後才顯示解析，避免一開始干擾作答

建議手機版頁面結構：

```text
Header
- 模式切換
- 進度

Main Card
- 題目 / 中文提示 / 聽力播放
- 選項或輸入區
- 作答結果
- 解析區

Bottom Action Bar
- 上一題
- 播放 / 顯示答案
- 下一題
- 掌握
- 複習
```

## 5. 路由設計

後端新增手機入口：

```text
GET /mobile
```

建議新增檔案：

```text
mobile.html
mobile.css
mobile.js
```

或放進資料夾：

```text
mobile/
├── index.html
├── mobile.css
└── mobile.js
```

目前比較建議後者，讓手機版資源集中。

## 6. API 共用策略

手機版應直接使用現有 API，不新增重複後端邏輯。

可共用 API：

```text
GET  /api/units
GET  /api/units/<unit_id>/sentences
POST /api/sentences/<sentence_id>/status

GET  /api/toeic/questions
POST /api/toeic/questions/<question_id>/status
POST /api/toeic/questions/<question_id>/ai-explain

GET  /api/toeic/part2/questions
POST /api/toeic/part2/questions/<question_id>/status
POST /api/toeic/part2/questions/<question_id>/ai-explain
GET  /api/toeic/part2/questions/<question_id>/audio

GET  /api/settings/config
POST /api/settings/config
```

## 7. 區網手機使用方式

如果手機要連到電腦上的 Flask server，需要讓 Flask 綁定區網。

Windows PowerShell：

```powershell
$env:APP_HOST="0.0.0.0"
.\run.bat
```

手機與電腦需要在同一個 Wi-Fi。

手機網址格式：

```text
http://電腦區網IP:8000/mobile
```

範例：

```text
http://192.168.1.23:8000/mobile
```

注意：`0.0.0.0` 只建議在自己的區網使用，不要直接暴露到公網。

## 8. 實作步驟建議

### Step 1：建立手機入口

- 新增 `/mobile` route
- 新增 `mobile/index.html`
- 確認手機可以打開空白頁

### Step 2：接 TOEIC Part 5

- 讀取 `/api/toeic/questions`
- 顯示題目與 A/B/C/D
- 支援作答
- 支援下一題

### Step 3：接句子訓練

- 讀取 `/api/units`
- 讀取 `/api/units/<id>/sentences`
- 顯示中文提示與英文答案
- 先做顯示答案模式，再考慮手機輸入拼寫

### Step 4：接 TOEIC Part 2

- 讀取 `/api/toeic/part2/questions`
- 播放 `/api/toeic/part2/questions/<id>/audio`
- 顯示 A/B/C
- 作答後揭露文字稿

### Step 5：加入標記與解析

- 掌握 / 複習
- AI 解析
- 狀態篩選

## 9. 可能的技術注意事項

- 手機瀏覽器可能限制自動播放音訊，播放必須由使用者點擊觸發。
- 手機輸入英文拼寫時，鍵盤會佔用螢幕高度，第一版可先不做完整拼寫模式。
- Safari / Chrome 對 `speechSynthesis` 支援不同，TOEIC Part 2 建議沿用後端 mp3。
- 若手機連不到電腦，通常是防火牆、Wi-Fi 隔離或 Flask host 沒設成 `0.0.0.0`。
- 手機版不應依賴鍵盤快捷鍵。

## 10. 建議第一版範圍

第一版手機版建議只做：

- `/mobile`
- TOEIC Part 5
- TOEIC Part 2
- 句子顯示/答案揭露
- 掌握/複習
- 下一題/上一題

先讓手機能穩定練習，再逐步補匯入、設定、統計與進階拼寫功能。

