from pydantic import BaseModel


class ReportGroupSetItemDTO(BaseModel):
    id: int
    name: str


class ReportGroupSetListResponseDTO(BaseModel):
    report_group_sets: list[ReportGroupSetItemDTO]


class ReportGroupSetCreateRequestDTO(BaseModel):
    name: str
