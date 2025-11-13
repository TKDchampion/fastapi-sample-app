from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.dtos.business_module_dto import BusinessModuleDTO


class OrgListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    created_at: datetime
    updated_at: datetime
    business_modules: list[BusinessModuleDTO] = []

    model_config = ConfigDict(from_attributes=True)


class OrgListResponseDTO(BaseModel):
    org: List[OrgListItemDTO] = Field(default_factory=list)


class OrgUpsertRequestDTO(BaseModel):
    org_id: Optional[int] = None
    logo: str
    name: str
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    business_modules: list[int]

    # class Config:
    #     orm_mode = True


class OrgUpsertResponseDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    business_modules: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogoUploadResponseDTO(BaseModel):
    url: str
