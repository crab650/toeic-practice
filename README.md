# Smart English Trainer

Smart English Trainer 是一個本機執行的英語訓練工具，目標是幫助使用者系統化練習 TOEIC 題型、強化英文句型熟悉度，並透過反覆作答、聽力播放與 AI 解析來提升多益分數。

這個專案的出發點很單純：我希望有一個可以每天打開就練習的工具，不只刷多益題目，也能練習英文句子的拼寫、語序與理解能力。透過句型訓練、TOEIC Part 5 文法/字彙題、TOEIC Part 2 聽力應答題，以及 AI 產生的翻譯與解析，讓準備多益的過程更集中、更有效率。

## Features

- 句子拼寫訓練：依中文提示輸入英文句子，強化單字拼寫與句型記憶。
- 拆句重組模式：將英文句子拆成單字卡片，訓練語序與句構。
- TOEIC Part 5 練習：支援文法與字彙選擇題，並可依狀態與題型篩選。
- TOEIC Part 2 聽力練習：播放聽力題目與選項，訓練即時聽懂與反應。
- 學習狀態標記：可將題目或句子標記為 `new`、`review`、`mastered`。
- 寵物養成系統：答對題目可獲得 XP、累積 streak、提升寵物等級，讓每日練習更有回饋感。
- 寵物每日任務與道具：支援每日任務獎勵、snack/toy/charm 道具，以及答題表現帶來的額外成長。
- 寵物外觀 skin：內建 default、aqua、ember、blossom、cosmic 等 skin，依等級解鎖並即時切換。
- AI 翻譯與解析：可使用 Gemini API 產生中文翻譯與詳解。
- 免費額度優先：預設使用 `gemini-3.1-flash-lite`，適合一般英文解析與省額度使用。
- 本機 SQLite 題庫：資料、學習狀態與寵物狀態儲存在本機 `trainer.db`。

## Tech Stack

- Python
- Flask
- SQLite
- HTML / CSS / Vanilla JavaScript
- Gemini API
- edge-tts

## Project Structure

```text
.
├── app.py                    # Flask 啟動入口
├── backend/                  # 後端 package
│   ├── config.py             # 路徑、環境變數與模型設定
│   ├── db.py                 # SQLite 連線與資料表初始化
│   ├── routes/               # API routes
│   └── services/             # Gemini 與 TTS service
├── app.js                    # 前端主要互動邏輯
├── index.html                # 前端頁面
├── style.css                 # 前端樣式
├── assets/
│   └── pets/                 # 寵物成長圖、skin 與動畫 frame
├── trainer.db                # SQLite 題庫與學習狀態
├── run.bat                   # Windows 啟動腳本
├── requirements.txt          # Python 依賴
├── TECHNICAL_OVERVIEW.md     # 技術文件與未來擴充規劃
├── MOBILE_INTERFACE_PLAN.md  # 行動版介面與互動規劃
├── AI_Prompt_Template.md     # AI 產生句子資料的提示詞模板
├── import_toeic.py           # TOEIC Part 5 匯入腳本
├── import_part2.py           # TOEIC Part 2 題庫產生/匯入腳本
├── import_sentences.py       # 句子資料匯入腳本
├── tools/
│   └── process_pet_assets.py # 寵物圖片切圖、去背、產生 stage/skin frame
└── audio_cache/              # 聽力音檔快取，不建議提交
```

## Getting Started

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Set Gemini API Key

AI 解析功能需要 Gemini API key。建議使用環境變數，不要把 key 寫進專案檔。

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:GEMINI_MODEL="gemini-3.1-flash-lite"
```

如果只使用句型練習、TOEIC 作答與聽力播放，可以不設定 API key；只有按下 AI 解析時才需要。

### 3. Run

```powershell
.\run.bat
```

啟動後開啟：

```text
http://127.0.0.1:8000
```

## Learning Flow

建議的練習流程：

1. 先使用句子拼寫訓練，熟悉常見英文句型。
2. 切換拆句模式，練習英文語序。
3. 使用 TOEIC Part 5 練習文法與字彙判斷。
4. 使用 TOEIC Part 2 練習聽力反應。
5. 將不熟的句子或題目標記為 `review`。
6. 定期回到 `review` 題目重練，直到能穩定答對再標記為 `mastered`。
7. 透過正確作答累積寵物 XP、streak 與每日任務進度，解鎖更高等級與 skin。

## Pet Growth System

寵物系統會把練習成果轉成可視化進度：

- 正確作答會增加 XP，並推進 1 到 20 級的寵物成長階段。
- 答錯會重置 streak，但不會清除既有等級或已解鎖內容。
- 每日任務會統計總答對數、句子練習數與 Part 2 練習數，完成後可領取道具與 XP。
- 每 3 次 streak 可獲得額外 snack，道具可用來增加 XP 或 streak。
- 寵物狀態會先保存在 `localStorage`，並透過 `/api/pet/state` 同步到 SQLite 的 `pet_state` 資料表。
- 寵物圖片位於 `assets/pets/`，每個 skin 都有 20 個 stage、每個 stage 有 3 張動畫 frame。

如果要重新產生寵物圖片資產，可使用：

```powershell
python tools\process_pet_assets.py
```

圖片來源檔為 `assets/pets/pet-growth-sheet-source.png`，輸出會產生 `assets/pets/stage-*.png` 以及 `assets/pets/skins/*/stage-*/frame-*.png`。

## AI Model Strategy

本專案的 AI 用途主要是英文題目翻譯與解析，因此預設採用免費額度優先、成本較低的模型：

```text
gemini-3.1-flash-lite
```

也可以在設定視窗切換到較強的 Flash 模型。如果超過免費額度或速率限制，後端會回傳 quota/rate limit 相關錯誤，稍後再試即可。

## Notes

- `config.json` 不建議提交，避免 API key 外洩。
- `audio_cache/` 是聽力 mp3 快取，可重新產生，不建議提交。
- `trainer.db` 是目前題庫、學習狀態與寵物狀態資料，若要保留完整資料，需一併備份。
- 寵物狀態有瀏覽器 `localStorage` fallback；如果後端或資料庫暫時不可用，前端仍會保留本機進度。
- 技術架構與未來擴充方向請看 [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md)。
