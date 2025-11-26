from typing import TYPE_CHECKING
from pydantic import BaseModel, EmailStr


class RoleDTO(BaseModel):
    id: int
    name: str


class UserRoleCreateDTO(BaseModel):
    email: EmailStr
    role_id: int


class AssignRoleParamDTO(UserRoleCreateDTO):
    si_id: int
    org_id: int
