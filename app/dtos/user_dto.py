from pydantic import BaseModel


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


class UserAccessTreeResponseDTO(BaseModel):
    user: UserReadDTO
    permissionTree: dict
