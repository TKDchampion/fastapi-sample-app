# Analyze: Upload CSV to GCS (WrenAI Module)

## Requirement Summary

實作上傳 CSV 檔案到 GCS 路徑 `adnex-bi/chatbot/csv_files/{YYYYMMDD}/{uuid}.csv` 的 API，並在 DB 記錄上傳結果，關聯至 chatbot。

---

## API Endpoint

| 項目 | 內容 |
|---|---|
| Method | `POST` |
| Path | `/wren_ai/si/{si_id}/org/{org_id}/csv` |
| Request | `multipart/form-data`，欄位 `file: UploadFile`（限 `.csv`） |
| Response | `ChatbotCsvReadDTO { id, chatbot_id, gcs_url, original_filename, created_at }` |
| Permission | `business.chatbot` |

---

## DB Schema 變更

### 新增 table：`chatbot_csvs`

| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | PK, autoincrement |
| `chatbot_id` | Integer | FK → `chatbots.id` ON DELETE CASCADE, NOT NULL |
| `gcs_url` | String(1024) | NOT NULL |
| `original_filename` | String(255) | NOT NULL |
| `created_at` | DateTime(timezone=True) | NOT NULL, server_default=now() |

- 需要 Alembic migration

---

## 多租戶權限

- 使用 `si_id` + `org_id` 路徑參數，`verify_user_permission(..., perm="business.chatbot")`
- `chatbot_id` 由 `org_id` lookup 得出（與現有模式一致）

---

## 外部服務

- GCS：在 `gcs_uploader.py` 新增 `upload_csv_to_gcs(file: UploadFile) -> str`，回傳 public URL
- 使用現有 `BUCKET_NAME` env var（值為 `adnex-bi`）
- GCS folder: `chatbot/csv_files/{YYYYMMDD}/{uuid}.csv`

---

## 業務流程

1. 驗證使用者權限（`business.chatbot`）
2. 驗證檔案副檔名為 `.csv`，否則回 `400 invalid_file_type`
3. 取得 `chatbot`（by `org_id`）
4. 上傳 CSV 到 GCS，取得 `gcs_url`
5. 在 `chatbot_csvs` table 建立記錄（`chatbot_id`, `gcs_url`, `original_filename`）
6. 回傳 `ChatbotCsvReadDTO`

---

## Transaction 邊界

- GCS 上傳成功後才寫 DB，無需 rollback GCS（GCS 無 transaction）
- DB 寫入使用 `@db_tx` 管理

---

## 不需要

- Alembic downgrade 複雜邏輯（新增 table 即可）
- SSE / streaming
- 非同步（GCS upload 使用同步 `google-cloud-storage` SDK）
