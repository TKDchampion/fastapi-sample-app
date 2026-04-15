from pydantic import BaseModel


class TableauTokenResponseDTO(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int
