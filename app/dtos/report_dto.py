from pydantic import BaseModel


class ReportGroupSetItemDTO(BaseModel):
    id: int
    name: str


class ReportGroupSetListResponseDTO(BaseModel):
    report_group_sets: list[ReportGroupSetItemDTO]


class ReportGroupSetCreateRequestDTO(BaseModel):
    name: str


class ReportGroupSetCreateResponseDTO(BaseModel):
    rawData: ReportGroupSetItemDTO


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


class ReportGroupCreateResponseDTO(BaseModel):
    rawData: ReportGroupItemDTO


class ReportGroupUpdateRequestDTO(BaseModel):
    name: str
    logo: str | None = None


class ReportGroupOrderItemDTO(BaseModel):
    report_group_id: int
    order: int


class ReportGroupOrderUpdateRequestDTO(BaseModel):
    orders: list[ReportGroupOrderItemDTO]


class ReportItemDTO(BaseModel):
    id: int
    group_id: int
    name: str
    looker_url: str
    order: int


class ReportListResponseDTO(BaseModel):
    reports: list[ReportItemDTO]


class ReportBatchUpdateItemDTO(BaseModel):
    id: int | None = None
    name: str
    looker_url: str
    order: int


class ReportBatchUpdateRequestDTO(BaseModel):
    reports: list[ReportBatchUpdateItemDTO]


class UserReportGroupItemDTO(BaseModel):
    report_group_set_id: int
    report_group_id: int
    report_group_name: str


class BusinessModuleItemDTO(BaseModel):
    id: int
    name: str


class OrgSidebarResponseDTO(BaseModel):
    report_groups: list[UserReportGroupItemDTO]
    business_modules: list[BusinessModuleItemDTO]
