# Plan Step 6 — Router: POST /wren_ai/si/{si_id}/org/{org_id}/csv

## 目標
在 `wren_ai_router.py` 新增 CSV 上傳 endpoint，並 import 所需 DTO。

## 檔案

### 修改：`app/routers/wren_ai_router.py`

新增 import：
```python
from fastapi import File, UploadFile
from app.dtos.wren_ai_dto import ChatbotCsvReadDTO
```

新增 endpoint：
```python
@router.post(
    "/si/{si_id}/org/{org_id}/csv",
    response_model=ChatbotCsvReadDTO,
    status_code=201,
)
@router_try()
def upload_csv_endpoint(
    si_id: int,
    org_id: int,
    file: UploadFile = File(...),
    service: WrenAiService = Depends(WrenAiService),
    user_info: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    return service.upload_csv(db, user_info, si_id, org_id, file)
```

## 注意
- `main.py` 已有 `wren_ai_router.router` 註冊，不需修改
