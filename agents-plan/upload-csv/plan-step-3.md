# Plan Step 3 — Repository: chatbot_csv_repository

## 目標
建立 `chatbot_csv_repository.py`，提供寫入 `chatbot_csvs` table 的函數。

## 檔案

### 新增：`app/repositories/chatbot_csv_repository.py`

函數：
```python
def create_csv_record(
    db: Session,
    chatbot_id: int,
    gcs_url: str,
    original_filename: str,
) -> ChatbotCsvEntity
```

- 使用 `db.add()` + `db.flush()`（不 commit，由上層 @db_tx 管理）
- 回傳新建的 `ChatbotCsvEntity`
