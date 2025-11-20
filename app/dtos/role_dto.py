from pydantic import BaseModel, ConfigDict


class RoleDTO(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)
