# 語言練習紀錄批次上傳對接規格（確認稿）

## 1. 文件目的

本文件用於確認「語言學習系統」是否能將使用者完成的語言練習紀錄，批次上傳至「Personal Learning & Workspace 學習平台」。

目前階段只處理練習紀錄的可靠上傳、保存與每日彙整，不包含 GitHub 發布、熱力圖或 GitHub Token 串接。

## 2. 使用情境

預期使用流程如下：

1. 使用者在語言學習系統進行英文或越文練習。
2. 語言學習系統先在本機保存每一次練習紀錄。
3. 使用者完成一段練習後，或由系統排程，每天批次上傳一至兩次。
4. 學習平台接收練習明細，避免重複入帳，並依實際練習日期彙整當日學習成果。
5. 未來再由學習平台的獨立定時器，於每日固定時間將彙整結果發布到 GitHub。

本期資料流程：

```text
語言學習系統
  └─ 本機保存每次練習
       └─ 每天手動或定時批次上傳 1～2 次
            └─ 學習平台保存練習明細
                 └─ 學習平台彙整每日學習成果
```

未來流程（不在本期範圍）：

```text
學習平台每日彙整
  └─ 固定時間執行發布任務
       └─ 更新 GitHub 日誌、統計或熱力圖
```

## 3. 核心資料原則

### 3.1 每次練習都是一筆獨立事件

同一個學習項目可能在同一天或不同日期練習多次，每一次都必須保留為獨立紀錄。

例如，同一題 `vi-402` 今天練習三次：

```text
第一次：答錯、播放 3 次、看過答案
第二次：答對、播放 2 次、沒有看答案
第三次：答對、播放 1 次、沒有看答案
```

學習平台應保存三筆練習明細，並將今日統計彙整為：

```text
練習次數：3
答對次數：2
答錯次數：1
播放次數：6
查看答案次數：1
不同學習項目數：1
```

因此，不能只使用 `sentence_id` 判斷資料是否重複。

### 3.2 上傳重送不能造成重複入帳

每次練習都必須具有永不重複的 `event_id`。同一次練習因網路中斷、逾時或補傳而再次上傳時，必須沿用相同的 `event_id`。

判斷方式：

- `sentence_id` 相同、`event_id` 不同：代表同一題再次練習，應新增紀錄。
- `event_id` 相同：代表同一筆紀錄重送，不應再次新增或重複統計。

### 3.3 依實際練習時間彙整

平台必須根據 `occurred_at` 判斷學習日期，而不是根據上傳時間。

例如：

- 7 月 12 日 23:30 完成練習。
- 7 月 13 日 08:00 才批次上傳。
- 該紀錄仍應計入 7 月 12 日的學習成果。

時間必須包含 UTC offset，例如：

```text
2026-07-12T23:30:00+07:00
```

## 4. 本期功能範圍

### 4.1 包含

- 語言學習系統批次上傳練習紀錄。
- Bearer Token 驗證上傳者身分。
- 支援英文與越文練習。
- 保存同一學習項目的多次練習。
- 使用 `event_id` 防止同一事件重複入帳。
- 依實際練習日期建立每日彙整。
- 回傳每筆資料的建立、重複或失敗狀態。
- 語言學習系統可在失敗後安全重送。

### 4.2 不包含

- GitHub API 串接。
- GitHub PAT 管理。
- GitHub 日誌、Commit 或熱力圖發布。
- 即時逐筆上傳要求。
- 學習平台向語言學習系統下載題庫。
- AI 分析與學習建議。

## 5. 建議 API

### 5.1 批次上傳練習紀錄

```http
POST /api/v1/study/practice-logs
Content-Type: application/json
Authorization: Bearer <Platform_Access_Token>
```

同一個 API 可以一次傳送一筆或多筆紀錄。建議每批最多 100 筆。

### 5.2 請求格式

