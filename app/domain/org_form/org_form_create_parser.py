from fastapi import Form
from datetime import datetime
from typing import Optional

from app.dtos.org_dto import OrgUpsertRequestDTO


async def parse_org_create_form(
    org_id: Optional[int] = Form(None),
    name: str = Form(...),
    disabled: Optional[bool] = Form(False),
    contract_start: Optional[str] = Form(None),
    contract_end: Optional[str] = Form(None),
    business_modules: Optional[list[int]] = Form(None),
):
    dto = OrgUpsertRequestDTO(
        org_id=org_id,
        name=name,
        disabled=disabled,
        contract_start=(
            datetime.fromisoformat(contract_start) if contract_start else None
        ),
        contract_end=datetime.fromisoformat(contract_end) if contract_end else None,
        business_modules=business_modules,
    )
    return dto
