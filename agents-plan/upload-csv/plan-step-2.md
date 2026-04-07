# Plan Step 2 — DTO: ChatbotCsvReadDTO

## 目標
在 `wren_ai_dto.py` 新增 CSV 上傳回應的 Pydantic DTO。

## 檔案

### 修改：`app/dtos/wren_ai_dto.py`

新增：
```python
class ChatbotCsvReadDTO(BaseModel):
    id: int
    chatbot_id: int
    gcs_url: str
    original_filename: str
    created_at: datetime
```
