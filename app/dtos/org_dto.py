from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile
from fastapi.params import File
from pydantic import BaseModel, ConfigDict, Field


class OrgListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrgListResponseDTO(BaseModel):
    org: List[OrgListItemDTO] = Field(default_factory=list)


class OrgCreateRequestDTO(BaseModel):
    org_id: Optional[int] = None
    logo: UploadFile = File(None)
    name: str
    disabled: Optional[bool] = False
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    business_modules: Optional[list[int]] = None

    # class Config:
    #     orm_mode = True