```json
{
  "device_id": "smart-language-trainer-home-pc",
  "events": [
    {
      "event_id": "0190cc7a-6483-7d55-a1c2-73cb31f6be20",
      "sentence_id": "vi-402",
      "language": "vi",
      "exercise_type": "multiple_choice",
      "sentence_text": "Chào buổi sáng, bạn khỏe không?",
      "translation_text": "早上好，你好嗎？",
      "user_answer": "Chào buổi sáng, bạn khỏe không?",
      "is_correct": true,
      "audio_play_count": 2,
      "revealed_answer": false,
      "occurred_at": "2026-07-12T15:30:20+07:00",
      "timezone": "Asia/Bangkok"
    },
    {
      "event_id": "0190cc7a-87aa-7ea1-83c8-41231ffb9142",
      "sentence_id": "vi-402",
      "language": "vi",
      "exercise_type": "multiple_choice",
      "sentence_text": "Chào buổi sáng, bạn khỏe không?",
      "translation_text": "早上好，你好嗎？",
      "user_answer": "Chào buổi sáng",
      "is_correct": false,
      "audio_play_count": 3,
      "revealed_answer": true,
      "occurred_at": "2026-07-12T16:10:05+07:00",
      "timezone": "Asia/Bangkok"
    }
  ]
}
```

上述範例中，兩筆資料的 `sentence_id` 相同，但 `event_id` 不同，因此代表同一題練習兩次，平台應保存兩筆。

## 6. 欄位規格

| 欄位 | 必填 | 型別 | 說明 |
| --- | --- | --- | --- |
| `device_id` | 是 | string | 語言學習系統的裝置或安裝識別碼 |
| `events` | 是 | array | 本次批次上傳的練習事件，最多 100 筆 |
| `event_id` | 是 | string | 每次練習唯一 ID，建議使用 UUID |
| `sentence_id` | 是 | string | 語言系統內的題目或句子 ID |
| `language` | 是 | string | 第一版支援 `en`、`vi` |
| `exercise_type` | 建議 | string | 例如 `multiple_choice`、`typing`、`listening` |
| `sentence_text` | 是 | string | 本次練習的英文或越文原文 |
| `translation_text` | 否 | string | 中文翻譯或其他對照文字 |
| `user_answer` | 否 | string | 使用者本次實際答案；若練習類型無答案可不傳 |
| `is_correct` | 是 | boolean | 本次作答是否正確 |
| `audio_play_count` | 是 | integer | 本次練習播放音檔次數，最小為 0 |
| `revealed_answer` | 是 | boolean | 本次練習是否曾顯示答案 |
| `occurred_at` | 是 | string | ISO 8601 格式，必須包含 UTC offset |
| `timezone` | 建議 | string | IANA 時區，例如 `Asia/Bangkok` |

### 6.1 `sentence_id` 型別

建議使用字串而不是整數，以便語言系統傳送：

```text
en-402
vi-402
lesson-12-sentence-5
```

若語言系統目前只能提供整數，平台也可以接受，但必須搭配 `language` 才能識別項目。

### 6.2 `event_id` 產生時機

語言學習系統應在「一次練習完成並寫入本機資料庫」時產生 `event_id`，不能等到上傳時才產生。

錯誤做法：每次重送都產生新的 `event_id`，會造成平台將同一筆練習重複入帳。

正確做法：一筆本機練習紀錄建立一次 `event_id`，直到平台確認接收前，所有重送都沿用該 ID。

## 7. 回應格式

### 7.1 全部接收成功

```json
{
  "success": true,
  "data": {
    "accepted": 2,
    "duplicates": 0,
    "rejected": 0,
    "results": [
      {
        "event_id": "0190cc7a-6483-7d55-a1c2-73cb31f6be20",
        "status": "created",
        "log_id": 98213
      },
      {
        "event_id": "0190cc7a-87aa-7ea1-83c8-41231ffb9142",
        "status": "created",
        "log_id": 98214
      }
    ]
  }
}
```

### 7.2 相同資料再次上傳

平台應視為安全重送，不應當成整個請求失敗：

```json
{
  "success": true,
  "data": {
    "accepted": 0,
    "duplicates": 2,
    "rejected": 0,
    "results": [
      {
        "event_id": "0190cc7a-6483-7d55-a1c2-73cb31f6be20",
        "status": "duplicate",
        "log_id": 98213
      },
      {
        "event_id": "0190cc7a-87aa-7ea1-83c8-41231ffb9142",
        "status": "duplicate",
        "log_id": 98214
      }
    ]
  }
}
```

### 7.3 部分資料錯誤

有效資料可以接收，錯誤資料逐筆回報：

```json
{
  "success": false,
  "data": {
    "accepted": 1,
    "duplicates": 0,
    "rejected": 1,
    "results": [
      {
        "event_id": "0190cc7a-6483-7d55-a1c2-73cb31f6be20",
        "status": "created",
        "log_id": 98213
      },
      {
        "event_id": "invalid-event",
        "status": "rejected",
        "errors": {
          "occurred_at": "A valid ISO 8601 time with UTC offset is required."
        }
      }
    ]
  }
}
```

