from typing import TYPE_CHECKING
from pydantic import BaseModel, EmailStr

if TYPE_CHECKING:
    from app.dtos.user_dto import UserReadDTO


class RoleDTO(BaseModel):
    id: int
    name: str
    description: str | None = None


class UserRoleCreateDTO(BaseModel):
    email: EmailStr
    role_id: int


class AssignRoleParamDTO(UserRoleCreateDTO):
    si_id: int
    org_id: int
    user_info: "UserReadDTO"
