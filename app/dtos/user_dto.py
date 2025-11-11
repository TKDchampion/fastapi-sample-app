from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserCreateDTO(BaseModel):
    name: str
    email: str


class UserReadDTO(BaseModel):
    id: int
    name: str
    email: str
    picture: str | None = None

    class Config:
        from_attributes = True


class OrgNodeDTO(BaseModel):
    level: str = Field(default="org")
    id: int
    name: str
    role: str
    isActive: bool
    logo: str | None = None
    permissions: List[str]


class SINodeDTO(BaseModel):
    level: str = Field(default="si")
    id: int
    name: str
    isActive: bool
    logo: str | None = None
    permissions: List[str]
    accessibleNode: List[OrgNodeDTO]


class PermissionTreeDTO(BaseModel):
    level: str = Field(default="super")
    isActive: bool
    permissions: List[str]
    accessibleNode: List[SINodeDTO]


class UserAccessTreeResponseDTO(BaseModel):
    user: UserReadDTO
    permissionTree: PermissionTreeDTO


class UserSIListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSIListResponseDTO(BaseModel):
    si: List[UserSIListItemDTO] = Field(default_factory=list)


class UserOrgListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: datetime | None = None
    contract_end: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOrgListResponseDTO(BaseModel):
    org: List[UserOrgListItemDTO] = Field(default_factory=list)
