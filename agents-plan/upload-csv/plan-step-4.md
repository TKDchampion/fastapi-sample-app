# Plan Step 4 — GCS Uploader: upload_csv_to_gcs

## 目標
在 `gcs_uploader.py` 新增 `upload_csv_to_gcs` 函數，上傳 CSV 到 GCS 並回傳 public URL。

## 檔案

### 修改：`app/services/gcs_uploader.py`

新增常數：
```python
CHATBOT_CSV_FOLDER = "chatbot/csv_files"
```

新增函數：
```python
def upload_csv_to_gcs(file: UploadFile) -> str:
    """
    Upload CSV file to GCS and return public URL.
    Path: chatbot/csv_files/{YYYYMMDD}/{uuid}.csv
    """
```

- 驗證副檔名為 `.csv`，否則 raise `DomainException(msg="Only .csv files are allowed", type="invalid_file_type", code=400)`
- 使用 `storage.Client()` + `BUCKET_NAME`
- blob_name: `chatbot/csv_files/{date}/{uuid}.csv`
- 回傳 public URL
- 錯誤處理：`GoogleAPIError` → `DomainException(type="gcs_error", code=502)`
