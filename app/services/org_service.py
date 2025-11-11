from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories import org_repository
from app.dtos.org_dto import (
    OrgListItemDTO,
    OrgListResponseDTO,
)


def get_organizations_by_si_id(db: Session, si_id: int):
    orgs = org_repository.get_organizations_by_si_id(db, si_id)

    if not orgs:
        raise HTTPException(
            status_code=404,
            detail={"type": "error", "msg": "Error ID"},
        )

    items = [OrgListItemDTO.model_validate(org, from_attributes=True) for org in orgs]

    return OrgListResponseDTO(org=items)
