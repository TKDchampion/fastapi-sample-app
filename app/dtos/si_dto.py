from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SIListItemDTO(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SIListResponseDTO(BaseModel):
    si: List[SIListItemDTO] = Field(default_factory=list)
