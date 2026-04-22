from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertInfoItemDTO(BaseModel):
    id: int
    schedule_name: str
    send_schedule: str
    is_recurring: bool
    send_email: str
    created_at: datetime
    status: int = Field(..., description="Alert狀態, 0:排程中, 1:已完成", examples=[0])


class AlertInfoResponseDTO(BaseModel):
    total_count: int
    data: list[AlertInfoItemDTO]
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class CreateAlertRequestDTO(BaseModel):
    schedule_name: str
    is_recurring: bool
    send_schedule: str
    interval: Optional[str] = None
    ads_str: str
    send_email: str


class CreateAlertResponseDTO(BaseModel):
    id: int
    email: str
    org_id: int
    schedule_name: str


class DeleteAlertRequestDTO(BaseModel):
    id: int


class DeleteAlertResponseDTO(BaseModel):
    delete_count: int
    message: str


class SyncIngestionTableInfoDTO(BaseModel):
    table_name: str
    gcs_uri: str


class SyncIngestionRequestDTO(BaseModel):
    table_info: List[SyncIngestionTableInfoDTO]
    models: List[str]
    project_name: str


class SyncIngestionResponseDTO(BaseModel):
    success_table_names: List[str]
    dataset_id: str
    status: str
    success_count: int
