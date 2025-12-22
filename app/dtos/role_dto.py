from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr


class RoleDTO(BaseModel):
    id: int
    name: str


class UserRoleCreateDTO(BaseModel):
    email: EmailStr
    role_id: int


class AssignRoleParamDTO(UserRoleCreateDTO):
    si_id: int
    org_id: int


class RolePermissionDTO(BaseModel):
    id: int
    name: str
    permissions: List[int]

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRoleResponseDTO(BaseModel):
    role_name: str
    permissions: List[str]
