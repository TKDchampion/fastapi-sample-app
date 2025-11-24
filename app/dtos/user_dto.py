from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.dtos.role_dto import RoleDTO


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


class UserRolesResponseDTO(BaseModel):
    user_id: int
    name: str
    email: str
    picture: str | None = None
    role_name: str