## 8. 語言學習系統的本機同步需求

語言學習系統應為每筆本機練習紀錄保存：

- `event_id`
- 完整練習內容
- `sync_status`：例如 `pending`、`synced`、`failed`
- `sync_attempts`
- `last_sync_error`
- `synced_at`

建議流程：

```text
練習完成
  → 寫入本機資料庫，狀態設為 pending
  → 每天手動或排程挑出 pending/failed 資料
  → 批次呼叫平台 API
  → created 或 duplicate：改為 synced
  → rejected：保留 failed 與錯誤原因
  → 網路或平台暫時失敗：保留 pending，稍後重試
```

`duplicate` 也應標記為 `synced`，因為這代表平台先前已成功接收。

## 9. 學習平台每日彙整需求

平台保存每一筆明細後，應能依使用者、日期與語言計算：

- `total_attempts`：所有練習事件數量。
- `correct_attempts`：答對次數。
- `incorrect_attempts`：答錯次數。
- `unique_items`：不同 `sentence_id` 數量。
- `audio_plays`：播放音檔總次數。
- `reveals`：曾查看答案的練習次數。
- `first_practiced_at`：當日第一次練習時間。
- `last_practiced_at`：當日最後一次練習時間。

同一題練習多次時：

- 每次都計入 `total_attempts`。
- 該題在 `unique_items` 只計算一次。
- 每次的正確性、播音與查看答案都分別累計。

本期只要求平台正確保存與彙整。GitHub 發布程式未來再讀取此處的每日結果。

## 10. 驗證與錯誤處理

建議 HTTP 狀態：

| HTTP 狀態 | 使用時機 |
| --- | --- |
| `200` | 批次已處理；每筆結果由 `results` 說明 |
| `400` | JSON 結構錯誤或缺少整個批次必要欄位 |
| `401` | Token 缺少、錯誤、過期或已撤銷 |
| `403` | Token 沒有 `study:write` 權限 |
| `413` | 批次或 request body 超過限制 |
| `429` | 請求頻率超過限制 |
| `500` | 平台內部錯誤；語言系統應稍後安全重送 |

使用者身分必須由 Bearer Token 決定，語言系統不應傳送或自行指定平台的 `user_id`。

## 11. 雙方需確認的問題

請語言學習系統開發端確認以下項目：

1. 每一次完成練習時，是否會建立一筆獨立的本機紀錄？
2. 是否能為每次練習產生並永久保存唯一 `event_id`？
3. 同一筆紀錄重送時，是否能沿用原本的 `event_id`？
4. 是否已有可長期識別安裝環境的 `device_id`？
5. 目前可提供哪些練習欄位？是否包含正確性、播音次數與查看答案？
6. `sentence_id` 目前是整數還是字串？英文與越文是否可能使用相同 ID？
7. 是否能提供包含 UTC offset 的實際練習時間？
8. 是否能保存 `pending`、`synced`、`failed` 等同步狀態？
9. 是否能一次上傳多筆 JSON，並處理每筆不同的回應狀態？
10. 一天一至兩次上傳是由使用者按下「上傳」，還是由排程自動執行？
11. 單日可能產生的最大練習筆數約為多少？
12. 除了英文與越文，近期是否需要支援其他語言？
13. 除了句子練習，是否還有單字、聽力或口說等不同項目類型？
14. `user_answer` 是否允許上傳？是否包含需要避免上傳的敏感內容？

## 12. 對接驗收條件

雙方完成下列測試，即可視為第一階段對接成功：

1. 使用有效 Token 上傳一批英文或越文練習紀錄。
2. 同一個 `sentence_id` 使用不同 `event_id` 上傳多次，平台保存全部練習。
3. 相同 `event_id` 重送多次，平台只保存及統計一次。
4. 前一天的離線資料隔天補傳，仍歸入實際練習日期。
5. 一批資料中部分錯誤時，有效項目仍能成功保存。
6. 語言系統能依每筆 `created`、`duplicate`、`rejected` 更新本機同步狀態。
7. 平台的每日練習次數、不同項目數、正確次數、播音次數及查看答案次數均與原始資料一致。
8. 無效或已撤銷 Token 無法上傳。
9. 不同平台使用者的資料完全隔離。
10. Token 明文不會寫入平台資料庫或應用程式 log。

