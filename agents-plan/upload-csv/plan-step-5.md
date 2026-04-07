# Plan Step 5 — Service: upload_csv method in WrenAiService

## 目標
在 `WrenAiService` 新增 `upload_csv` 方法，串接 GCS 上傳與 DB 寫入。

## 檔案

### 修改：`app/services/wren_ai_service.py`

新增方法：
```python
@db_tx
def upload_csv(
    self,
    db: Session,
    user: UserReadDTO,
    si_id: int,
    org_id: int,
    file: UploadFile,
) -> ChatbotCsvReadDTO:
```

流程：
1. `_verify_and_get_chatbot(db, user, si_id, org_id)` 取得 chatbot（含權限驗證）
2. `upload_csv_to_gcs(file)` 上傳並取得 `gcs_url`（副檔名驗證在此函數內）
3. `chatbot_csv_repository.create_csv_record(db, chatbot.id, gcs_url, file.filename)`
4. 回傳 `ChatbotCsvReadDTO`
