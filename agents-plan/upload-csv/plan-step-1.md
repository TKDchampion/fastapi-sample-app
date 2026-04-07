# Plan Step 1 — Entity: ChatbotCsvEntity

## 目標
建立 `chatbot_csvs` table 的 SQLAlchemy ORM model，並在 `entities/__init__.py` 中 import。

## 檔案

### 新增：`app/entities/chatbot_csv_entity.py`

```python
class ChatbotCsvEntity(Base):
    __tablename__ = "chatbot_csvs"

    id: int (PK, autoincrement)
    chatbot_id: int (FK → chatbots.id, CASCADE, NOT NULL)
    gcs_url: str (String(1024), NOT NULL)
    original_filename: str (String(255), NOT NULL)
    created_at: datetime (DateTime timezone, server_default=now())
```

### 修改：`app/entities/__init__.py`
- 新增 `from .chatbot_csv_entity import ChatbotCsvEntity`

## 完成後
執行 Step 03-B（Migration Review）
