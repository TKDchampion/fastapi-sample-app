from fastapi import Form
from datetime import datetime
from typing import Optional

from app.dtos.org_dto import OrgCreateRequestDTO


async def parse_org_create_form(
    name: str = Form(...),
    disabled: Optional[bool] = Form(False),
    contract_start: Optional[str] = Form(None),
    contract_end: Optional[str] = Form(None),
    business_modules: Optional[list[int]] = Form(None),
):
    dto = OrgCreateRequestDTO(
        name=name,
        disabled=disabled,
        contract_start=(
            datetime.fromisoformat(contract_start) if contract_start else None
        ),
        contract_end=datetime.fromisoformat(contract_end) if contract_end else None,
        business_modules=business_modules,
    )
    return dto