## 13. 建議確認結果格式

語言學習系統開發端可直接回覆：

```text
可直接支援：
- ...

需要修改後支援：
- ...

無法提供的欄位：
- ...

目前本機資料表欄位：
- ...

預計上傳方式：手動 / 自動排程 / 兩者皆有
預估單次最大筆數：...

建議調整的 API 或欄位：
- ...
```

## 14. 已確認的第一版實作契約

本節依 `LANGUAGE_PRACTICE_UPLOAD_CONFIRMATION_QUESTIONS.md` 的確認結果補充，若與前述「建議」內容不同，第一版實作以本節為準。

### 14.1 客戶端範圍

- 第一版由使用者按下「立即同步」後上傳，並保留未來排程呼叫同一同步服務的能力。
- 納入 `spelling`、`scramble`、`toeic_part5`、`toeic_part2` 四種固定 `exercise_type`。
- 第一版支援 `en`、`vi`；資料結構保留增加其他 ISO 639-1 語言代碼的能力。
- `sentence_id` 使用 `{language}-{source_type}-{local_id}`，最大 120 字元，只允許英文字母、數字、`-`、`_`、`.`、`:`。
- `event_id` 在本機事件建立時產生，只接受 UUID v4。
- `device_id` 代表一次應用程式安裝，首次啟動產生並永久保存。
- 舊版練習紀錄不補傳；只同步新版事件機制建立的紀錄。
- 每批最多 100 筆，超過時依建立時間由舊至新自動分批。
- `user_answer` 選填；句子題傳實際輸入文字，TOEIC 題只傳選項代碼。

### 14.2 欄位限制

- `sentence_text` 必填且最大 10,000 字元。
- `translation_text`、`user_answer` 選填且最大 10,000 字元。
- `audio_play_count` 必須為 0～10,000 的整數。
- `is_correct`、`revealed_answer` 必須為 JSON boolean。
- `timezone` 必須是有效 IANA 時區；`occurred_at` 必須包含 UTC offset。
- 平台將時間點轉換到 `timezone` 後產生 `study_date`。若該時間點的 offset 與時區明顯不一致，該事件回傳 `rejected`。
- `events` 不可為空陣列；request body 最大 1 MiB。
- 未知欄位第一版忽略且不保存。

### 14.3 身分、安全與帳號切換

- Base URL 必須可設定；本機開發預設為 `http://127.0.0.1:5050`。
- Token 由平台設定頁建立，需具有 `study:write` scope，可撤銷且可選擇到期日。
- Windows 正式版使用 Windows Credential Manager 保存 Token；環境變數可作為開發與自動測試覆寫來源。
- Token 明文不得寫入 `config.json`、SQLite、Git、錯誤回報或應用程式 log。
- 平台提供 `GET /api/v1/auth/me`，以 `{ "success": true, "data": { ... } }` 包裝回傳；`data` 內包含 `user_id`、`username`、`display_name`、Token prefix 與 scopes。
- pending 事件必須綁定建立／首次確認時的平台帳號。更換 Token 時，不得將既有 pending 資料自動上傳至另一帳號。

### 14.4 去重及逐筆結果

- `event_id` 在同一平台使用者內唯一，資料庫唯一鍵為 `(user_id, event_id)`。
- 相同 `event_id` 且核心內容相同：回傳 `duplicate` 及原 `log_id`。
- 相同 `event_id` 但核心內容不同：回傳 `conflict`，不得覆寫原紀錄。
- `created`、`duplicate`：客戶端標記為 `synced`。
- `rejected`、`conflict`：客戶端標記為 `failed` 並保存原因。
- 網路錯誤、`429` 或暫時性 `5xx`：保留 `pending`，稍後使用相同 `event_id` 重試。
- 完成逐筆處理的批次一律回 HTTP `200`，包括全部重複、部分失敗及 conflict；客戶端必須解析每筆 `results[].status`。
- 整個 JSON 或批次結構無法解析時才回 `400`，不使用 `207`。

### 14.5 平台尚待交付

- 實作 `POST /api/v1/study/practice-logs` 與 `GET /api/v1/auth/me`。
- 提供可清理的測試資料庫與查看練習明細／每日彙整的介面。
- 提供有效 `study:write` Token、已撤銷 Token及缺少 scope 的 Token。
- 正式 Base URL 待部署完成後提供；正式驗收不得直接使用正式資料庫。
