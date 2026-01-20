from pydantic import BaseModel


class InsightInfoRequestDTO(BaseModel):
    table_location: str
    type: str
