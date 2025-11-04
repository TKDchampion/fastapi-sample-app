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

    class Config:
        from_attributes = True


class OrgNodeDTO(BaseModel):
    level: str = Field(default="org")
    id: int
    name: str
    role: str
    isActive: bool
    permissions: List[str]


class SINodeDTO(BaseModel):
    level: str = Field(default="si")
    id: int
    name: str
    isActive: bool
    accessibleNode: List[OrgNodeDTO]


class PermissionTreeDTO(BaseModel):
    level: str = Field(default="super")
    isActive: bool
    accessibleNode: List[SINodeDTO]


class UserAccessTreeResponseDTO(BaseModel):
    user: UserReadDTO
    permissionTree: PermissionTreeDTO


class RoleRow(BaseModel):
    # Flattened row from joined user_roles + role + permission (+ org for name lookup)
    scope_type: str
    scope_id: int
    isActiveOrg: Optional[bool]
    role_id: int
    role_name: str
    permission_name: Optional[str]
