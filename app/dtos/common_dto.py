from pydantic import BaseModel


class TextResponseDTO(BaseModel):
    status: str
    message: str
