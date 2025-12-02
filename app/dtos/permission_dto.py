from typing import List
from pydantic import BaseModel, ConfigDict


class RolePermissionDTO(BaseModel):
    id: int
    name: str
    permissions: List[int]

    model_config = ConfigDict(from_attributes=True)


class OrgPermissionDTO(BaseModel):
    id: int
    key: str
    name: str


class RolePermissionUpdateDTO(BaseModel):
    id: int
    permissions: List[int]
