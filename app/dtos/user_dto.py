from typing import List, Optional
from pydantic import BaseModel, Field


class UserCreateDTO(BaseModel):
    name: str
    email: str


class UserReadDTO(BaseModel):
    id: int
    name: str
    email: str
    picture: str | None = None


class OrgNodeDTO(BaseModel):
    level: str = Field(default="org")
    id: int
    name: str
    role: str
    isActive: bool
    logo: str | None = None
    permissions: List[str]
    isContractLive: Optional[bool] = None


class SINodeDTO(BaseModel):
    level: str = Field(default="si")
    id: int
    name: str | None = None
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


class UserRolesResponseDTO(BaseModel):
    user_id: int
    name: str
    email: str
    picture: str | None = None
    role_name: str
    role_id: Optional[int] = None
