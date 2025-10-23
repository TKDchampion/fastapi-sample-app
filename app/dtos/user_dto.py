from pydantic import BaseModel


class UserCreateDTO(BaseModel):
    name: str
    email: str


class UserReadDTO(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
