from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.dtos.business_module_dto import BusinessModuleDTO


class OrgDetailDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime
    contract_end: datetime
    created_at: datetime
    updated_at: datetime
    business_modules: list[BusinessModuleDTO] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("business_modules")
    def serialize_business_modules(self, modules: list[BusinessModuleDTO]):
        """
        把 [BusinessModuleDTO(...), BusinessModuleDTO(...)]
        轉成 [1, 2, 3]
        """
        return [m.id for m in modules]


class OrgListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime
    contract_end: datetime
    created_at: datetime
    updated_at: datetime


class OrgListResponseDTO(BaseModel):
    org: List[OrgListItemDTO] = Field(default_factory=list)


class OrgUpsertParamDTO(BaseModel):
    org_id: Optional[int] = None
    logo: str
    name: str
    contract_start: datetime
    contract_end: datetime
    business_modules: list[int]


class OrgUpsertRequestDTO(BaseModel):
    logo: str
    name: str
    contract_start: datetime
    contract_end: datetime
    business_modules: list[int]


class OrgUpsertResponseDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime
    contract_end: datetime
    business_modules: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LogoUploadResponseDTO(BaseModel):
    url: str
