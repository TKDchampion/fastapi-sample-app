from pydantic import BaseModel


class ReportGroupSetItemDTO(BaseModel):
    id: int
    name: str


class ReportGroupSetListResponseDTO(BaseModel):
    report_group_sets: list[ReportGroupSetItemDTO]


class ReportGroupSetCreateRequestDTO(BaseModel):
    name: str


class ReportGroupItemDTO(BaseModel):
    report_group_set_id: int
    id: int
    name: str
    logo: str | None
    order: int
    counts: int


class ReportGroupListResponseDTO(BaseModel):
    report_groups: list[ReportGroupItemDTO]


class ReportGroupCreateRequestDTO(BaseModel):
    name: str
    logo: str | None = None
    order: int
