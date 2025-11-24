from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.dtos.business_module_dto import BusinessModuleDTO
from app.dtos.date_mixins import DateOnlySerializerMixin
from app.dtos.types import DateLikeDatetime


class OrgDetailDTO(DateOnlySerializerMixin, BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: DateLikeDatetime
    contract_end: DateLikeDatetime
    business_modules: list[BusinessModuleDTO] = []

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("business_modules")
    def serialize_business_modules(self, modules: list[BusinessModuleDTO]):
        """
        把 [BusinessModuleDTO(...), BusinessModuleDTO(...)]
        轉成 [1, 2, 3]
        """
        return [m.id for m in modules]


class OrgListItemDTO(DateOnlySerializerMixin, BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: DateLikeDatetime
    contract_end: DateLikeDatetime


class OrgListResponseDTO(BaseModel):
    org: List[OrgListItemDTO] = Field(default_factory=list)


class OrgUpsertParamDTO(DateOnlySerializerMixin, BaseModel):
    org_id: Optional[int] = None
    logo: str
    name: str
    contract_start: DateLikeDatetime
    contract_end: DateLikeDatetime
    business_modules: list[int]


class OrgUpsertRequestDTO(BaseModel):
    logo: str
    name: str
    contract_start: DateLikeDatetime
    contract_end: DateLikeDatetime
    business_modules: list[int]


class OrgUpsertResponseDTO(DateOnlySerializerMixin, BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    disabled: bool
    contract_start: DateLikeDatetime
    contract_end: DateLikeDatetime
    business_modules: List[int] = Field(default_factory=list)


class LogoUploadResponseDTO(BaseModel):
    url: str
