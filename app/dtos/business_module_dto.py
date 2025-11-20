from pydantic import BaseModel


class BusinessModuleDTO(BaseModel):
    id: int
    name: str
