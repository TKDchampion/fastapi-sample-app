from pydantic import BaseModel, ConfigDict, EmailStr


class RoleDTO(BaseModel):
    id: int
    name: str
    description: str | None = None


class UserRoleCreateDTO(BaseModel):
    email: EmailStr
    role_id: int
